# 📊 Guia de Observabilidade - Nexus Engine

Neste guia vou te ensinar como usar a stack completa de observabilidade que implementei no Nexus Engine Trading Platform. Se você nunca trabalhou com Grafana, Loki ou Tempo, este tutorial vai te ajudar a começar.

---

## 🎯 Os Três Pilares

Os **três pilares da observabilidade**. Pensa assim:

```
┌──────────────────────────────────────────────────────────┐
│                   OBSERVABILITY                          │
├──────────────┬──────────────┬────────────────────────────┤
│    LOGS      │   TRACES     │      METRICS               │
│              │              │                            │
│  "O que      │  "Por que    │  "Quanto                   │
│   aconteceu?"│   demorou?"  │   aconteceu?"              │
│              │              │                            │
│   Loki       │    Tempo     │    Prometheus              │
└──────────────┴──────────────┴────────────────────────────┘
                       │
                ┌──────▼──────┐
                │   Grafana   │
                │ (Unified UI)│
                └─────────────┘
```

**Por quê isso é importante para trading?**

Decidi implementar observabilidade completa porque:
- **Logs**: Ver exatamente o que aconteceu em cada backtest ou trade
- **Traces**: Descobrir onde o backtest está lento (C++ engine? Database? API externa?)
- **Metrics**: Monitorar quantos backtests rodaram, taxa de acerto, latência do C++ engine

---

## 📝 Logs (Loki)

### O que são Logs?

Logs são **registros de eventos** que acontecem na aplicação de trading. Pensa neles como o "diário" do sistema:
- Backtests executados (quando, qual estratégia, resultado)
- Sinais de trading gerados (BUY/SELL)
- Chamadas para APIs de market data (Finnhub, Alpha Vantage)
- Erros e exceções (o que quebrou)
- Operações de banco de dados (estratégias salvas, backtests persistidos)

### Como Configurei

Structured logging com JSON para facilitar queries no Loki.

**backend/python/src/infrastructure/telemetry/loki_logger.py**:
```python
class LokiLogger:
    """
    Logger estruturado com JSON.
    Com trace_id para correlação com Tempo.
    """

    def __init__(self, name: str = "nexus"):
        self.logger = logging.getLogger(name)

        # Formato JSON com campos customizados
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s %(user_id)s'
        )
```

**devops/observability/loki/loki-config.yml**:
```yaml
# Retenção de 30 dias para análise histórica de backtests
limits_config:
  retention_period: 720h  # 30 dias

# Decidi usar gzip para economizar espaço de armazenamento
chunk_encoding: gzip
```

### Como Acessar (Passo a Passo)

Vou te mostrar como navegar nos logs de trading:

1. **Abra o Grafana**: http://localhost:3000 (usuário: admin, senha: configurada no .env)
2. **Vá em Explore** (ícone de bússola no menu lateral)
3. **Selecione datasource**: `Loki` no dropdown superior
4. **Execute queries** (copie e cole os exemplos abaixo):

#### Queries Úteis que Preparei

**Ver todos os logs do Nexus Engine**:
```logql
{app="nexus-engine"}
```
Resultado: Mostra tudo que está acontecendo em tempo real (backtests, trades, API calls).

**Filtrar apenas erros de backtest** (útil para debug):
```logql
{app="nexus-engine"} |= "ERROR" |= "backtest"
```
Resultado: Lista só os problemas durante execução de backtests.

**Logs de uma estratégia específica** (ex: SMA Crossover):
```logql
{app="nexus-engine"} | json | strategy_type="sma_crossover"
```
Resultado: Mostra apenas eventos da estratégia SMA.

**Logs de sinais de trading gerados**:
```logql
{app="nexus-engine"} |= "signal_generated" | json | signal_type="BUY"
```
Resultado: Lista todos os sinais de compra gerados pelas estratégias.

**Logs de um backtest específico** (correlação via trace):
```logql
{app="nexus-engine"} | json | trace_id="abc123def456"
```
Resultado: Mostra todos os logs de um backtest específico (mágico!).

**Chamadas para APIs de market data**:
```logql
{app="nexus-engine"} |= "api_call" | json | api_name="finnhub"
```
Resultado: Vê todas as chamadas para Finnhub API.

