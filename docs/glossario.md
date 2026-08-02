# Glossário de siglas

Todas as siglas usadas no código, nos testes e na documentação deste projeto.
Para siglas de origem inglesa, a tabela traz o significado em inglês (o original)
e a tradução em português; o campo "Uso no projeto" explica onde e por que a sigla
aparece — a maioria não tem tradução consagrada e é usada em português na forma
inglesa mesmo (ex.: ninguém fala "IPA" em vez de "API").

## Tecnologia geral

| Sigla | Inglês | Português | Uso no projeto |
|---|---|---|---|
| **API** | Application Programming Interface | Interface de Programação de Aplicações | A OpenF1 API é a fonte de todos os dados ingeridos (veja [Arquitetura](arquitetura.md)). |
| **CI** | Continuous Integration | Integração Contínua | Pipeline do GitHub Actions (`.github/workflows/ci.yml`) que roda lint, testes e build da doc a cada push/PR. |
| **CLI** | Command-Line Interface | Interface de Linha de Comando | O pipeline de ingestão é executado via linha de comando (`python -m f1_project.pipeline --years ...`). |
| **CSV** | Comma-Separated Values | Valores Separados por Vírgula | Formato de exportação opcional da OpenF1 (`csv=true` na query string) — não é o formato usado internamente pelo projeto, que grava Parquet na Silver/Gold. |
| **HTTP** | HyperText Transfer Protocol | Protocolo de Transferência de Hipertexto | Protocolo usado pelo cliente de ingestão (`ingestion/client.py`) para consultar a OpenF1. |
| **JSON** | JavaScript Object Notation | Notação de Objetos JavaScript | Formato de resposta da OpenF1 e formato em que a camada Bronze é persistida (`data/raw/`). |
| **PR** | Pull Request | Solicitação de Integração | Como uma contribuição é proposta e revisada antes de entrar em `main` (veja [Contribuindo](contributing.md)). |
| **REST** | Representational State Transfer | Transferência de Estado Representacional | Estilo de arquitetura da OpenF1 API — endpoints acessados via `GET /v1/<endpoint>`. |
| **URL** | Uniform Resource Locator | Localizador Uniforme de Recursos | Endereço base da API, configurável via `OPENF1_BASE_URL` (`config.py`, `.env.example`). |
| **UTC** | Coordinated Universal Time | Tempo Universal Coordenado | Fuso horário de referência: `meetings` e `sessions` da OpenF1 são atualizados diariamente à meia-noite UTC. |
| **GMT** | Greenwich Mean Time | Hora de Greenwich | Campo `gmt_offset` em `MeetingSchema`/`SessionSchema` — deslocamento do fuso local do circuito em relação ao GMT. |

## Domínio de Fórmula 1

| Sigla | Inglês | Português | Uso no projeto |
|---|---|---|---|
| **GP** | Grand Prix | Grande Prêmio | Um fim de semana de corrida (entidade `meetings`); aparece nos filtros e na navegação do dashboard. |
| **DNF** | Did Not Finish | Não Completou (a prova) | Campo booleano `dnf` em `SessionResultSchema` — piloto abandonou a corrida antes do fim. |
| **DNS** | Did Not Start | Não Largou | Campo booleano `dns` em `SessionResultSchema` — piloto não chegou a largar. |
| **DSQ** | Disqualified | Desclassificado | Campo booleano `dsq` em `SessionResultSchema` — piloto foi desclassificado do resultado. |

## Nota sobre nomes de campo

Campos como `meeting_key`, `session_key` e `name_acronym` (código de 3 letras do
piloto, ex.: `VER`, `HAM`) não são siglas — são identificadores da OpenF1 API e
estão documentados por entidade em [Arquitetura](arquitetura.md#entidades-e-chave-natural).
