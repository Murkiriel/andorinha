# Gerador do Andorinha

Código que gera os pacotes de tiles e o `catalogo.json` a partir do extrato do Brasil no OpenStreetMap.

## Requisitos

- Python 3.10+ (testado com 3.12)
- `pip install -r requirements.txt`: `pyvalhalla` (o Valhalla, com os executáveis nativos, inclusive para Windows)
  e `shapely`. Num Python sem venv (a distribuição "embeddable" do Windows), use
  `pip install --target .pylib -r requirements.txt`; o `generate.py` põe `.pylib/` no caminho de import.
- ~25 GB de disco livre (o build confere antes de começar e para na hora se faltar; o pico medido em `data/` foi
  17,5 GB) e memória conforme as threads: pico medido de **20,3 GB com 8 threads** e **13,4 GB com 2** (a leitura
  do extrato sozinha passa de 7 GB). O build usa as threads da máquina, no máximo 8 (`ANDORINHA_THREADS` muda)
- ~2,3 GB de download por geração (o extrato só é baixado de novo quando há versão nova)

## Como rodar

Da pasta `gerador/`:

```
python generate.py                   # geração completa em data/dist/
python generate.py --from packages   # reaproveita os tiles de data/build/
python scripts/publish.py            # confere a geração (não publica nada)
python scripts/publish.py --release  # sobe os pacotes numa release e grava o catalogo.json na raiz
python scripts/due.py                # está na hora de gerar de novo? (só responde; não gera)
python -m unittest discover -s tests -t .
```

Os testes também rodam no GitHub Actions a cada push e pull request (`.github/workflows/testes.yml`), sem o
pyvalhalla e sem os dados baixados: os 2 testes que dependem deles são pulados, com o motivo no log.

A geração inteira roda no Actions, no workflow `gerar` (`.github/workflows/gerar.yml`), **a cada 29 dias**: ele
dispara todo dia às 03:17 e às 09:17 de Brasília, o job `interval` pergunta ao `scripts/due.py` se a geração
publicada (`built_at` do `catalogo.json`) já tem 29 dias, e só então o build roda e publica. Se a geração falhar, o
disparo seguinte tenta de novo. São dois horários, fora da hora cheia, porque o GitHub atrasa ou pula disparos
agendados sem avisar: o segundo cobre o primeiro e, se o primeiro já publicou, só confere a data e para. Disparado à
mão, gera na hora e só publica com `publish` marcado. Num fork, o agendamento não gera.

Para uma geração fora do intervalo sem disparar à mão, a variável `GENERATE_FROM` do job `interval` marca um dia
(`AAAA-MM-DD`, UTC): a partir dele, o agendamento gera se a geração publicada for de antes desse dia. Depois de
publicar, a marca não tem mais efeito, e os 29 dias passam a contar dessa geração.

O job do build libera espaço apagando ferramentas pré-instaladas da máquina, põe os dados e 12 GB de swap no disco
com mais espaço livre, gera, guarda os logs e as medições (memória, swap e disco a cada 30 s) como artefato e
publica pelo `publish.py`. O repositório das releases é o do próprio Actions (`GITHUB_REPOSITORY`), então o mesmo workflow
serve num repositório de teste e no público.

Medido no Actions em 2026-09-30, na máquina de repositório privado (2 CPUs, 7,8 GB de RAM), geração completa com
publicação: **30,5 min** — extrato 1,8 min, tiles 24,0 min com 2 threads, pacotes 4,1 min, validação 0,5 min — e
mais 1,8 min para subir a release. Pico de 3,9 GB de RAM usada (sem contar o cache de arquivos) e 0,6 GB de swap,
em amostras a cada 30 s; 16,0 GB de disco em `data/`. As máquinas são compartilhadas: em outras execuções do mesmo
dia os tiles levaram de 23 a 40 min.

Cada geração grava `data/dist/geracao.json`: minutos de cada etapa, pico de disco usado em `data/` (amostrado a
cada 20 s, para pegar os intermediários do Valhalla) e o resultado. `--from catalog` só remonta o catálogo, sem
validar (avisa no log).

Geração completa medida em 2026-09-30 (`geracao.json`, máquina de 16 threads e 32 GB, sem download novo do
extrato): **20,8 min** — tiles do Brasil 15,5 min, pacotes 3,9 min, validação das 30 rotas 1,4 min. Com o extrato
novo, somar o download de 2,3 GB (25 min numa conexão de ~1,5 MB/s).

## Como funciona