**Logs das últimas 5 minutos com erro no C++ engine**:
```logql
{app="nexus-engine"} | json | level="ERROR" | component="cpp-engine" [5m]
```

### Estrutura do Log

Cada log possui:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "name": "nexus.backtest",
  "message": "Backtest completed: strategy=sma_crossover, symbol=AAPL, return=15.3%",
  "trace_id": "550e8400e29b41d4a716446655440000",
  "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "AAPL",
  "total_return": 0.153,
  "sharpe_ratio": 1.85
}
```

### Labels e Filtros

**Labels** (indexados, busca rápida):
- `app`: Nome da aplicação (`nexus-engine`)
- `level`: Nível do log (DEBUG, INFO, WARN, ERROR, CRITICAL)
- `component`: Componente (backend-python, cpp-engine, frontend)

**Campos JSON** (extraídos em runtime):
- `trace_id`: ID do trace para correlação
- `strategy_type`: Tipo da estratégia (sma_crossover, rsi_mean_reversion, macd)
- `symbol`: Símbolo do ativo
- `signal_type`: Tipo de sinal (BUY, SELL, HOLD)
- `api_name`: Nome da API chamada (finnhub, alpha_vantage)

---

## 🔍 Traces (Tempo)

### O que são Traces?

Traces rastreiam **o caminho completo de um backtest** através do sistema. É como ver um raio-X da sua execução:

**Exemplo real**: Quando você executa um backtest SMA 50/200 em AAPL, o trace mostra:

```
RunBacktestUseCase (2.1s total)
      │
      ├─ StrategyRepository.get_by_id (15ms)
      │     └─ PostgreSQL Query (12ms)
      │
      ├─ MarketDataService.fetch_daily (850ms)
      │     └─ AlphaVantageAdapter.get_daily (840ms)
      │           ├─ HTTP Request (820ms)  ← Gargalo externo!
      │           └─ Cache Write (20ms)
      │
      ├─ CppBridge.run_backtest (1.2s)
      │     └─ BacktestEngine.run (C++) (1.19s)
      │           ├─ SmaStrategy.on_data [252 calls] (980ms)
      │           ├─ ExecutionSimulator.process (150ms)
      │           └─ PerformanceAnalyzer.calculate (60ms)
      │
      └─ BacktestRepository.save (35ms)
            └─ PostgreSQL Insert (30ms)

Total: 2.1s
```

**Por que isso é útil?** Você descobre onde o backtest está lento: se é a API externa, o C++ engine, ou o banco de dados.

### Como Configurei

**backend/python/src/infrastructure/telemetry/tempo_tracer.py**:
```python
class TempoTracer:
    """
    Distributed tracing com OpenTelemetry.
    Usando OTLP exporter para enviar traces ao Tempo.
    """

    def __init__(self):
        # Resource com metadados do serviço
        resource = Resource.create({
            "service.name": "nexus-engine",
            "service.version": "0.7.0",
            "deployment.environment": settings.environment
        })

        # OTLP Exporter para Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.tempo_url,
            insecure=True  # Uso TLS em produção
        )
```

**devops/observability/tempo/tempo-config.yml**:
```yaml
# Recepção de traces via OTLP, Jaeger e Zipkin
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  jaeger:
    protocols:
      thrift_http:
        endpoint: 0.0.0.0:14268
  zipkin:
    endpoint: 0.0.0.0:9411

# Retenção de 30 dias para análise de performance
storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces
    wal:
      path: /tmp/tempo/wal
    block:
      retention: 720h  # 30 dias
