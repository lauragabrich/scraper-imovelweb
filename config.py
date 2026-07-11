import os
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ImovelWeb usa slug de estado na URL
ESTADOS_URL = {
    "SP": "sao-paulo-sp", "RJ": "rio-de-janeiro-rj", "MG": "minas-gerais-mg",
    "PR": "parana-pr", "RS": "rio-grande-do-sul-rs", "SC": "santa-catarina-sc",
    "BA": "bahia-ba", "PE": "pernambuco-pe", "CE": "ceara-ce",
    "DF": "distrito-federal-df", "GO": "goias-go", "ES": "espirito-santo-es",
    "PA": "para-pa", "AM": "amazonas-am", "MA": "maranhao-ma",
    "MT": "mato-grosso-mt", "MS": "mato-grosso-do-sul-ms",
    "PB": "paraiba-pb", "RN": "rio-grande-do-norte-rn", "AL": "alagoas-al",
    "PI": "piaui-pi", "SE": "sergipe-se", "TO": "tocantins-to",
    "RO": "rondonia-ro", "AC": "acre-ac", "AP": "amapa-ap", "RR": "roraima-rr",
}
