"""Debug: vê o que o Selenium retorna do ImovelWeb."""
import re
from browser import create_driver, fetch_page

driver = create_driver(headless=False)  # Abre visível para ver

url = "https://www.imovelweb.com.br/apartamentos-venda-sao-paulo-sp.html"
print(f"Acessando: {url}")
html = fetch_page(driver, url)
print(f"HTML: {len(html)} chars")

# Busca links de propriedades
props = re.findall(r'href="(/propriedades/[^"?]+)', html)
print(f"\nLinks /propriedades/: {len(props)}")
for p in props[:5]:
    print(f"  {p}")

# Busca qualquer link com número de ID
ids = re.findall(r'href="([^"]*\d{7,}[^"]*)"', html)
print(f"\nLinks com ID numérico: {len(ids)}")
for i in ids[:5]:
    print(f"  {i}")

# Busca hrefs com imovelweb
all_links = re.findall(r'href="([^"]*imovelweb[^"]*)"', html)
print(f"\nLinks com 'imovelweb': {len(all_links)}")

# Busca qualquer href que parece anúncio
anuncios = re.findall(r'href="(/[^"]*\d{6,}\.html)"', html)
print(f"\nLinks tipo anúncio (/*.html com ID): {len(anuncios)}")
for a in anuncios[:10]:
    print(f"  {a}")

input("\nPressione Enter para fechar...")
driver.quit()