```

### Como Acessar (Passo a Passo)

Te ensino a explorar os traces de trading:

1. **Abra o Grafana**: http://localhost:3000
2. **Vá em Explore** (mesmo lugar dos logs)
3. **Selecione datasource**: `Tempo` (troca o dropdown)
4. **Busque traces de várias formas**:

#### 1. Buscar por Service (ver tudo do sistema)

```
Service Name: nexus-engine
Operation: run_backtest
```
Resultado: Lista todas as execuções de backtest.

#### 2. Buscar por TraceID (correlacionar com logs)

Se você pegou um `trace_id` de um log:
```
Trace ID: 550e8400e29b41d4a716446655440000
```
Resultado: Mostra exatamente aquele backtest específico.

#### 3. Buscar por Duração (encontrar backtests lentos)

```
Min Duration: 1s
Max Duration: 10s
```
Resultado: Lista backtests que demoraram entre 1s e 10s (ótimo para performance tuning).

#### 4. Buscar por Tags (filtrar estratégias)

```
Tags:
  strategy.type = sma_crossover
  symbol = AAPL
```
Resultado: Backtests apenas de SMA em AAPL.

### Visualizando um Trace (O Mais Legal!)

Quando você clica em um trace, a mágica acontece:

**Timeline View**:
```
RunBacktestUseCase       ████████████████████████ 2.1s
  MarketDataService      ███████████ 850ms
    AlphaVantageAdapter  ██████████ 840ms
  CppBridge              ███████████████ 1.2s
    BacktestEngine (C++)  ██████████████ 1.19s
      SmaStrategy         ████████ 980ms
      ExecutionSimulator  ███ 150ms
      PerformanceAnalyzer █ 60ms
  BacktestRepository     █ 35ms