| Etapa | Módulo | O que faz |
|---|---|---|
| osm | `andorinha/sources.py` | Baixa o extrato do Brasil do openstreetmap.fr quando há versão nova e confere o md5 publicado. Se o site troca o extrato durante o download (uma vez por dia), lê o md5 de novo e baixa a versão nova uma vez |
| tiles | `andorinha/builder.py` | Roda `valhalla_build_admins` e `valhalla_build_tiles` do pyvalhalla, com 8 threads (config e executáveis vêm do `engine.py`), com o banco de fusos só do Brasil de `andorinha/timezones.py` (desde 2026-10-05; precisa do SpatiaLite, `mod_spatialite`) |
| packages | `andorinha/packing.py` | Divide os tiles em base (nível 0) e um pacote por UF (níveis 1 e 2), pela malha do IBGE, e grava os `.tar.gz` e, com o mesmo tar, os `.tar.zst` (zstd 19, desde 2026-10-05) |
| validate | `andorinha/validation.py` | 33 rotas, cada uma só com a base e as UFs dela instaladas, comparadas com a rota do Brasil inteiro. O foco é a moto, com 30: uma dentro de cada UF (capital -> cidade de 25 a 140 km), duas entre UFs vizinhas e Porto Alegre -> Fortaleza só com os pacotes das pontas. Carro, bicicleta e a pé têm uma rota curta cada, dentro de uma UF. Leva ~1 min |
| catalog | `andorinha/catalog.py` | Monta o `catalogo.json` com tamanho, sha256, bbox e contagem de tiles de cada pacote |

Módulos de apoio:
- `andorinha/engine.py`: o único que importa o pyvalhalla. Confere a versão em toda importação e guarda as duas configs:
  a do build e a de quem usa os pacotes (`routing_config`, com `use_connectivity` desligado e o limite de distância da
  moto aumentado), que a validação usa.
- `andorinha/publishing.py`: as travas da publicação (`check`, `drops`); `scripts/publish.py` é só a linha de comando.
- `andorinha/schedule.py`: a regra do intervalo entre gerações (29 dias, `GENERATION_INTERVAL_DAYS`), contada do
  `built_at` do `catalogo.json` publicado, em dias arredondados, e a geração extra com dia marcado;
  `scripts/due.py` é só a linha de comando.
- `andorinha/tiles.py`: a grade de tiles (caminho do arquivo, nível, índice e retângulo).
- `andorinha/net.py`: downloads que retomam de onde pararam (`Range`), nunca deixam arquivo pela metade com o nome final e só repetem erro passageiro (4xx, fora 408 e 429, falha na hora).
  Corpo comprimido (gzip) é descomprimido ao gravar: o IBGE manda a malha assim para os executores do Actions,
  mesmo sem o urllib pedir.
- `andorinha/util.py`: hash de arquivo (sha256 dos pacotes, md5 do extrato).
- `andorinha/config.py`: tudo o que muda o resultado de uma geração.

## Decisões e medições

**Versão do Valhalla fixada em 3.6.3.** O formato do tile muda entre versões (o cabeçalho mudou na 3.8), e os
tiles precisam ser lidos pelo mesmo Valhalla que os gerou. 3.6.3 é a versão embutida no `valhalla-mobile` 0.6.x,
a biblioteca Android e iOS. O `builder.py` recusa rodar com outra versão do pyvalhalla instalada. Para trocar:
mude `VALHALLA_VERSION` e `requirements.txt` juntos, gere tudo de novo e publique como geração nova.

**8 threads, não todas.** Numa máquina Windows de 16 threads, o `valhalla_build_tiles` com todas caiu duas vezes
sem escrever nada no log (código `0xC0000409`), com o Brasil e com o DF, no Valhalla 3.6.3 e no 3.8.3. Com 8
terminou todas as vezes. O Valhalla 3.9 passou a limitar uma ordenação interna a 8 threads.

**Sem tabela de velocidades padrão (`default_speeds_config`).** As velocidades vêm do `maxspeed` do OpenStreetMap
e das regras por tipo de via do próprio Valhalla. Num teste no DF, tiles gerados com uma tabela de velocidades
por densidade urbana estimaram 39 km/h para a moto na DF-002 (Eixão, via expressa de 80 km/h), contra 73 km/h sem
a tabela, e quase o dobro do tempo na rota inteira.

**Sem trânsito, fusos horários, transporte público e pontos de referência.** O pacote é só o grafo de rotas. Sem
o banco de fusos, rotas com hora marcada (`date_time`) não saem; rota sem hora funciona normalmente.

**Divisão por UF.** O nível 0 (motorway, trunk e primary) vai inteiro para o pacote base: longe da origem e do
destino, o Valhalla só usa esse nível, então uma viagem longa funciona com a base e os pacotes das duas pontas. Os
níveis 1 e 2 vão para as UFs cujo polígono (malha do IBGE, com margem de 0,05°, ~5 km) toca o tile. Tile na divisa
entra nas duas UFs. Os tiles que não tocam nenhuma UF (sobras do recorte do extrato em países vizinhos) ficam de
fora.

**Pacotes parciais exigem `loki.use_connectivity: false`.** A checagem prévia de conectividade do Valhalla olha só as vias locais: com a base e os pacotes das duas pontas, sem os estados do meio, ela recusava Porto Alegre → Fortaleza ("regiões desconectadas") sem tentar. Desligada, sai a mesma rota do Brasil inteiro (4.242 km). A validação roda assim, e o README da raiz manda quem usa fazer o mesmo.

