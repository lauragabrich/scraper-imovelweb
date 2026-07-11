# Scraper ImovelWeb - Imóveis Brasil

Coleta anúncios do ImovelWeb via scraping HTML com cloudscraper (bypass Cloudflare).

## Como funciona

1. Acessa páginas de listagem por estado (paginação)
2. Extrai links de anúncios individuais (~30 por página)
3. Para cada anúncio, faz scraping do HTML completo
4. Extrai dados via BeautifulSoup (preço, área, quartos, etc.)
5. Salva no Turso com progresso por estado

## Dados coletados

- Preço, condomínio, IPTU, preço/m²
- Área construída/terreno, quartos, suítes, banheiros, vagas
- Localização (endereço, coordenadas)
- Título, descrição, fotos, amenities
- Datas (publicação/atualização quando disponíveis)
- HTML parcial como backup (raw_html)

## Uso

```bash
pip install -r requirements.txt
python main.py --estado SP --limit 10
python main.py --all-estados
```

## Limitações

- Cloudflare pode bloquear após muitas requests
- Scraping HTML é mais lento (~3-5s por anúncio)
- Estrutura do HTML pode mudar sem aviso
- Datas nem sempre disponíveis