```

**Span Details**:
- **Operation**: Nome da operação (ex: `CppBridge.run_backtest`)
- **Duration**: Tempo total (ex: 1.2s)
- **Tags**: Metadata
  - `strategy.type`: sma_crossover
  - `symbol`: AAPL
  - `initial_capital`: 100000
  - `total_trades`: 24
- **Logs**: Eventos dentro do span
  - "Strategy loaded: SMA(50, 200)"
  - "Market data fetched: 252 days"
  - "Backtest completed: return=15.3%"

### Correlação Logs ↔ Traces (Magia da Observabilidade!)

Correlação automática. Veja como funciona:

**Do Log para o Trace**:
1. Você está vendo logs no Loki
2. Vê um log de backtest lento
3. Clica no `trace_id` (aparece como link azul)
4. Grafana abre automaticamente o trace no Tempo
5. Você vê toda a execução do backtest em detalhes!

**Do Trace para os Logs**:
1. Você está vendo um trace no Tempo
2. Clica em "Logs for this span"
3. Grafana mostra todos os logs daquele backtest
4. Você vê exatamente o que o código estava fazendo!

---

## 📈 Metrics (Prometheus)

### O que são Metrics?

Metrics são **números** sobre a plataforma de trading ao longo do tempo. Pensa em gráficos:
- Quantos backtests por minuto? (throughput)
- Quantos trades foram executados? (volume)
- Qual a latência do C++ engine? (performance)
- Quantas chamadas para APIs externas? (usage)
- Taxa de cache hit do market data? (efficiency)

**Por que são úteis?** Você consegue ver tendências, anomalias e otimizar performance.

### Como Configurei

Métricas customizadas específicas para trading algorítmico.

**backend/python/src/infrastructure/telemetry/prometheus_metrics.py**:
```python
class PrometheusMetrics:
    """
    Métricas customizadas para monitorar:
    - Performance do backtest engine
    - Trades executados
    - Chamadas de API externa
    - Latência do C++ engine
    """

    def __init__(self):
        # Backtest metrics
        self.backtests_total = Counter(
            'nexus_backtests_total',
            'Total number of backtests executed',
            ['strategy_type', 'status']
        )

        self.backtest_duration_seconds = Histogram(
            'nexus_backtest_duration_seconds',
            'Backtest execution time in seconds',
            ['strategy_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        # C++ Engine metrics
        self.cpp_engine_latency_ns = Histogram(
            'nexus_cpp_engine_latency_nanoseconds',
            'C++ engine latency in nanoseconds',
            ['operation'],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
        )

        # Trade metrics
        self.trades_total = Counter(
            'nexus_trades_total',
            'Total number of trades executed',
            ['symbol', 'side']
        )
```

**devops/observability/prometheus/prometheus.yml**:
```yaml
scrape_configs:
  # Nexus Backend Python
  - job_name: 'nexus-backend'
    scrape_interval: 10s  # Mais frequente para métricas de trading
    metrics_path: '/metrics'
    static_configs:
      - targets: ['nexus-backend:9090']
        labels:
          service: 'nexus-backend'
          component: 'trading-engine'

# Retenção de 15 dias para análise histórica
storage:
  tsdb:
    retention.time: 15d
    retention.size: 50GB
```

### Como Acessar (Duas Formas)

#### 1. Prometheus UI (Interface Simples)

**URL**: http://localhost:9090

Abra e vá em "Graph". Cole as queries abaixo na caixa de texto:

```promql
# Backtests executados por minuto
rate(nexus_backtests_total[1m])
→ Mostra quantos backtests/minuto o sistema está processando

# Duração média de backtest (últimos 5 minutos)
rate(nexus_backtest_duration_seconds_sum[5m]) /
rate(nexus_backtest_duration_seconds_count[5m])
→ Tempo médio de execução de backtest

# Latência do C++ engine (p95)
histogram_quantile(0.95,
  rate(nexus_cpp_engine_latency_nanoseconds_bucket[5m])
)
→ 95% dos backtests têm latência abaixo deste valor

# Trades por símbolo
sum by (symbol) (nexus_trades_total)
→ Quantos trades foram executados em cada ativo

# Taxa de erro em backtests
rate(nexus_backtests_total{status="failed"}[5m]) /
rate(nexus_backtests_total[5m])
→ Percentual de backtests que falharam
```

#### 2. Grafana Dashboards (Interface Bonita)

**URL**: http://localhost:3000

Três dashboards prontos para você:

1. **Nexus Trading Metrics** (dashboard principal)
   - Backtests executados (total, rate)
   - Trades executados (por símbolo, por sinal)
   - API calls para market data
   - Estratégias ativas

2. **C++ Engine Performance**
   - Latência do engine (p50, p95, p99)
   - Throughput de sinais (signals/s)
   - Latency heatmap
   - Operações por tipo

3. **System Metrics**
   - CPU e memória
   - Threads ativas
   - Database connections (PostgreSQL)
   - Garbage collection

### Métricas Disponíveis

#### Backtest Metrics

```promql
# Total de backtests executados
nexus_backtests_total

# Por estratégia
nexus_backtests_total{strategy_type="sma_crossover"}

# Por status (completed, failed)
nexus_backtests_total{status="completed"}

# Duração de backtest (percentis)
histogram_quantile(0.95,
  rate(nexus_backtest_duration_seconds_bucket{strategy_type="sma_crossover"}[5m])
)
```

#### Trade Metrics

```promql
# Total de trades
nexus_trades_total

# Trades de compra vs venda
nexus_trades_total{side="BUY"}
nexus_trades_total{side="SELL"}

# Por símbolo
nexus_trades_total{symbol="AAPL"}

# P&L médio
rate(nexus_trade_pnl_sum[5m]) / rate(nexus_trade_pnl_count[5m])
```

#### C++ Engine Metrics

```promql
# Latência do engine em nanosegundos
nexus_cpp_engine_latency_nanoseconds

# Por operação
nexus_cpp_engine_latency_nanoseconds{operation="signal_generation"}
nexus_cpp_engine_latency_nanoseconds{operation="backtest_run"}

# Sinais gerados
nexus_signals_generated_total

# Por tipo de sinal
nexus_signals_generated_total{signal_type="BUY"}
```

#### API Metrics

```promql
# Total de chamadas para APIs externas
nexus_api_calls_total

# Por API
nexus_api_calls_total{api_name="finnhub"}
nexus_api_calls_total{api_name="alpha_vantage"}

# Latência de API
nexus_api_latency_seconds

# Taxa de erro
rate(nexus_api_calls_total{status="error"}[5m])
```

#### System Metrics

```promql
# Estratégias ativas
nexus_active_strategies

# Taxa de cache hit
nexus_cache_hit_rate
```

---

## 🎨 Grafana Dashboards

### Dashboards Incluídos

Três dashboards específicos para trading algorítmico:

#### 1. Nexus Trading Metrics Dashboard

**O que monitora**:
- **Backtests**: Total, rate, duration distribution
- **Trades**: Total, by symbol, by signal type, P&L
- **API Calls**: Market data providers, latency, errors
- **Strategies**: Active strategies, most used strategies

**Quando usar**:
- Monitorar atividade de trading
- Ver quais estratégias estão sendo testadas
- Identificar problemas com APIs de market data
- Análise de volume de trades

**Painéis incluídos**:
1. Backtests Executed (Time Series)
2. Backtest Duration Distribution (Heatmap)
3. Trades by Symbol (Pie Chart)
4. API Calls by Provider (Stacked Area)
5. Active Strategies (Gauge)
6. Backtest Success Rate (Stat)
7. Average P&L (Time Series)
8. Market Data Cache Hit Rate (Gauge)

#### 2. C++ Engine Performance Dashboard

**O que monitora**:
- **Latency**: p50, p95, p99 do C++ engine
- **Throughput**: Signals/second, operations/second
- **Heatmap**: Latency distribution ao longo do tempo
- **Operations**: Breakdown por tipo (signal_generation, backtest_run, optimization)

**Quando usar**:
- Performance tuning do C++ engine
- Identificar degradação de performance
- Comparar latência de diferentes estratégias
- Validar otimizações (SIMD, lock-free)

**Painéis incluídos**:
1. Engine Latency Percentiles (Time Series com 3 linhas)
2. Throughput (Signals/s) (Graph)
3. Latency Heatmap (Heatmap)
4. Operations Breakdown (Bar Chart)
5. Average Latency by Operation (Table)
6. Slowest Operations (Top 10 List)
7. Latency vs Throughput (Scatter Plot)

#### 3. System Metrics Dashboard

**O que monitora**:
- **CPU**: Usage percentage
- **Memory**: Heap usage, allocation rate
- **Threads**: Active threads, daemon threads
- **Database**: PostgreSQL connections (active, idle)
- **Garbage Collection**: GC pause time, collections
- **Network**: Bytes sent/received

**Quando usar**:
- Investigar resource usage
- Detectar memory leaks
- Otimizar thread pools
- Monitor database connections

**Painéis incluídos**:
1. CPU Usage (Gauge)
2. Memory Usage (Time Series)
3. Thread Count (Time Series)
4. Database Connections (Stacked Graph)
5. GC Pause Time (Histogram)
6. Network I/O (Area Chart)
7. Process Uptime (Stat)

### Como Adicionar Novo Dashboard

1. **Acesse Grafana**: http://localhost:3000
2. **Clique em "+"** → **Import**
3. **Cole o ID do dashboard** ou arraste JSON
4. **Selecione datasources**:
   - Prometheus: Metrics
   - Loki: Logs
   - Tempo: Traces
5. **Clique em Import**

**Dashboards recomendados da comunidade**:
- **11378**: JVM Micrometer (para backend Python)
- **1860**: Node Exporter (se adicionar métricas de host)
- **7587**: PostgreSQL Database

---

## 🔗 Correlação entre Pilares

### Tutorial Prático: Debugar um Backtest Lento

Deixa eu te mostrar um exemplo real de como eu uso a stack completa para debugar problemas de performance.

**Cenário**: Backtests de SMA Crossover em AAPL estão demorando mais de 5 segundos (target: < 2s).

#### Passo 1: Começar com Metrics (Prometheus)

```promql
# Identificar estratégias lentas
topk(5,
  histogram_quantile(0.95,
    rate(nexus_backtest_duration_seconds_bucket[5m])
  ) by (strategy_type)
)
```

**Resultado**: `sma_crossover` tem p95 = 5.2s (muito lento!)

**Conclusão**: Confirma o problema! 95% dos backtests SMA demoram 5.2 segundos.

#### Passo 2: Ir para Traces (Tempo)

**Buscar**:
- Service: `nexus-engine`
- Operation: `run_backtest`
- Tags: `strategy.type = sma_crossover`
- Min Duration: 5000ms

**Encontrar** trace específico lento:
```
RunBacktestUseCase (5.2s total)
  MarketDataService.fetch_daily (3.8s)  ← Gargalo!
    AlphaVantageAdapter.get_daily (3.75s)
      HTTP Request (3.7s)
      Cache Write (50ms)
  CppBridge.run_backtest (1.3s)
    BacktestEngine (C++) (1.28s)
  BacktestRepository.save (100ms)
```

**Conclusão**: Achei o gargalo! A API Alpha Vantage está demorando 3.7s dos 5.2s totais.

#### Passo 3: Ver Logs (Loki)

**Query**:
```logql
{app="nexus-engine"}
| json
| trace_id="550e8400e29b41d4a716446655440000"
| api_name="alpha_vantage"
```

**Logs revelam**:
```json
{
  "level": "WARN",
  "message": "Alpha Vantage API slow response",
  "trace_id": "550e8400e29b41d4a716446655440000",
  "api_name": "alpha_vantage",
  "latency_ms": 3700,
  "cache_miss": true,
  "symbol": "AAPL",
  "rate_limit_remaining": 4
}
```

**Conclusão**: Cache miss! Dados não estavam cacheados, causou chamada lenta à API.

#### Passo 4: Solução

**Diagnóstico**: Cache não está funcionando corretamente para dados diários de AAPL.

**Fix aplicado**:
```python
# backend/python/src/application/services/market_data_service.py

# TTL de 24h para dados diários (não mudam intraday)
@cached(ttl=86400)  # 24 horas
def fetch_daily(self, symbol: Symbol, time_range: TimeRange) -> pd.DataFrame:
    """Busca dados diários com cache."""
    # ...
```

**Validação do fix (usando a stack)**:
1. **Metrics**: p95 caiu de 5.2s para 1.4s ✅
2. **Metrics**: Cache hit rate subiu de 20% para 95% ✅
3. **Traces**: MarketDataService span caiu de 3.8s para 50ms ✅
4. **Logs**: "cache_hit: true" aparecendo nos logs ✅

**Resultado**: Problema resolvido em 15 minutos! Isso é o poder da observabilidade completa.

---

## 🚨 Alerting (Implementação Futura - FASE 33)

### Alerts Planejados

Vou implementar os seguintes alertas críticos:

```yaml
# grafana/provisioning/alerting/rules.yml
groups:
  - name: trading-engine
    interval: 1m
    rules:
      # Backtest muito lento
      - alert: HighBacktestLatency
        expr: |
          histogram_quantile(0.95,
            rate(nexus_backtest_duration_seconds_bucket[5m])
          ) > 5
        for: 10m
        annotations:
          summary: "Backtests estão lentos (p95 > 5s)"
          description: "Performance degradou. Investigar gargalo."

      # Taxa de erro alta
      - alert: HighBacktestFailureRate
        expr: |
          rate(nexus_backtests_total{status="failed"}[5m]) /
          rate(nexus_backtests_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Taxa de falha > 10%"
          description: "Muitos backtests falhando. Verificar logs."

      # API externa com problemas
      - alert: HighAPIErrorRate
        expr: |
          rate(nexus_api_calls_total{status="error"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "API externa com > 5% de erro"
          description: "{{ $labels.api_name }} está com problemas"

      # C++ engine muito lento
      - alert: CppEngineSlowdown
        expr: |
          histogram_quantile(0.95,
            rate(nexus_cpp_engine_latency_nanoseconds_bucket[5m])
          ) > 100000  # 100µs
        for: 10m
        annotations:
          summary: "C++ engine lento (p95 > 100µs)"
          description: "Performance do engine degradou"

      # Cache hit rate baixo
      - alert: LowCacheHitRate
        expr: nexus_cache_hit_rate < 70
        for: 15m
        annotations:
          summary: "Cache hit rate < 70%"
          description: "Cache não está efetivo. Muitas chamadas para APIs externas."
```

### Canais de Notificação Planejados

**Slack** (para time de desenvolvimento):
```yaml
contact_points:
  - name: slack-trading-alerts
    type: slack
    settings:
      url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      title: "🚨 Nexus Engine Alert"
      text: |
        *Alert*: {{ .Labels.alertname }}
        *Summary*: {{ .Annotations.summary }}
        *Description*: {{ .Annotations.description }}
        *Severity*: {{ .Labels.severity }}
```

**Email** (para operações):
```yaml
contact_points:
  - name: email-ops
    type: email
    settings:
      addresses: ops@trading-firm.com
```

---

## 📊 Melhores Práticas

### 1. Logging

Structured logging em primeira pessoa. Veja exemplos:

**✅ Bom**:
```python
logger.info(
    "Backtest completed",
    strategy_id=str(strategy.id),
    strategy_type=strategy.strategy_type,
    symbol=symbol,
    total_return=result.total_return,
    sharpe_ratio=result.sharpe_ratio,
    total_trades=result.total_trades
)
```

**❌ Ruim**:
```python
logger.info(f"Backtest completed: {result}")
```

**Por quê**:
- JSON parsing no Loki funciona melhor
- Posso filtrar por campos específicos
- Performance (lazy evaluation)
- Segurança (não logar API keys)

### 2. Tracing

Decidi adicionar spans customizados em operações críticas:

**✅ Bom**:
```python
@traced(name="backtest.run")
def execute(self, strategy_id: UUID, symbol: Symbol, ...):
    with tracer.start_span("fetch_market_data") as span:
        span.set_attribute("symbol", str(symbol))
        span.set_attribute("days", len(data))
        data = market_data_service.fetch_daily(symbol, time_range)

    with tracer.start_span("cpp_engine.run") as span:
        span.set_attribute("strategy_type", strategy.strategy_type)
        result = cpp_bridge.run_backtest(...)
```

**❌ Ruim**:
- Criar spans demais (overhead)
- Não adicionar atributos úteis
- Ignorar exceptions em spans

### 3. Metrics

Métricas com tags úteis para filtragem:

**✅ Bom**:
```python
# Reuse metrics instance (singleton)
metrics = get_metrics()

# Increment with useful labels
metrics.backtests_total.labels(
    strategy_type="sma_crossover",
    status="completed"
).inc()

# Record timing
metrics.backtest_duration_seconds.labels(
    strategy_type="sma_crossover"
).observe(duration)
```

**❌ Ruim**:
- Alta cardinalidade em tags (ex: user_id, backtest_id)
- Criar metrics dentro de loops
- Não usar labels para agrupamento

### 4. Retenção de Dados

**Recomendações que Implementei**:

| Pilar       | Dev     | Prod    | Por quê                     |
|-------------|---------|---------|-----------------------------|
| **Logs**    | 7 dias  | 30 dias | Logs ocupam muito espaço    |
| **Traces**  | 2 dias  | 7 dias  | Traces são muito granulares |
| **Metrics** | 15 dias | 90 dias | Métricas compactam bem      |

**Configuração**:

Loki:
```yaml
# devops/observability/loki/loki-config.yml
limits_config:
  retention_period: 720h  # 30 dias
```

Tempo:
```yaml
# devops/observability/tempo/tempo-config.yml
storage:
  trace:
    block:
      retention: 168h  # 7 dias
```

Prometheus:
```yaml
# devops/observability/prometheus/prometheus.yml
storage:
  tsdb:
    retention.time: 15d
    retention.size: 50GB
```

---

## 🛠️ Troubleshooting

### Problema: Logs não aparecem no Loki

**Verificar**:
```bash
# 1. Container Loki está rodando?
docker ps | grep loki

# 2. Porta 3100 acessível?
curl http://localhost:3100/ready

# 3. Backend está enviando logs?
docker logs nexus-backend | grep loki
```

**Solução comum**:
- Verificar `loki_logger.py`: URL do Loki correta
- Firewall bloqueando porta 3100
- Loki sem espaço em disco
- Formato de log incorreto

### Problema: Traces não aparecem no Tempo

**Verificar**:
```bash
# 1. OpenTelemetry endpoint correto?
curl http://localhost:4318/v1/traces

# 2. Backend está exportando traces?
docker logs nexus-backend | grep tempo

# 3. Verificar configuração
# backend/python/config/settings.py: tempo_url correto
```

**Solução comum**:
- `tempo_url` incorreto no settings
- Porta 4317 (gRPC) ou 4318 (HTTP) bloqueada
- OpenTelemetry SDK não inicializado
- Traces muito grandes (aumentar limites)

### Problema: Métricas não aparecem no Prometheus

**Verificar**:
```bash
# 1. Endpoint /metrics acessível?
curl http://localhost:9090/metrics

# 2. Prometheus está scraping?
# Acesse: http://localhost:9090/targets

# 3. Métricas sendo exportadas?
curl http://nexus-backend:9090/metrics | grep nexus_
```

**Solução comum**:
- `start_metrics_server()` não foi chamado
- Porta 9090 já em uso
- Prometheus não configurado para scraping
- Labels com alta cardinalidade (evitar user_id, trace_id)

### Problema: Dashboards não carregam

**Verificar**:
```bash
# 1. Datasources configurados?
# Acesse: http://localhost:3000/datasources

# 2. Provisioning funcionou?
docker logs grafana | grep provisioning

# 3. JSONs corretos?
ls devops/observability/grafana/dashboards/*.json
```

**Solução comum**:
- Datasources não provisionados
- Permissões incorretas nos arquivos JSON
- UIDs duplicados nos dashboards
- Queries incompatíveis com versão do Grafana

---

## 📚 Recursos que Usei para Aprender

### Documentação Oficial (Onde Aprendi)

Stack de observabilidade:

- [Grafana Docs](https://grafana.com/docs/) - Excelente para começar
- [Loki Docs](https://grafana.com/docs/loki/latest/) - LogQL queries
- [Tempo Docs](https://grafana.com/docs/tempo/latest/) - Distributed tracing
- [Prometheus Docs](https://prometheus.io/docs/) - PromQL e best practices
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/) - Instrumentação
- [Prometheus Python Client](https://github.com/prometheus/client_python) - Exportar métricas

### Tutoriais Recomendados

- [Grafana Fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) - Tutorial interativo
- [LogQL Tutorial](https://grafana.com/docs/loki/latest/logql/) - Queries de logs
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/) - Queries de métricas
- [OpenTelemetry Getting Started](https://opentelemetry.io/docs/instrumentation/python/getting-started/) - Traces

### Livros e Papers

Estudei estes recursos para entender observabilidade em sistemas de trading:

- **"Distributed Systems Observability"** - Cindy Sridharan
  - Como implementar observabilidade em microsserviços
- **"The Art of Monitoring"** - James Turnbull
  - Best practices de monitoring
- **"Prometheus: Up & Running"** - Brian Brazil
  - Deep dive em Prometheus

### Comunidade (Onde Tirar Dúvidas)

- [Grafana Community](https://community.grafana.com/) - Forum ativo
- [CNCF Slack](https://slack.cncf.io/) - Canais #prometheus, #opentelemetry, #tempo
- [Prometheus Users Google Group](https://groups.google.com/g/prometheus-users)

---

## 🔗 Links Úteis

- [README Principal](../README.md)
- [Arquitetura](ARCHITECTURE.md)
- [API Reference](API.md)
- [User Guide](GUIDE.md)

### Stack de Observabilidade

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

### Configurações

- [Prometheus Config](../devops/observability/prometheus/prometheus.yml)
- [Loki Config](../devops/observability/loki/loki-config.yml)
- [Tempo Config](../devops/observability/tempo/tempo-config.yml)
- [Grafana Datasources](../devops/observability/grafana/provisioning/datasources.yml)
- [Grafana Dashboards](../devops/observability/grafana/provisioning/dashboards.yml)

### Código Fonte

- [Prometheus Metrics](../backend/python/src/infrastructure/telemetry/prometheus_metrics.py)
- [Loki Logger](../backend/python/src/infrastructure/telemetry/loki_logger.py)
- [Tempo Tracer](../backend/python/src/infrastructure/telemetry/tempo_tracer.py)

---

**Nexus Engine Trading Platform** - Desenvolvido por [Thiago Di Faria](https://github.com/thiagodifaria)

Se você chegou até aqui e conseguiu explorar a stack de observabilidade completa, parabéns! Você agora sabe como monitorar, debugar e otimizar um sistema de trading algorítmico de alta performance. Implementei tudo isso pensando em facilitar sua vida quando estiver operando backtests em produção! 🚀📊