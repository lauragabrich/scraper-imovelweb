import re
import json
import time
import random
import cloudscraper
from bs4 import BeautifulSoup
from config import USER_AGENTS, ESTADOS_URL
from database import Database


class ImovelWebScraper:
    """Scraper ImovelWeb via páginas de listagem + scraping individual."""

    def __init__(self):
        self.db = Database()
        self.scraper = cloudscraper.create_scraper()

    def _wait(self):
        time.sleep(random.uniform(2.0, 4.0))

    def _headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    def _build_url(self, estado: str, page: int, cidade_slug: str = "") -> str:
        estado_slug = ESTADOS_URL.get(estado.upper(), estado.lower())
        if cidade_slug:
            # URL por cidade: /imoveis-venda-campinas-sp.html
            base = f"https://www.imovelweb.com.br/imoveis-venda-{cidade_slug}-{estado.lower()}.html"
        else:
            base = f"https://www.imovelweb.com.br/imoveis-venda-{estado_slug}.html"

        if page == 1:
            return base
        return base.replace(".html", f"-pagina-{page}.html")

    def get_listing_links(self, estado: str, page: int, cidade_slug: str = "") -> list[str]:
        """Extrai links de anúncios de uma página de listagem."""
        url = self._build_url(estado, page, cidade_slug)
        self._wait()
        try:
            r = self.scraper.get(url, headers=self._headers(), timeout=20)
            if r.status_code != 200:
                return []
        except Exception:
            return []

        links = re.findall(r'href="(/propriedades/[^"?]+)', r.text)
        links = list(set(links))
        return [f"https://www.imovelweb.com.br{l}" for l in links]

    def scrape_listing(self, url: str) -> dict | None:
        """Scrape de um anúncio individual."""
        self._wait()
        try:
            r = self.scraper.get(url, headers=self._headers(), timeout=20)
            if r.status_code != 200:
                return None
        except Exception:
            return None

        return self._parse_html(r.text, url)

    def _parse_html(self, html: str, url: str) -> dict | None:
        """Extrai todos os dados possíveis do HTML."""
        soup = BeautifulSoup(html, "html.parser")

        try:
            # Título
            titulo_el = soup.find("h1")
            titulo = titulo_el.text.strip() if titulo_el else None

            # Preço
            preco_el = soup.find(class_=re.compile(r"price|precio"))
            preco = self._clean_price(preco_el.text) if preco_el else None

            # Descrição
            desc_el = soup.find(class_=re.compile(r"description|descricao"))
            descricao = desc_el.get_text(strip=True) if desc_el else None

            # Características
            features = self._extract_features(soup)

            # Localização
            location_el = soup.find(class_=re.compile(r"location|address"))
            location_text = location_el.get_text(strip=True) if location_el else ""

            # Condomínio / IPTU
            condo = self._find_expense(soup, r"condomínio|condominio")
            iptu = self._find_expense(soup, r"iptu")

            # Coordenadas
            lat, lng = self._extract_coords(html)

            # Fotos
            fotos = self._extract_photos(soup)

            # Amenities
            amenities = self._extract_amenities(soup)

            # Datas
            dates = self._extract_dates(soup, html)

            # Tipo
            tipo = self._detect_tipo(titulo or "", url)

            # Preço por m²
            area = features.get("area_construida")
            preco_por_m2 = round(preco / area, 2) if preco and area and area > 0 else None

            return {
                "portal": "imovelweb",
                "url": url,
                "titulo": titulo,
                "descricao": descricao,
                "preco": preco,
                "preco_condominio": condo,
                "iptu": iptu,
                "preco_por_m2": preco_por_m2,
                "area_construida": features.get("area_construida"),
                "area_terreno": features.get("area_terreno"),
                "quartos": features.get("quartos"),
                "suites": features.get("suites"),
                "banheiros": features.get("banheiros"),
                "vagas": features.get("vagas"),
                "tipo": tipo,
                "rua": location_text or None,
                "latitude": lat,
                "longitude": lng,
                "finalidade": "venda",
                "fotos_urls": fotos,
                "image_count": len(fotos.split("|")) if fotos else 0,
                "amenities": amenities,
                "data_publicacao": dates.get("pub"),
                "data_ultima_atualizacao": dates.get("upd"),
                "raw_html": html[:5000],  # Primeiros 5k do HTML como backup
            }
        except Exception:
            return None

    def _extract_features(self, soup) -> dict:
        features = {}
        items = soup.find_all(class_=re.compile(r"feature|icon-feature|detail"))
        for item in items:
            text = item.get_text(strip=True).lower()
            if "quarto" in text or "dormitório" in text or "dorm" in text:
                features["quartos"] = self._extract_int(text)
            elif "suíte" in text or "suite" in text:
                features["suites"] = self._extract_int(text)
            elif "banheiro" in text:
                features["banheiros"] = self._extract_int(text)
            elif "vaga" in text or "garagem" in text:
                features["vagas"] = self._extract_int(text)
            elif "terreno" in text and "m²" in text:
                features["area_terreno"] = self._extract_area(text)
            elif "m²" in text or "area" in text:
                features["area_construida"] = self._extract_area(text)
        return features

    def _extract_amenities(self, soup) -> str | None:
        amenities = []
        items = soup.find_all(class_=re.compile(r"amenity|facility|tag"))
        for item in items:
            text = item.get_text(strip=True)
            if text and len(text) < 50:
                amenities.append(text)
        return "|".join(amenities) if amenities else None

    def _extract_photos(self, soup) -> str | None:
        photos = set()
        for img in soup.find_all("img", src=re.compile(r"https?://.*\.(jpg|jpeg|png|webp)", re.I)):
            src = img.get("src") or img.get("data-src")
            if src and "logo" not in src.lower():
                photos.add(src)
        for img in soup.find_all(attrs={"data-src": re.compile(r"https?://.*\.(jpg|jpeg|png|webp)", re.I)}):
            photos.add(img["data-src"])
        return "|".join(photos) if photos else None

    def _extract_dates(self, soup, html: str) -> dict:
        dates = {"pub": None, "upd": None}
        pub_meta = soup.find("meta", {"property": "article:published_time"})
        if pub_meta and pub_meta.get("content"):
            dates["pub"] = pub_meta["content"]
        mod_meta = soup.find("meta", {"property": "article:modified_time"})
        if mod_meta and mod_meta.get("content"):
            dates["upd"] = mod_meta["content"]
        return dates

    def _extract_coords(self, html: str) -> tuple:
        lat_m = re.search(r'latitude["\s:=]+(-?\d+\.?\d*)', html)
        lng_m = re.search(r'longitude["\s:=]+(-?\d+\.?\d*)', html)
        lat = float(lat_m.group(1)) if lat_m else None
        lng = float(lng_m.group(1)) if lng_m else None
        return lat, lng

    def _find_expense(self, soup, pattern: str) -> float | None:
        el = soup.find(text=re.compile(pattern, re.I))
        if el and el.parent:
            return self._clean_price(el.parent.get_text())
        return None

    def _clean_price(self, text: str) -> float | None:
        if not text: return None
        cleaned = re.sub(r'[R$\s.]', '', text).replace(',', '.')
        match = re.search(r'(\d+\.?\d*)', cleaned)
        try: return float(match.group(1)) if match else None
        except: return None

    def _extract_int(self, text: str) -> int | None:
        m = re.search(r'(\d+)', text)
        return int(m.group(1)) if m else None

    def _extract_area(self, text: str) -> float | None:
        m = re.search(r'([\d.,]+)\s*m', text)
        if m:
            val = m.group(1).replace('.', '').replace(',', '.')
            try: return float(val)
            except: return None
        return None

    def _detect_tipo(self, titulo: str, url: str) -> str | None:
        text = (titulo + " " + url).lower()
        if "apartamento" in text: return "apartamento"
        elif "casa" in text or "sobrado" in text: return "casa"
        elif "terreno" in text or "lote" in text: return "terreno"
        elif "cobertura" in text: return "cobertura"
        elif "kitnet" in text or "studio" in text: return "kitnet"
        elif "comercial" in text or "sala" in text: return "comercial"
        return None
