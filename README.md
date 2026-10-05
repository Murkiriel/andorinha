# Andorinha — tiles de roteamento do Valhalla para o Brasil

**Rotas offline no Brasil com o [Valhalla](https://github.com/valhalla/valhalla)**, o motor de roteamento open
source: os tiles do grafo de vias do país inteiro, gerados a partir do OpenStreetMap e divididos em um **pacote
base** (as rodovias do país) e **um pacote por estado**. Baixe só o que precisa, extraia numa pasta e aponte o
Valhalla para ela: carro, moto, bicicleta e a pé, com instruções em português, sem internet.

O Valhalla não publica tiles prontos, e gerar os do Brasil pede até ~20 GB de RAM. O Andorinha gera e publica o
resultado.

> **Aviso.** Os dados vêm do OpenStreetMap e podem estar incompletos ou errados. A sinalização da via sempre
> prevalece.

**Índice:** [`catalogo.json`](catalogo.json) · **Pacotes:** [releases](https://github.com/Murkiriel/andorinha/releases)
(a mais recente tem a data da geração)

## Baixar por estado

<!-- downloads:start -->
Geração **2026-10-02-161031d6**: OpenStreetMap de 2026-10-01, Valhalla 3.6.3. Baixe sempre a base e os estados por onde vai rodar; confira o sha256 pelo [`catalogo.json`](catalogo.json).

| Pacote | Arquivo | Tamanho |
|---|---|---:|
| **Base** (rodovias do Brasil, sempre necessária) | [andorinha-base.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-base.tar.gz) | 62,4 MB |
| Acre (AC) | [andorinha-AC.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-AC.tar.gz) | 4,6 MB |
| Alagoas (AL) | [andorinha-AL.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-AL.tar.gz) | 22,7 MB |
| Amapá (AP) | [andorinha-AP.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-AP.tar.gz) | 2,3 MB |
| Amazonas (AM) | [andorinha-AM.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-AM.tar.gz) | 12,3 MB |
| Bahia (BA) | [andorinha-BA.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-BA.tar.gz) | 113,9 MB |
| Ceará (CE) | [andorinha-CE.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-CE.tar.gz) | 62,9 MB |
| Distrito Federal (DF) | [andorinha-DF.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-DF.tar.gz) | 18,7 MB |
| Espírito Santo (ES) | [andorinha-ES.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-ES.tar.gz) | 34,9 MB |
| Goiás (GO) | [andorinha-GO.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-GO.tar.gz) | 68,8 MB |
| Maranhão (MA) | [andorinha-MA.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-MA.tar.gz) | 40,3 MB |
| Mato Grosso (MT) | [andorinha-MT.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-MT.tar.gz) | 35,6 MB |
| Mato Grosso do Sul (MS) | [andorinha-MS.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-MS.tar.gz) | 27,8 MB |
| Minas Gerais (MG) | [andorinha-MG.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-MG.tar.gz) | 204,4 MB |
| Pará (PA) | [andorinha-PA.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-PA.tar.gz) | 36,9 MB |
| Paraíba (PB) | [andorinha-PB.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-PB.tar.gz) | 44,6 MB |
| Paraná (PR) | [andorinha-PR.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-PR.tar.gz) | 102,1 MB |
| Pernambuco (PE) | [andorinha-PE.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-PE.tar.gz) | 71,2 MB |
| Piauí (PI) | [andorinha-PI.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-PI.tar.gz) | 35,8 MB |
| Rio Grande do Norte (RN) | [andorinha-RN.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-RN.tar.gz) | 28,9 MB |
| Rio Grande do Sul (RS) | [andorinha-RS.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-RS.tar.gz) | 90,0 MB |
| Rio de Janeiro (RJ) | [andorinha-RJ.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-RJ.tar.gz) | 59,3 MB |
| Rondônia (RO) | [andorinha-RO.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-RO.tar.gz) | 11,0 MB |
| Roraima (RR) | [andorinha-RR.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-RR.tar.gz) | 4,3 MB |
| Santa Catarina (SC) | [andorinha-SC.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-SC.tar.gz) | 76,5 MB |
| São Paulo (SP) | [andorinha-SP.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-SP.tar.gz) | 216,3 MB |
| Sergipe (SE) | [andorinha-SE.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-SE.tar.gz) | 17,8 MB |
| Tocantins (TO) | [andorinha-TO.tar.gz](https://github.com/Murkiriel/andorinha/releases/download/2026-10-02-161031d6/andorinha-TO.tar.gz) | 20,8 MB |
<!-- downloads:end -->

## Compatibilidade

| Andorinha | Valhalla | Bibliotecas que leem |
|---|---|---|
| gerações atuais | **3.6.3** | `valhalla_service` 3.6.3, `pyvalhalla` 3.6.3, [`valhalla-mobile`](https://github.com/Rallista/valhalla-mobile) 0.6.x (Android e iOS) |

Os tiles precisam ser lidos pela versão do Valhalla que os gerou: o formato muda entre versões. A versão de cada
geração está no campo `valhalla_version` do `catalogo.json`: confira antes de baixar e recuse uma geração de
versão diferente da do seu motor.

A versão é a 3.6.3 porque é a que o `valhalla-mobile` publicado embute. O Valhalla já tem a série 3.9, e os
pacotes sobem para ela quando o `valhalla-mobile` publicar uma versão com esse motor (o que falta está em
[`gerador/PENDENCIAS.md`](gerador/PENDENCIAS.md)). Nessa troca o formato do tile muda: os pacotes novos não servem
para um motor 3.6.3, nem os atuais para um motor 3.9.

## Como usar

1. Leia o `catalogo.json` e escolha os pacotes: **sempre o `base`**, mais os estados por onde você vai rodar.
2. Baixe cada arquivo de `release_url` + `file` e confira o `sha256`.
3. Extraia **todos na mesma pasta**. Tiles de divisa vêm nos dois estados vizinhos: são o mesmo arquivo e podem
   ser sobrescritos.
4. Aponte o Valhalla para a pasta (`mjolnir.tile_dir`) e roteie.

```
curl -LO https://github.com/Murkiriel/andorinha/releases/download/<build_id>/andorinha-base.tar.gz
curl -LO https://github.com/Murkiriel/andorinha/releases/download/<build_id>/andorinha-GO.tar.gz
mkdir tiles && tar -xzf andorinha-base.tar.gz -C tiles && tar -xzf andorinha-GO.tar.gz -C tiles
```

```python
import json, valhalla   # pip install pyvalhalla==3.6.3
cfg = valhalla.get_config(tile_extract="", tile_dir="tiles")
cfg["service_limits"]["motorcycle"]["max_distance"] = 5_000_000.0   # o padrão recusa rota acima de 500 km
cfg["loki"]["use_connectivity"] = False   # obrigatório com pacotes parciais (ver "Viagens longas")
actor = valhalla.Actor(cfg)
rota = actor.route(json.dumps({"locations": [{"lat": -16.6869, "lon": -49.2648}, {"lat": -16.3281, "lon": -48.9534}],
                               "costing": "motorcycle", "directions_options": {"language": "pt-BR"}}))
```

No Android e no iOS, com o [`valhalla-mobile`](https://github.com/Rallista/valhalla-mobile) 0.6.x (testado
com o 0.6.3 no Android: Porto Alegre → Fortaleza só com base + RS + CE em 0,3 s):

```kotlin
val padrao = ValhallaConfigFactory.usingTilesDir(pastaDosTiles.absolutePath)
val config = padrao.copy(
    loki = padrao.loki?.copy(useConnectivity = false),
    serviceLimits = padrao.serviceLimits?.let { it.copy(motorcycle = it.motorcycle?.copy(maxDistance = 5_000_000)) },
)
val rota = Valhalla(context, config).use { it.routeRaw(requisicaoJson) }
```

**Não misture gerações.** Os tiles de um estado apontam para os dos vizinhos. Todos os pacotes de uma pasta
precisam ter o mesmo `build_id`; ao atualizar, baixe de novo todos os que estiverem instalados.

**Viagens longas.** Longe da origem e do destino, o Valhalla só usa as rodovias do pacote base. Uma viagem entre
estados funciona com a base e os pacotes da origem e do destino, **desde que a config tenha
`loki.use_connectivity: false`**. Essa checagem prévia olha só as vias locais: sem os estados do meio, ela declara
as pontas "em regiões desconectadas" e nem tenta a rota. Desligada, Porto Alegre → Fortaleza só com base + RS + CE
dá a mesma rota do Brasil inteiro (4.242 km).

## O que tem em cada pacote

| Pacote | Conteúdo |
|---|---|
| `andorinha-base.tar.gz` | Nível 0 do Valhalla: motorway, trunk e primary do Brasil inteiro (quadrados de 4°) |
| `andorinha-<UF>.tar.gz` | Níveis 1 (secondary e tertiary, quadrados de 1°) e 2 (demais vias, quadrados de 0,25°) que tocam a UF, pela malha oficial do IBGE com ~5 km de margem |

Tamanho, sha256, número de tiles e retângulo de cada pacote estão no `catalogo.json`.

## `catalogo.json`

```
schema             versão deste formato (1)
build_id           a geração: data + 8 primeiros do md5 do extrato (ex.: 2026-09-30-cb859dc3), também o nome da release
built_at           quando foi gerada (UTC)
valhalla_version   versão do Valhalla que gerou (e que precisa ler) os tiles
generator_commit   commit do gerador que produziu a geração
required_config    ajustes obrigatórios na config do Valhalla de quem usa os pacotes: {"chave.pontuada": valor}
osm                data (timestamp), md5 e endereço (url) do extrato do OpenStreetMap usado
release_url        onde baixar os arquivos desta geração
attribution        crédito obrigatório dos dados
timezones          fusos horários dentro dos tiles: release do timezone-boundary-builder e as zonas (as 16 do Brasil)
base               o pacote base (campos abaixo)
states             {UF: pacote}, um por estado (campos abaixo)
  name             nome do estado (só em states)
  file             nome do arquivo na release
  bytes            tamanho do arquivo compactado
  sha256           para conferir o download
  tiles            quantos tiles o pacote tem
  bytes_tiles      tamanho dos tiles descompactados
  bbox             área que o pacote atende: o polígono da UF no IBGE (na base, o Brasil),
                   [lat mín, lon mín, lat máx, lon máx], arredondado para fora; use para escolher o que baixar
  bbox_tiles       área coberta pelos tiles do pacote: em geral maior que o bbox (os tiles de 1° e 4° passam da
                   divisa), mas menor onde a UF não tem via (ilhas oceânicas, extremo norte da Amazônia)
  zstd             o mesmo pacote em .tar.zst, quando a geração tem: {"file", "bytes", "sha256"}, como acima
```

Desde as gerações seguintes a 2026-10-05, cada pacote sai também em **`.tar.zst`** (zstd nível 19, janela de 8 MB),
com o mesmo tar do `.tar.gz` dentro: cerca de 15% menor e mais rápido de descompactar, com pouca memória (bom para
celular). Quem lê zstd baixa o `zstd.file`; quem não lê segue no `file` (`.tar.gz`), que continua igual.

Desde as gerações seguintes a 2026-10-05, os tiles levam o **fuso horário** de cada cruzamento (as 16 zonas do
Brasil): uma rota pedida com `date_time` (hora de partida ou de chegada) responde com a hora de cada ponto e o
fuso (`time_zone_name`, `time_zone_offset`). Não há arquivo a mais para baixar.

Hoje, `required_config` é `{"loki.use_connectivity": false, "service_limits.motorcycle.max_distance": 5000000}`
(ver "Viagens longas"). Quem usa os pacotes pode aplicar essas chaves direto na config do Valhalla.

## Atualização

O conjunto é gerado de novo a cada 29 dias, com o extrato do OpenStreetMap mais recente, pelo GitHub Actions
(workflow [`gerar`](.github/workflows/gerar.yml)). Cada geração é uma release nova; o `catalogo.json` da raiz
sempre aponta para a mais recente, e a data do OpenStreetMap usado está no campo `osm.timestamp`.

Ficam no ar as **3 gerações mais recentes**; as anteriores são apagadas a cada publicação, e os links delas deixam
de funcionar. Quem instalou uma geração consegue baixar mais estados dela enquanto ela estiver entre as 3; depois
disso, precisa atualizar todos os pacotes para a geração do catálogo. Use sempre o `release_url` do `catalogo.json`,
não um link fixo de release.

## Como é gerado

O código está em [`gerador/`](gerador) (Python): baixa o extrato, roda o Valhalla, divide por estado, testa rotas
com os pacotes separados e monta o catálogo. Lá estão as medições e as decisões (versão, threads, velocidades).

Cada geração só é publicada se 33 rotas derem, com os pacotes separados, a mesma distância que com o Brasil
inteiro. O foco é a moto: uma rota dentro de cada estado, duas entre estados vizinhos e uma viagem longa só com
os pacotes das pontas. Carro, bicicleta e a pé têm uma rota curta cada.

## Licença

Os **pacotes** são uma base derivada do OpenStreetMap, distribuída sob a **Open Database License (ODbL) 1.0**
(texto em [`LICENSE`](LICENSE)).

- Cite "© colaboradores do OpenStreetMap".
- Se você publicar uma base derivada destes pacotes, ela precisa manter a ODbL.

A divisão por estado usa a malha das UFs do IBGE. O **código** (pasta `gerador/`) é MIT
([`gerador/LICENSE`](gerador/LICENSE)). O Valhalla é MIT.

## English

**Andorinha** publishes ready-to-use **Valhalla routing tiles for Brazil**, rebuilt periodically from OpenStreetMap and
split into a base pack (the country's highways) plus one pack per state. Download the base and the states you
need, extract them into one folder and point Valhalla's `mjolnir.tile_dir` at it. Tiles are built with Valhalla
**3.6.3** and must be read by that version (e.g. `valhalla-mobile` 0.6.x on Android/iOS). All packs in a folder
must share the same `build_id`. Data under the ODbL 1.0 (© OpenStreetMap contributors); generator code under MIT.

<sub>Palavras-chave: Valhalla Brasil, tiles Valhalla, roteamento offline, navegação offline, rotas offline Brasil,
OpenStreetMap Brasil, grafo de rotas, moto, carro, bicicleta, pyvalhalla, valhalla-mobile.</sub>
