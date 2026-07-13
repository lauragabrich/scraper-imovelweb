# Scraper ImovelWeb - Imóveis Brasil

Coleta anúncios do ImovelWeb usando sitemap do site (200k+ URLs de listagem) para cobertura completa.

## Abordagem técnica

### Fase 1: Sitemap → URLs de listagem (cloudscraper)
```
sitemaps_https.xml → 42 sub-sitemaps (gzip)
→ 200k+ URLs tipo /apartamentos-venda-sao-paulo-sp.html
→ Filtra apenas URLs de venda
```

### Fase 2: Listagem → links de propriedades (cloudscraper)
```
Cada URL de listagem tem ~30 links de /propriedades/...
→ Extrai todos os links
```

### Fase 3: Scraping individual (cloudscraper + BeautifulSoup)
```
Acessa cada /propriedades/... e extrai:
preço, área, quartos, bairro, fotos, coordenadas, etc.
```

## Dados coletados

- Preço, condomínio, IPTU, preço/m²
- Área construída/terreno, quartos, suítes, banheiros, vagas
- Localização (endereço, coordenadas)
- Título, descrição, fotos, amenities
- Datas (quando disponíveis via meta tags)
- HTML parcial como backup

## Uso

```bash
pip install -r requirements.txt
python main.py --limit 10
python main.py
python main.py --reset
```

## Cobertura

- ✅ 200k+ URLs de listagem do sitemap oficial
- ✅ Todas as cidades/bairros que o ImovelWeb indexa
- ✅ Apenas venda (filtrado)
- ✅ Progresso salvo no banco (continua entre execuções)

## Limitações

- Cloudflare pode bloquear (usa cloudscraper para bypass)
- Scraping HTML é lento (~3-5s por anúncio)
- Estrutura HTML pode mudar
- Datas nem sempre disponíveis
