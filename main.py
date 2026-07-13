"""
Scraper ImovelWeb — Sitemap → listagens → propriedades individuais.
Usa 200k+ URLs do sitemap para cobertura completa.

Uso:
    python main.py --limit 10
    python main.py
"""

import argparse
from scraper import ImovelWebScraper


def main():
    parser = argparse.ArgumentParser(description="Scraper ImovelWeb (sitemap)")
    parser.add_argument("--limit", type=int, help="Limite total de anúncios")
    parser.add_argument("--reset", action="store_true", help="Resetar progresso")

    args = parser.parse_args()

    scraper = ImovelWebScraper()
    db = scraper.db

    if args.reset:
        db.save_progress("imovelweb", 1)
        print("[*] Progresso resetado", flush=True)

    # Lê progresso (índice da URL de listagem atual)
    start_idx = db.get_progress("imovelweb")
    if start_idx == -1:
        print("[ImovelWeb] Já concluído.", flush=True)
        return

    # Fase 1: Baixa URLs do sitemap
    listing_urls = scraper.get_listing_urls(filter_venda=True)
    if not listing_urls:
        print("[ImovelWeb] Nenhuma URL encontrada no sitemap", flush=True)
        return

    # Começa de onde parou
    start = start_idx - 1 if start_idx > 1 else 0
    remaining = listing_urls[start:]

    print(f"[ImovelWeb] {len(remaining)} listagens a processar (de {len(listing_urls)} total)", flush=True)

    total_saved = 0
    seen_props = set()

    for i, listing_url in enumerate(remaining):
        # Fase 2: Extrai links de propriedades
        prop_links = scraper.get_property_links(listing_url)

        # Fase 3: Scraping individual
        for prop_url in prop_links:
            if prop_url in seen_props:
                continue
            seen_props.add(prop_url)

            data = scraper.scrape_listing(prop_url)
            if data and db.save_anuncio(data):
                total_saved += 1

            if args.limit and total_saved >= args.limit:
                db.save_progress("imovelweb", start + i + 2)
                print(f"\nLimite de {args.limit} atingido. Total: {total_saved}", flush=True)
                return

        # Progresso a cada 10 listagens
        if (i + 1) % 10 == 0:
            db.save_progress("imovelweb", start + i + 2)
            print(f"  Listagens: {i+1}/{len(remaining)} | Propriedades: {total_saved}", flush=True)

    db.save_progress("imovelweb", -1)
    print(f"\n[ImovelWeb] Concluído: {total_saved} anúncios salvos", flush=True)


if __name__ == "__main__":
    main()
