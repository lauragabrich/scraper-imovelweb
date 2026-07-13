# Scraper ImovelWeb - Imóveis Brasil

Coleta anúncios do ImovelWeb usando **386.361 URLs de listagem** extraídas do sitemap oficial + Selenium para bypass do Cloudflare.

## Abordagem técnica

### Fase 1: URLs de listagem (pré-baixadas do sitemap)

O sitemap do ImovelWeb (`sitemaps_https.xml`) contém 42 sub-sitemaps com 386k+ URLs de páginas de listagem:
```
/apartamentos-venda-sao-paulo-sp.html
/casas-venda-campinas-sp.html
/terrenos-venda-belo-horizonte-mg.html
...
```

Essas URLs foram baixadas localmente e commitadas no repositório (`listing_urls.json`) porque o Cloudflare bloqueia o download dos sitemaps no GitHub Actions.

### Fase 2: Listagem → links de propriedades (Selenium)

Para cada URL de listagem, acessa com **undetected-chromedriver** e extrai links de anúncios individuais (`/propriedades/...`).

### Fase 3: Scraping individual (Selenium + BeautifulSoup)

Visita cada propriedade com Selenium e extrai dados via BeautifulSoup:
- Preço, área, quartos, banheiros, vagas
- Localização (endereço, coordenadas)
- Descrição, fotos, amenities
- Condomínio, IPTU

## Dados coletados

| Categoria | Campos |
|-----------|--------|
| Preço | preço, condomínio, IPTU, preço/m² |
| Características | área construída, área terreno, quartos, suítes, banheiros, vagas, tipo |
| Localização | rua, latitude, longitude |
| Qualitativo | título, descrição, fotos, amenities |
| Temporalidade | data publicação, data atualização (quando disponível), data coleta |
| Backup | raw_html (primeiros 5KB) |
| Controle | imovel_disponivel, imovel_atualizado |

## Uso

```bash
pip install -r requirements.txt
python main.py --limit 10
python main.py
python main.py --reset
```

## Cobertura

- ✅ 386.361 URLs de listagem (todas as combinações tipo+cidade do Brasil)
- ✅ Apenas venda (filtrado do sitemap)
- ✅ Progresso salvo no banco (continua entre execuções)
- ✅ Selenium bypassa Cloudflare

## Limitações

- Selenium é lento (~3-5s por página)
- Chrome headless consome memória
- Cloudflare pode eventualmente bloquear
- Estrutura HTML pode mudar sem aviso
- Datas nem sempre disponíveis nas meta tags
