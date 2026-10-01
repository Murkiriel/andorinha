# Pendências do Andorinha

Situação em 2026-09-30, depois da revisão do gerador (download retomável, malha do IBGE conferida, `build_id`
único, validação das 27 UFs, release em rascunho com retomada). O que não foi feito ainda e por quê.

## Manutenção

| Item | Situação | O que destrava |
|---|---|---|
| **Primeira geração agendada** | O workflow `gerar` gera e publica sozinho a cada 29 dias (ver o README desta pasta), mas uma geração agendada ainda não rodou: as execuções completas até aqui foram disparadas à mão. A primeira está marcada para 2026-10-02 (`GENERATE_FROM` no job `interval`), justamente para ver o caminho agendado rodar inteiro; depois dela, a seguinte é 29 dias mais tarde. O que já rodou de verdade em testes: uma publicação à mão que apagou a release mais antiga (com a tag, depois do push do catálogo), e um run com evento `schedule` em que o job `interval` respondeu "ainda não" e o `generate` foi pulado. | Conferir essa execução: release nova, `catalogo.json` e tabela do README gravados pelo robô, e o segundo disparo do dia parando no "ainda não". |
| **O agendamento do GitHub atrasa muito** | Em 2026-10-01, um disparo marcado para as 06:00 UTC não apareceu no horário, e três disparos de teste marcados para 10:43, 10:55 e 11:07 UTC também não; um único run agendado apareceu às 12:19 UTC. Há relatos do mesmo comportamento em repositórios recém-criados, sem causa confirmada pelo GitHub. Por isso o agendamento saiu da hora cheia e passou a dois disparos por dia (06:17 e 12:17 UTC). O workflow tolera atraso (a regra é "29 dias ou mais", e uma geração que falha é tentada no disparo seguinte), mas não um agendamento que nunca dispara. | Acompanhar os disparos por alguns dias (`gh run list --workflow gerar --event schedule`). Se continuarem faltando, a saída é um disparo de fora do GitHub (`workflow_dispatch` pela API). |
| **Trocar de versão do Valhalla (3.6.3 → 3.9.x)** | Fixada em 3.6.3, a do `valhalla-mobile` 0.6.3 (a mais recente dele em 2026-09-30). O Valhalla já está na 3.9.0 (2026-09-19), com, por exemplo, `surface=laterite` e `surface=clay` tratados como terra (3.8.3), `use_distance` no perfil de moto (3.9.0), `junction=intersection` (3.7.0) e correções de rota. A subida para a 3.9.0 está no [PR #114 do valhalla-mobile](https://github.com/Rallista/valhalla-mobile/pull/114), em revisão; ele espera uma versão do Valhalla com a correção que faz a 3.9.0 compilar para Android de 32 bits (valhalla#6360, que entrou depois da 3.9.0). O `pyvalhalla` 3.9.0 já existe (Windows e Linux). | O `valhalla-mobile` publicar a versão com o Valhalla 3.9.x. Então, tudo junto: `VALHALLA_VERSION` e `requirements.txt`; adaptar `engine.py` ao `pyvalhalla` novo (a 3.8.0 reorganizou o pacote e quebra alguns imports, e mudou a config de log); geração nova (o formato do tile mudou na 3.8.0, então tiles 3.6 e motor 3.9 não se misturam); o catálogo e a seção "Compatibilidade" do README da raiz passam a dizer a versão nova. Quem usa os pacotes precisa conferir `valhalla_version` e recusar uma geração de outra versão: depois da troca, um motor 3.6.3 não lê os pacotes novos. A última geração 3.6.3 só continua nas releases até saírem mais 2 gerações (a limpeza mantém 3); decidir na troca se ela precisa ficar por mais tempo. |

## Qualidade das rotas

| Item | Por que ainda não | O que destrava |
|---|---|---|
| **Tempo estimado otimista nas estradas** | Sem trânsito nem paradas, o Valhalla estima como pista livre: de moto, São Paulo → Rio sai em 4 h 35 (95 km/h de média) e Goiânia → Brasília em 2 h 31 (85 km/h). Na cidade, o DF deu 68 km/h de média na Rodoviária → Aeroporto. | Comparar com tempos reais de viagem em rotas conhecidas e, se preciso, ajustar do lado de quem usa os pacotes (fator por tipo de via) ou por velocidades por trecho (`valhalla_add_predicted_traffic`), o que exige uma fonte aberta de velocidades. |
| **Rotas com hora marcada (`date_time`)** | O pacote não leva o banco de fusos horários; sem ele, o Valhalla não resolve rotas com hora de partida ou chegada. Rota sem hora funciona. | Incluir o `timezones.sqlite` (~120 MB) como pacote à parte, se algum uso precisar. |
| **Elevação** | Os tiles saem sem altitude: o perfil de bicicleta não considera subida, e a ação `height` não responde. | Gerar com os dados de elevação (SRTM, vários GB a mais de download e de pacote); talvez um pacote à parte. |
| **Download menor** | Pacotes em `.tar.gz` (nível 6). zstd reduziria mais, mas o Android não descompacta zstd sem biblioteca extra. | Medir o ganho do zstd e decidir junto com quem consome os pacotes. |

## Publicação

O repositório é github.com/Murkiriel/andorinha. O código é MIT (`LICENSE` desta pasta); os pacotes, ODbL 1.0.
`data/` (extrato, tiles e pacotes) fica fora do git (`.gitignore` da raiz): os pacotes vão para as releases.
Commits usam o e-mail anônimo do GitHub (`…@users.noreply.github.com`).