**Pacotes reproduzíveis.** Ordem fixa e datas zeradas no `.tar` e no gzip: os mesmos tiles geram o mesmo arquivo,
byte a byte, e o mesmo sha256.

**GitHub Releases, não git.** Os pacotes são binários de centenas de MB que mudam por inteiro a cada geração.
No git, o histórico incharia a cada mês. Cada geração vira uma release (`build_id` = data), e o repositório guarda
só o gerador e o `catalogo.json`. Limites do GitHub Releases: cada arquivo abaixo de 2 GiB, sem limite de tamanho
total nem de banda.

**Ficam 3 gerações.** No fim de cada publicação, depois do push do `catalogo.json` novo, o `publish.py` apaga as
releases antigas (e as tags delas): ficam a do catálogo e as 2 anteriores mais recentes (`KEEP_GENERATIONS`;
`ANDORINHA_KEEP_GENERATIONS=0` desliga). Três, e não uma, porque pacotes de gerações diferentes não se misturam:
quem instalou a geração anterior só consegue baixar mais um estado dela enquanto a release existir. Também saem os
rascunhos órfãos (uma subida que caiu deixa um rascunho que a geração seguinte, com outro `build_id`, não retoma).
Release com tag fora do formato do `build_id` nunca é tocada; se a release do catálogo não estiver publicada, nada
é apagado. Uma falha na limpeza vira aviso e não derruba a publicação: a geração seguinte tenta de novo.
`python scripts/publish.py --prune --dry-run` mostra o que seria apagado.

## Travas de publicação

O `scripts/publish.py` não publica se:
- a geração ainda roda ou caiu no meio (marca `GERACAO_EM_ANDAMENTO` em `data/dist/`),
- o catálogo foi gerado com outra versão do Valhalla,
- algum pacote falta, não bate o sha256 ou passa do limite do GitHub Releases,
- algum pacote perdeu mais de 5% dos tiles em relação ao `catalogo.json` publicado (`--accept-drop` para passar),
- a geração usa um OpenStreetMap mais antigo que o da publicada (`--accept-older` para passar),
- já existe uma release PUBLICADA com o mesmo `build_id`,
- com `--commit`, o git do repositório não está com o e-mail anônimo do GitHub (`…@users.noreply.github.com`).

A release sobe como rascunho, sem arquivos; cada pacote que ainda não está lá (ou está com outro tamanho) sobe; só
com todos presentes e do tamanho certo ela é publicada. Se a subida cair no meio, fica um rascunho que ninguém vê, e
rodar o mesmo comando de novo retoma do que falta. Só depois disso o `catalogo.json` e a tabela "Baixar por estado"
do README da raiz (gerada a partir do catálogo, com o link de cada pacote) mudam, no mesmo commit: o catálogo publicado
nunca aponta para arquivos que ainda não existem. Um erro do `gh` mostra o comando e a mensagem dele; sem rede ou sem
login não é confundido com "a release não existe". `--commit` sem `--release` e `--push` sem `--commit` dão erro.

## Convenções

**Idioma**

- Nomes de arquivos e pastas de dados e documentos: português, sem acento, sem espaço (`andorinha-GO.tar.gz`,
  `catalogo.json`, `geracao.json`, `pacotes.json`, `PENDENCIAS.md`, `gerar.yml`). Exceção: os nomes que o
  ecossistema espera (`README.md`, `LICENSE`, `requirements.txt`).
- Código: nomes de variáveis, funções, classes, módulos e arquivos de código em inglês (`packing.py`,
  `publish_release`, `RunRecorder`); siglas como são (`osm`, `ibge`). Opções de linha de comando (`--from`,
  `--accept-drop`), variáveis de ambiente (`ANDORINHA_THREADS`), nomes de etapas (`packages`, `validate`) e
  identificadores do workflow (entrada `publish`, job `generate`) também.
- Formato dos dados: chaves do `catalogo.json` e do `geracao.json` e valores com significado (`ok`, `failed`) em
  inglês.
- Comentários, docstrings, documentação, mensagens de log e de erro, notas das releases, nomes dos passos do workflow
  e mensagens de commit: português.

**Versão do formato (`schema`)**

O `catalogo.json` tem o campo `schema`, a versão do formato. Ela sobe quando muda algo que um leitor feito para a
versão anterior não entenderia: uma chave renomeada ou removida, um nome ou caminho de arquivo que muda, um valor que
muda de significado. Não sobe quando só entram dados novos, ou chaves novas que um leitor antigo pode ignorar. Numa
mudança que exige subir a versão, primeiro o gerador passa a escrever o formato novo junto com o antigo, depois quem
lê passa a usar o novo, e só então o antigo sai e a versão sobe.

## Licença

Código: MIT (`LICENSE` desta pasta). Os pacotes gerados são base derivada do OpenStreetMap, sob a ODbL 1.0 (ver o
README da raiz).
