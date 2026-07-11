"""Lista de cidades do IBGE com slugs para ImovelWeb."""
import requests
import json
import os
import re
import unicodedata
import time

CACHE_FILE = "cidades_ibge.json"

ESTADOS_IBGE = {
    "AC": 12, "AL": 27, "AP": 16, "AM": 13, "BA": 29, "CE": 23,
    "DF": 53, "ES": 32, "GO": 52, "MA": 21, "MT": 51, "MS": 50,
    "MG": 31, "PA": 15, "PB": 25, "PR": 41, "PE": 26, "PI": 22,
    "RJ": 33, "RN": 24, "RS": 43, "RO": 11, "RR": 14, "SC": 42,
    "SP": 35, "SE": 28, "TO": 17,
}

ESTADOS_SIGLA = {v: k for k, v in ESTADOS_IBGE.items()}


def slugify(text: str) -> str:
    """Converte nome de cidade para slug de URL do ImovelWeb."""
    # Remove acentos
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Substitui espaços e caracteres especiais por hifens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove hifens duplicados e nas pontas
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def get_all_cidades() -> dict[str, list[dict]]:
    """Retorna {estado: [{nome, slug}]} do IBGE."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    print("[IBGE] Baixando lista de municípios...", flush=True)
    resultado = {}

    for estado, codigo in ESTADOS_IBGE.items():
        for tentativa in range(3):
            try:
                url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{codigo}/municipios"
                r = requests.get(url, timeout=60)
                if r.status_code == 200:
                    municipios = r.json()
                    cidades = []
                    for m in municipios:
                        nome = m.get("nome", "")
                        if nome:
                            cidades.append({
                                "nome": nome,
                                "slug": slugify(nome),
                            })
                    resultado[estado] = sorted(cidades, key=lambda x: x["nome"])
                    print(f"  {estado}: {len(cidades)} cidades", flush=True)
                    break
            except Exception as e:
                if tentativa == 2:
                    print(f"  {estado}: erro - {e}", flush=True)
                    resultado[estado] = []
                else:
                    time.sleep(5)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in resultado.values())
    print(f"[IBGE] Total: {total} municípios", flush=True)
    return resultado


def get_cidades_estado(estado: str) -> list[dict]:
    """Retorna [{nome, slug}] de um estado."""
    todas = get_all_cidades()
    return todas.get(estado.upper(), [])
