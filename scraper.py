"""
Scraper ImovelWeb — Sitemap (listagens) + cloudscraper (anúncios individuais).

Estratégia:
- Fase 1: sitemaps_https.xml → 42 sub-sitemaps → 200k+ URLs de listagem
  (ex: /apartamentos-venda-sao-paulo-sp.html)
- Fase 2: para cada URL de listagem, extrai links de /propriedades/
- Fase 3: scraping individual de cada propriedade
"""

import gzip
import re
import time
import random
import json
import cloudscraper
from bs4 import BeautifulSoup
from database import Database
from config import USER_AGENTS


class ImovelWebScraper:
    """Scraper ImovelWeb via sitemap + scraping HTML."""

    SITEMAP_INDEX = "https://www.imovelweb.com.br/sitemaps_https.xml"

    def __init__(self):
        self.db = Database()
        self.scraper = cloudscraper.create_scraper()
        self.driver = None

    def _get_driver(self):
        if not self.driver:
            from browser import create_driver
            print("[ImovelWeb] Iniciando Chrome...", flush=True)
            self.driver = create_driver(headless=True)
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _wait(self, min_s=2.0, max_s=4.0):
        time.sleep(random.uniform(min_s, max_s))

    def _headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    def _fetch(self, url: str, retries: int = 2) -> str | None:
        """GET com cloudscraper, fallback Selenium."""
        # Tenta cloudscraper primeiro (mais rápido para sitemaps XML)
        for attempt in range(1, retries + 1):
            try:
                self._wait(0.5, 1.5)
                r = self.scraper.get(url, headers=self._headers(), timeout=30)
                if r.status_code == 403:
                    break  # Vai pro Selenium
                r.raise_for_status()
                if url.endswith(".gz"):
                    return gzip.decompress(r.content).decode("utf-8")
                return r.text
            except Exception:
                if attempt < retries:
                    time.sleep(2 ** attempt)

        # Fallback: Selenium
        from browser import fetch_page
        driver = self._get_driver()
        try:
            html = fetch_page(driver, url)
            return html if html else None
        except Exception:
            return None

    # ─── Fase 1: Sitemap → URLs de listagem ──────────────────────

    def get_listing_urls(self, filter_venda: bool = True) -> list[str]:
        """Baixa sub-sitemaps e extrai URLs de listagem."""
        print("[ImovelWeb] Baixando sitemaps...", flush=True)

        # URLs conhecidas dos sub-sitemaps (descobertas via robots.txt)
        sub_sitemaps = [
            f"https://www.imovelweb.com.br/sitemap_list_https_{i}.xml.gz"
            for i in range(1, 43)
        ]

        all_urls = []
        for i, sub_url in enumerate(sub_sitemaps):
            # Usa requests direto para .xml.gz (não precisa de Selenium)
            try:
                self._wait(0.3, 0.8)
                r = self.scraper.get(sub_url, timeout=30)
                if r.status_code != 200:
                    continue
                content = gzip.decompress(r.content).decode("utf-8")
                locs = re.findall(r'<loc>\s*(.*?)\s*</loc>', content)

                if filter_venda:
                    locs = [l for l in locs if "-venda" in l]

                all_urls.extend(locs)
                if locs:
                    print(f"  [{i+1}] {sub_url.split('/')[-1]}: {len(locs)} URLs", flush=True)
            except Exception:
                continue

        print(f"[ImovelWeb] Total: {len(all_urls)} URLs de listagem (venda)", flush=True)
        return all_urls

    # ─── Fase 2: Listagem → links de propriedades ────────────────

    def get_property_links(self, listing_url: str) -> list[str]:
        """Acessa uma página de listagem com Selenium e extrai links."""
        from browser import fetch_page
        self._wait()
        driver = self._get_driver()
        try:
            html = fetch_page(driver, listing_url)
            if not html:
                return []
        except Exception:
            return []

        links = re.findall(r'href="(/propriedades/[^"?]+)', html)
        links = list(set(links))
        return [f"https://www.imovelweb.com.br{l}" for l in links]

    # ─── Fase 3: Scraping individual ─────────────────────────────

    def scrape_listing(self, url: str) -> dict | None:
        """Scrape de um anúncio individual com Selenium."""
        from browser import fetch_page
        self._wait()
        driver = self._get_driver()
        try:
            html = fetch_page(driver, url)
            if not html:
                return None
        except Exception:
            return None
        return self._parse_html(html, url)

    def _parse_html(self, html: str, url: str) -> dict | None:
        """Extrai dados do HTML de um anúncio."""
        soup = BeautifulSoup(html, "html.parser")

        try:
            titulo_el = soup.find("h1")
            titulo = titulo_el.text.strip() if titulo_el else None

            preco_el = soup.find(class_=re.compile(r"price|precio"))
            preco = self._clean_price(preco_el.text) if preco_el else None

            desc_el = soup.find(class_=re.compile(r"description|descricao"))
            descricao = desc_el.get_text(strip=True) if desc_el else None

            features = self._extract_features(soup)

            location_el = soup.find(class_=re.compile(r"location|address"))
            location_text = location_el.get_text(strip=True) if location_el else ""

            condo = self._find_expense(soup, r"condomínio|condominio")
            iptu = self._find_expense(soup, r"iptu")

            lat, lng = self._extract_coords(html)
            fotos = self._extract_photos(soup)
            amenities = self._extract_amenities(soup)
            dates = self._extract_dates(soup, html)

            tipo = self._detect_tipo(titulo or "", url)
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
                "raw_html": html[:5000],
            }
        except Exception:
            return None

    def _extract_features(self, soup) -> dict:
        features = {}
        items = soup.find_all(class_=re.compile(r"feature|icon-feature|detail"))
        for item in items:
            text = item.get_text(strip=True).lower()
            if "quarto" in text or "dormitório" in text:
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
        for item in soup.find_all(class_=re.compile(r"amenity|facility|tag")):
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
        pub = soup.find("meta", {"property": "article:published_time"})
        if pub and pub.get("content"):
            dates["pub"] = pub["content"]
        mod = soup.find("meta", {"property": "article:modified_time"})
        if mod and mod.get("content"):
            dates["upd"] = mod["content"]
        return dates

    def _extract_coords(self, html: str) -> tuple:
        lat_m = re.search(r'latitude["\s:=]+(-?\d+\.?\d*)', html)
        lng_m = re.search(r'longitude["\s:=]+(-?\d+\.?\d*)', html)
        return (float(lat_m.group(1)) if lat_m else None,
                float(lng_m.group(1)) if lng_m else None)

    def _find_expense(self, soup, pattern: str) -> float | None:
        el = soup.find(text=re.compile(pattern, re.I))
        if el and el.parent:
            return self._clean_price(el.parent.get_text())
        return None

    def _clean_price(self, text: str) -> float | None:
        if not text: return None
        cleaned = re.sub(r'[R$\s.]', '', text).replace(',', '.')
        m = re.search(r'(\d+\.?\d*)', cleaned)
        try: return float(m.group(1)) if m else None
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
