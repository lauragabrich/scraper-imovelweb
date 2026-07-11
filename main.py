"""
Scraper ImovelWeb - Imóveis Brasil (por cidade)
Usa lista IBGE de 5.570 municípios para cobertura completa.

Uso:
    python main.py --estado SP --limit 10
    python main.py --all-estados
"""

import argparse
from scraper import ImovelWebScraper
from ibge_cidades import get_cidades_estado
from config import ESTADOS_URL


def main():
    parser = argparse.ArgumentParser(description="Scraper ImovelWeb")
    parser.add_argument("--estado", type=str, help="Estado (ex: SP, RJ)")
    parser.add_argument("--all-estados", action="store_true", help="Todos os estados")
    parser.add_argument("--limit", type=int, help="Limite total de anúncios")
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
        start_progress = db.get_progress(estado)
        if start_progress == -1:
            print(f"[{estado}] Concluído, pulando...", flush=True)
            continue

        # Progresso: cidade_idx (cada cidade = +1)
        cidades = get_cidades_estado(estado)
        if not cidades:
            print(f"[{estado}] Sem cidades IBGE, pulando...", flush=True)
            continue

        start_cidade = start_progress - 1 if start_progress > 1 else 0

        print(f"\n{'='*50}", flush=True)
        print(f"ImovelWeb - {estado} ({len(cidades)} cidades, começando em {start_cidade+1})", flush=True)
        print(f"{'='*50}", flush=True)

        estado_saved = 0

        for cidade_idx in range(start_cidade, len(cidades)):
            cidade = cidades[cidade_idx]
            cidade_nome = cidade["nome"]
            cidade_slug = cidade["slug"]

            saved = scrape_cidade(scraper, estado, cidade_slug, cidade_nome, cidade_idx, len(cidades))
            estado_saved += saved
            total_saved += saved

            # Salva progresso a cada cidade
            db.save_progress(estado, cidade_idx + 2)

            if args.limit and total_saved >= args.limit:
                print(f"\nLimite de {args.limit} atingido.", flush=True)
                return

        # Estado concluído
        db.save_progress(estado, -1)
        print(f"\n[{estado}] Concluído: {estado_saved} anúncios", flush=True)

    print(f"\n{'='*50}", flush=True)
    print(f"TOTAL: {total_saved} anúncios salvos no Turso", flush=True)
    print(f"{'='*50}", flush=True)


def scrape_cidade(scraper, estado, cidade_slug, cidade_nome, idx, total) -> int:
    """Scrape todas as páginas de uma cidade."""
    saved = 0
    empty_pages = 0

    for page in range(1, 100):  # Max 100 páginas por cidade
        links = scraper.get_listing_links(estado, page, cidade_slug)

        if not links:
            empty_pages += 1
            if empty_pages >= 2:
                break
            continue

        empty_pages = 0

        for link in links:
            data = scraper.scrape_listing(link)
            if data and scraper.db.save_anuncio(data):
                saved += 1

    if saved > 0:
        print(f"  [{estado}] {idx+1}/{total} {cidade_nome}: +{saved}", flush=True)

    return saved


if __name__ == "__main__":
    main()
