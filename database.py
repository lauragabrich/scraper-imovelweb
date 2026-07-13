import requests
from datetime import datetime
from config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN


class Database:
    def __init__(self):
        url = TURSO_DATABASE_URL.replace("libsql://", "https://")
        self.base_url = url
        self.headers = {
            "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
            "Content-Type": "application/json",
        }
        self._create_tables()

    def _execute(self, sql, args=None):
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql}},
                {"type": "close"}
            ]
        }
        if args:
            payload["requests"][0]["stmt"]["args"] = [self._fmt(a) for a in args]
        r = requests.post(f"{self.base_url}/v2/pipeline", json=payload, headers=self.headers, timeout=30)
        r.raise_for_status()
        return r.json()

    def _fmt(self, value):
        if value is None: return {"type": "null", "value": None}
        elif isinstance(value, int): return {"type": "integer", "value": str(value)}
        elif isinstance(value, float): return {"type": "float", "value": value}
        elif isinstance(value, str): return {"type": "text", "value": value}
        elif isinstance(value, datetime): return {"type": "text", "value": value.isoformat()}
        else: return {"type": "text", "value": str(value)}

    def _create_tables(self):
        self._execute("""
            CREATE TABLE IF NOT EXISTS anuncios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portal TEXT NOT NULL DEFAULT 'imovelweb',
                url TEXT UNIQUE NOT NULL,
                preco REAL, area_construida REAL, area_terreno REAL,
                quartos INTEGER, banheiros INTEGER, vagas INTEGER, suites INTEGER,
                tipo TEXT, rua TEXT, bairro TEXT, cidade TEXT, estado TEXT, cep TEXT,
                latitude REAL, longitude REAL,
                titulo TEXT, descricao TEXT, fotos_urls TEXT, image_count INTEGER,
                preco_condominio REAL, iptu REAL, preco_por_m2 REAL,
                finalidade TEXT, amenities TEXT, complex_amenities TEXT,
                data_publicacao TEXT, data_ultima_atualizacao TEXT, data_coleta TEXT,
                anunciante_nome TEXT, anunciante_telefone TEXT,
                listing_id TEXT, stamps TEXT, contract_type TEXT, zona TEXT,
                usage_types TEXT, property_sub_type TEXT,
                andar INTEGER, total_andares INTEGER, aceita_permuta TEXT,
                status_anuncio TEXT, raw_json TEXT, raw_html TEXT,
                imovel_disponivel TEXT, imovel_atualizado TEXT
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS scraper_progress (
                estado TEXT PRIMARY KEY, last_page INTEGER DEFAULT 1, updated_at TEXT
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_cidade ON anuncios(cidade)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_estado ON anuncios(estado)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_bairro ON anuncios(bairro)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_tipo ON anuncios(tipo)")
        print("[DB] Tabela pronta no Turso (ImovelWeb)", flush=True)

    def save_anuncio(self, data: dict) -> bool:
        try:
            if "data_coleta" not in data:
                data["data_coleta"] = datetime.utcnow().isoformat()
            columns = list(data.keys())
            placeholders = ", ".join(["?" for _ in columns])
            col_names = ", ".join(columns)
            self._execute(
                f"INSERT OR REPLACE INTO anuncios ({col_names}) VALUES ({placeholders})",
                list(data.values()),
            )
            return True
        except Exception as e:
            print(f"Erro ao salvar: {e}", flush=True)
            return False

    def get_progress(self, estado: str) -> int:
        try:
            result = self._execute("SELECT last_page FROM scraper_progress WHERE estado = ?", [estado])
            rows = result.get("results", [{}])[0].get("response", {}).get("result", {}).get("rows", [])
            if rows:
                return int(rows[0][0].get("value", 1))
        except Exception:
            pass
        return 1

    def save_progress(self, estado: str, last_page: int):
        try:
            self._execute(
                "INSERT OR REPLACE INTO scraper_progress (estado, last_page, updated_at) VALUES (?, ?, ?)",
                [estado, last_page, datetime.utcnow().isoformat()]
            )
        except Exception as e:
            print(f"Erro progresso: {e}", flush=True)
