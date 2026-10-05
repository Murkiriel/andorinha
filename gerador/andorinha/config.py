"""Tudo o que muda o resultado de uma geração, num lugar só."""
from __future__ import annotations

import os
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
REPO = GENERATOR_DIR.parent
DATA = GENERATOR_DIR / "data"
RAW = DATA / "raw"        # extrato do OpenStreetMap e malha do IBGE
BUILD = DATA / "build"    # tiles soltos e bancos auxiliares do Valhalla
DIST = DATA / "dist"      # pacotes .tar.gz e o catalogo.json desta geração

# Versão do Valhalla que gera os tiles. TEM de ser a mesma do motor que vai lê-los: o formato do tile muda entre
# versões (o cabeçalho mudou na 3.8). 3.6.3 é a embutida no valhalla-mobile 0.6.x, a biblioteca Android/iOS.
# Trocar aqui = gerar tudo de novo e publicar como geração nova, com a versão nova no catálogo.
VALHALLA_VERSION = "3.6.3"

# Extrato do Brasil. O openstreetmap.fr recorta pelo polígono do país e publica a data e o md5 ao lado.
OSM_PBF_URL = "https://download.openstreetmap.fr/extracts/south-america/brazil-latest.osm.pbf"
OSM_STATE_URL = "https://download.openstreetmap.fr/extracts/south-america/brazil.state.txt"
OSM_MD5_URL = "https://download.openstreetmap.fr/extracts/south-america/brazil.osm.pbf.md5"

# Malha oficial das UFs (API de malhas do IBGE, v3, qualidade máxima): decide em que pacote cada tile entra.
IBGE_MESH_URL = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
                 "?formato=application/vnd.geo%2Bjson&intrarregiao=UF&qualidade=maxima")

USER_AGENT = "andorinha-gerador/1 (+https://github.com/Murkiriel/andorinha)"

# Threads do valhalla_build_tiles: as da máquina, no máximo 8 (ANDORINHA_THREADS muda). Com todas as 16 de uma
# máquina Windows ele caiu duas vezes sem log (0xC0000409), no Brasil e no DF; com 8 terminou nas duas. O Valhalla 3.9
# limitou uma ordenação interna a 8. Menos threads também baixam o pico de memória (ver gerador/README.md).
THREADS = int(os.environ.get("ANDORINHA_THREADS") or min(8, os.cpu_count() or 1))

# Margem, em graus (~5 km), em volta do polígono da UF ao escolher os tiles dela: pega pontes, balsas e vias que
# cruzam a divisa. Tile na margem de duas UFs entra nas duas.
STATE_MARGIN_DEG = 0.05

# Espaço livre exigido na unidade de data/ antes do build. Medido: extrato (2,3 GB) + intermediários do Valhalla
# (~12 GB, apagados no fim) + tiles (3,2 GB) + pacotes (1,5 GB), com folga. Sem isso, o build cai depois de 15 min.
# ANDORINHA_MIN_FREE_DISK_GB muda (ex.: numa máquina do GitHub Actions depois de liberar espaço).
MIN_FREE_DISK_BYTES = int(float(os.environ.get("ANDORINHA_MIN_FREE_DISK_GB") or 25) * 1_000_000_000)

# De quantos em quantos dias o agendamento gera de novo (andorinha/schedule.py, scripts/due.py).
GENERATION_INTERVAL_DAYS = 29

# Quantas gerações ficam nas releases: a do catálogo publicado e as anteriores mais recentes. As demais são apagadas
# no fim de cada publicação (publishing.prune_releases). 0 = não apaga nenhuma. ANDORINHA_KEEP_GENERATIONS muda.
KEEP_GENERATIONS = int(os.environ.get("ANDORINHA_KEEP_GENERATIONS") or 3)

# O GitHub Releases recusa arquivo a partir de 2 GiB; esta é a trava, com folga.
MAX_ASSET_BYTES = 1_900_000_000
# Nível do .tar.zst de cada pacote. O 19 com a janela padrão (8 MB) dá ~15% menos que o .tar.gz; níveis maiores
# e janelas maiores quase não ganham (medido em 2026-10-05) e pedem mais memória para descompactar no celular.
ZSTD_LEVEL = 19
# Fusos horários dos tiles (andorinha/timezones.py): release fixada do timezone-boundary-builder, a fonte do
# valhalla_build_timezones. Trocar de release muda os tiles só onde uma fronteira de fuso mudou.
TIMEZONE_RELEASE = "2026d"
TIMEZONE_URL = ("https://github.com/evansiroky/timezone-boundary-builder/releases/download/{release}/"
                "timezones-with-oceans.geojson.zip")

# O repositório das releases: ANDORINHA_REPO, senão o do GitHub Actions (GITHUB_REPOSITORY, que ele define sozinho),
# senão o público. Assim um repositório de teste publica e aponta os links para ele mesmo.
GITHUB_REPO = os.environ.get("ANDORINHA_REPO") or os.environ.get("GITHUB_REPOSITORY") or "Murkiriel/andorinha"
RELEASE_URL = "https://github.com/" + GITHUB_REPO + "/releases/download/{tag}/"

ATTRIBUTION = "© colaboradores do OpenStreetMap (ODbL 1.0); limites das UFs: IBGE"

# Marca que o gerador cria em DIST ao começar e apaga ao terminar: se ela existe, a geração caiu no meio.
IN_PROGRESS_MARKER = "GERACAO_EM_ANDAMENTO"

STATES = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
          "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
          "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
          "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
          "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
          "TO": "Tocantins"}

# Código IBGE da UF (campo `codarea` da malha) -> sigla.
IBGE_STATE_CODES = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA",
                    "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
                    "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
                    "51": "MT", "52": "GO", "53": "DF"}
