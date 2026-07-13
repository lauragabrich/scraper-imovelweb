# Scraper ImovelWeb - Imóveis Brasil

Coleta anúncios de venda do ImovelWeb usando **386.361 URLs de listagem** do sitemap oficial + **Selenium** (undetected-chromedriver) para bypass do Cloudflare.

## Abordagem técnica

### Por que Selenium?

O ImovelWeb usa **Cloudflare com proteção anti-bot agressiva**:
- Bloqueia requests de IPs de datacenter (GitHub Actions, VPS)
- Detecta modo headless (Chrome sem tela)
- Só permite acesso de IPs residenciais com navegador real

Por isso o scraper usa `undetected-chromedriver` em modo visível (com janela) rodando **localmente** na máquina do desenvolvedor.

### Fase 1: URLs de listagem (sitemap pré-baixado)

O sitemap do ImovelWeb (`sitemaps_https.xml`) contém 42 sub-sitemaps gzipped com 386k+ URLs de páginas de busca:
```
/apartamentos-venda-sao-paulo-sp.html
/casas-venda-campinas-sp.html
/terrenos-venda-belo-horizonte-mg.html
...
```

Essas URLs foram baixadas e salvas em `listing_urls.json` (commitado no repo) porque o Cloudflare bloqueia o download dos sitemaps em ambientes de CI/CD.

### Fase 2: Listagem → links de propriedades (Selenium)

Para cada URL de listagem, o Selenium acessa a página e extrai links de anúncios individuais:
```
/propriedades/apartamento-a-venda-pinheiros-sp-3032945218.html
/propriedades/casa-a-venda-campinas-sp-3000734669.html
```

Cada página de listagem retorna ~30 links de propriedades.

### Fase 3: Scraping individual (Selenium + BeautifulSoup)

Visita cada `/propriedades/...` e extrai dados via BeautifulSoup:
- Preço (classe CSS `price`)
- Características (classe `feature` — quartos, m², vagas)
- Localização (classe `location`)
- Coordenadas (regex no HTML)
- Fotos (tags `<img>`)
- Descrição, amenities, condomínio, IPTU

### Progresso

Salvo no banco Turso a cada 10 listagens processadas. Se o computador desligar ou o script parar (`Ctrl+C`), na próxima execução continua de onde parou.

## Dados coletados

| Categoria | Campos |
|-----------|--------|
| Preço | preço, condomínio, IPTU, preço/m² |
| Características | área construída, área terreno, quartos, suítes, banheiros, vagas, tipo |
| Localização | rua, latitude, longitude |
| Qualitativo | título, descrição, fotos, image_count, amenities |
| Temporalidade | data publicação, data atualização (meta tags), data coleta |
| Backup | raw_html (primeiros 5KB) |
| Controle | imovel_disponivel, imovel_atualizado (preenchidos depois) |

## Uso

```bash
pip install -r requirements.txt

# Roda sem limite (percorre todas as 386k listagens)
python main.py

# Com limite
python main.py --limit 100

# Resetar progresso
python main.py --reset
```

**Requer**: Chrome instalado na máquina. Roda com janela visível (necessário para bypass Cloudflare).

## Execução

- **Local apenas** — não funciona no GitHub Actions (Cloudflare bloqueia IPs de datacenter + headless)
- Deixar computador ligado com Chrome aberto
- `Ctrl+C` para parar — progresso é salvo automaticamente
- Rodar `python main.py` de novo para continuar

## Cobertura

- ✅ 386.361 URLs de listagem do sitemap oficial
- ✅ Todas as combinações tipo + cidade do Brasil
- ✅ Apenas venda (filtrado)
- ✅ Progresso persistido no banco Turso

## Limitações

- Roda apenas localmente (Cloudflare bloqueia datacenter)
- Necessita Chrome visível (headless detectado)
- Lento (~3-5s por anúncio, ~4s por listagem)
- 386k listagens = ~18 dias para 100% (coleta parcial já é útil)
- Estrutura HTML pode mudar sem aviso
