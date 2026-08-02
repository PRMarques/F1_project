# OpenF1 API — Resumo

Fonte: https://openf1.org/docs/#api-endpoints

## Visão geral

- **URL base:** `https://api.openf1.org/v1/`
- **Formato de resposta:** JSON. Para exportar como CSV, adicione `csv=true` na query string.
- Cada endpoint expõe um recurso (drivers, laps, weather, etc.) acessado via `GET /v1/<endpoint>`.

## Autenticação

- **Dados históricos (a partir de 2023):** gratuitos, sem necessidade de autenticação.
- **Dados em tempo real (live):** exigem assinatura paga.

## Endpoints principais

### Car Data
Telemetria amostrada a ~3.7 Hz: velocidade, acelerador, freio, RPM, marcha e status do DRS.
- Filtros: `driver_number`, `session_key`, `speed`, `brake`, `throttle`, `rpm`
- Uso: analisar desempenho e telemetria do carro durante uma sessão.

### Drivers
Informações dos pilotos: nome, equipe, foto e cor da equipe.
- Filtros: `driver_number`, `session_key`
- Uso: obter dados de perfil do piloto e associação com equipe.

### Drivers Championship (Beta)
Classificação do campeonato de pilotos por sessão, com pontos e posições antes/depois da corrida.
- Filtros: `session_key`, `driver_number`
- Uso: acompanhar a evolução do campeonato ao longo da temporada.

### Teams Championship (Beta)
Classificação do campeonato de construtores, com pontos e posições.
- Filtros: `session_key`, `team_name`
- Uso: acompanhar a evolução do campeonato de construtores.

### Intervals
Diferenças de tempo (gaps) entre pilotos e o líder, atualizadas a cada ~4 segundos durante a corrida.
- Filtros: `session_key`, `interval`, `gap_to_leader`
- Uso: monitorar a dinâmica da corrida e ganho/perda de posições.

### Laps
Dados detalhados de voltas: tempos de setor, velocidades em pontos intermediários e mini-setores.
- Filtros: `session_key`, `driver_number`, `lap_number`, `lap_duration`
- Uso: analisar desempenho de voltas específicas e identificar setores rápidos/lentos.

### Location
Coordenadas 3D aproximadas da posição do carro na pista (~3.7 Hz). Útil para progresso no traçado, mas sem detalhe lateral preciso.
- Filtros: `session_key`, `driver_number`, `date`
- Uso: visualizar a posição dos carros no circuito durante a sessão.

### Meetings
Informações de um fim de semana de GP ou teste: datas, circuito, país. Atualizado diariamente à meia-noite UTC.
- Filtros: `year`, `country_name`, `is_cancelled`
- Uso: localizar um fim de semana de corrida específico e seus detalhes.

### Overtakes
Mudanças de posição entre pilotos (ultrapassagens em pista, ganhos em pit stop, penalidades). Apenas para corridas; pode estar incompleto.
- Filtros: `session_key`, `overtaking_driver_number`, `overtaken_driver_number`, `position`
- Uso: identificar e analisar ultrapassagens durante a corrida.

### Pit
Dados de pit stop: duração no pit lane, tempo parado e volta em que ocorreu.
- Filtros: `session_key`, `driver_number`, `stop_duration`, `lane_duration`
- Uso: comparar eficiência de pit stops e decisões de estratégia.

### Position
Posições dos pilotos ao longo da sessão, incluindo posição inicial e mudanças subsequentes.
- Filtros: `session_key`, `driver_number`, `position`, `date`
- Uso: acompanhar mudanças de posição e progresso do piloto.

### Race Control
Status da sessão, incidentes, bandeiras, safety car e penalidades.
- Filtros: `session_key`, `flag`, `driver_number`, `category`, `date`
- Uso: entender incidentes e decisões regulatórias da corrida.

### Sessions
Informações de sessões (treino, classificação, sprint, corrida): datas e circuito. Atualizado diariamente à meia-noite UTC.
- Filtros: `year`, `country_name`, `session_name`, `session_type`
- Uso: localizar e filtrar tipos específicos de sessão e datas.

### Session Result
Classificação final após a sessão (treino, classificação, corrida): posições, tempos e gaps.
- Filtros: `session_key`, `position`, `driver_number`
- Uso: acessar resultados oficiais e comparar desempenho.

### Starting Grid
Resultado da classificação que define a ordem de largada da corrida.
- Filtros: `session_key`, `position`, `driver_number`
- Uso: revisar desempenho na classificação e ordem do grid.

### Stints
Informações de stints: composto de pneu, intervalo de voltas e idade do pneu.
- Filtros: `session_key`, `driver_number`, `compound`, `tyre_age_at_start`
- Uso: analisar estratégias de pneus e gestão de stints.

### Team Radio
Comunicações de rádio entre pilotos e equipe (seleção limitada, não é completa). A cobertura caiu significativamente a partir de 2026, com a maioria dos eventos sem dados de rádio.
- Filtros: `session_key`, `driver_number`
- Uso: acessar gravações de comunicações de equipe.

### Weather
Condições da pista e do ambiente, atualizadas a cada minuto: temperatura, umidade, vento e chuva.
- Filtros: `meeting_key`, `session_key`, `track_temperature`, `wind_direction`, `air_temperature`
- Uso: correlacionar condições climáticas com variações de desempenho.

## Filtros e query params

- Qualquer atributo de um endpoint pode ser usado como filtro (exceto campos do tipo array).
- Operadores de comparação suportados: `=`, `<`, `<=`, `>`, `>=`
- Suporta múltiplos formatos de data (ISO 8601, texto, etc.) para filtros de intervalo de tempo.

**Exemplo:**
```
GET https://api.openf1.org/v1/laps?driver_number=55&session_key=9222&is_pit_out_lap=true&lap_duration>=120
```

## Recursos especiais

- **Exportação CSV:** adicione `csv=true` a qualquer query para receber uma resposta compatível com planilhas.
- **Palavra-chave `latest`:** pode ser usada em `meeting_key` ou `session_key` para referenciar automaticamente o meeting/sessão mais recente.

## Notas gerais

- Limites de taxa (rate limits) não são documentados explicitamente pela OpenF1.
- `Overtakes` é exclusivo para corridas e pode estar incompleto.
- `Team Radio` teve cobertura reduzida a partir de 2026.
- `Meetings` e `Sessions` são atualizados diariamente à meia-noite UTC.
