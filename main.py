"""
Scraper ImovelWeb - Imóveis Brasil
Coleta via scraping HTML com cloudscraper.

Uso:
    python main.py --estado SP --limit 10
    python main.py --all-estados
"""

import argparse
from scraper import ImovelWebScraper
from config import ESTADOS_URL


def main():
    parser = argparse.ArgumentParser(description="Scraper ImovelWeb")
    parser.add_argument("--estado", type=str, help="Estado (ex: SP, RJ)")
    parser.add_argument("--all-estados", action="store_true", help="Todos os estados")
    parser.add_argument("--limit", type=int, help="Limite por estado")
    parser.add_argument("--reset", action="store_true", help="Resetar progresso")

    args = parser.parse_args()

    if not args.estado and not args.all_estados:
        parser.print_help()
        return

    scraper = ImovelWebScraper()
    db = scraper.db

    if args.reset:
        for estado in ESTADOS_URL.keys():
            db.save_progress(estado, 1)
        print("[*] Progresso resetado", flush=True)

    if args.all_estados:
        estados = list(ESTADOS_URL.keys())
    else:
        estados = [args.estado.upper()]

    total_saved = 0

    for estado in estados:
        start_page = db.get_progress(estado)
        if start_page == -1:
            print(f"[{estado}] Concluído, pulando...", flush=True)
            continue

        print(f"\n{'='*50}", flush=True)
        print(f"ImovelWeb - {estado} (página {start_page})", flush=True)
        print(f"{'='*50}", flush=True)

        saved = 0
        empty_pages = 0

        for page in range(start_page, start_page + 200):
            links = scraper.get_listing_links(estado, page)

            if not links:
                empty_pages += 1
                if empty_pages >= 3:
                    print(f"[{estado}] 3 páginas vazias, concluído.", flush=True)
                    db.save_progress(estado, -1)
                    break
                continue

            empty_pages = 0

            for link in links:
                data = scraper.scrape_listing(link)
                if data and db.save_anuncio(data):
                    saved += 1

            total_saved += len(links)
            db.save_progress(estado, page + 1)
            print(f"  Página {page}: +{saved} anúncios ({total_saved} total)", flush=True)

            if args.limit and saved >= args.limit:
                print(f"[{estado}] Limite atingido.", flush=True)
                break

        print(f"[{estado}] {saved} anúncios salvos", flush=True)

    print(f"\n{'='*50}", flush=True)
    print(f"TOTAL: {total_saved} anúncios salvos no Turso", flush=True)
    print(f"{'='*50}", flush=True)


if __name__ == "__main__":
    main()
