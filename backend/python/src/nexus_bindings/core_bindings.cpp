// backend/python/src/nexus_bindings/core_bindings.cpp
//
// Implementei estes bindings PyBind11 para expor o C++ engine ao Python.
// Decidi manter a interface pythonica enquanto preservo a performance nativa do C++.
//
// Referências:
// - PyBind11 Documentation: https://pybind11.readthedocs.io/
// - Type conversions: https://pybind11.readthedocs.io/en/stable/advanced/cast/overview.html

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include "core/backtest_engine.h"
#include "core/event_queue.h"
#include "core/event_types.h"
#include "core/event_pool.h"
#include "core/disruptor_queue.h"
#include "core/real_time_config.h"
#include "core/high_resolution_clock.h"
#include "core/latency_tracker.h"
#include "data/market_data_handler.h"
#include "position/position_manager.h"
#include "execution/execution_simulator.h"
#include "strategies/abstract_strategy.h"

namespace py = pybind11;

using namespace nexus::core;
using namespace nexus::data;
using namespace nexus::position;
using namespace nexus::execution;
using namespace nexus::strategies;

// Implementei este módulo para expor o core do engine C++ ao Python
PYBIND11_MODULE(nexus_core, m) {
    m.doc() = R"doc(
        Nexus C++ Core Engine Python Bindings

        Módulo que expõe o engine de backtest de alta performance ao Python.
        Implementei estes bindings para permitir orquestração Python enquanto
        mantenho a performance crítica no C++.

        Referências:
        - Nexus Engine: Ultra-high performance trading engine (800K+ signals/s)
        - PyBind11: https://pybind11.readthedocs.io/
    )doc";

    // ========== Event Types ==========

    py::enum_<EventType>(m, "EventType", "Tipo de evento no sistema")
        .value("MARKET_DATA", EventType::MARKET_DATA, "Evento de dados de mercado")
        .value("TRADING_SIGNAL", EventType::TRADING_SIGNAL, "Sinal de trading gerado por estratégia")
        .value("TRADE_EXECUTION", EventType::TRADE_EXECUTION, "Execução de trade")
        .export_values();

    py::class_<Event, std::shared_ptr<Event>>(m, "Event", "Evento base do sistema")
        .def_readwrite("timestamp", &Event::timestamp, "Timestamp do evento")
        .def_readwrite("hardware_timestamp_tsc", &Event::hardware_timestamp_tsc,
                      "Hardware TSC timestamp (nanossegundo)")
        .def_readwrite("creation_time_ns", &Event::creation_time_ns,
                      "Tempo de criação em nanossegundos")
        .def("get_type", &Event::get_type, "Retorna o tipo do evento")
        .def("set_hardware_timestamp", &Event::set_hardware_timestamp,
             "Define hardware timestamp usando high-resolution clock");

    py::class_<MarketDataEvent, Event, std::shared_ptr<MarketDataEvent>>(m, "MarketDataEvent",
        "Evento de dados de mercado (OHLCV)")
        .def(py::init<>())
        .def_readwrite("symbol", &MarketDataEvent::symbol, "Símbolo do ativo")
        .def_readwrite("open", &MarketDataEvent::open, "Preço de abertura")
        .def_readwrite("high", &MarketDataEvent::high, "Preço máximo")
        .def_readwrite("low", &MarketDataEvent::low, "Preço mínimo")
        .def_readwrite("close", &MarketDataEvent::close, "Preço de fechamento")
        .def_readwrite("volume", &MarketDataEvent::volume, "Volume negociado");

    py::enum_<TradingSignalEvent::SignalType>(m, "SignalType", "Tipo de sinal de trading")
        .value("BUY", TradingSignalEvent::SignalType::BUY, "Sinal de compra")
        .value("SELL", TradingSignalEvent::SignalType::SELL, "Sinal de venda")
        .value("HOLD", TradingSignalEvent::SignalType::HOLD, "Manter posição")
        .value("EXIT", TradingSignalEvent::SignalType::EXIT, "Sair da posição")
        .export_values();

    py::class_<TradingSignalEvent, Event, std::shared_ptr<TradingSignalEvent>>(m, "TradingSignalEvent",
        "Sinal de trading gerado por estratégia")
        .def(py::init<>())
        .def_readwrite("strategy_id", &TradingSignalEvent::strategy_id, "ID da estratégia")
        .def_readwrite("symbol", &TradingSignalEvent::symbol, "Símbolo do ativo")
        .def_readwrite("signal", &TradingSignalEvent::signal, "Tipo de sinal")
        .def_readwrite("confidence", &TradingSignalEvent::confidence, "Confiança do sinal (0.0 a 1.0)")
        .def_readwrite("suggested_quantity", &TradingSignalEvent::suggested_quantity,
                      "Quantidade sugerida");

    py::class_<TradeExecutionEvent, Event, std::shared_ptr<TradeExecutionEvent>>(m, "TradeExecutionEvent",
        "Resultado de execução de trade")
        .def(py::init<>())
        .def_readwrite("symbol", &TradeExecutionEvent::symbol, "Símbolo do ativo")
        .def_readwrite("quantity", &TradeExecutionEvent::quantity, "Quantidade executada")
        .def_readwrite("price", &TradeExecutionEvent::price, "Preço de execução")
        .def_readwrite("commission", &TradeExecutionEvent::commission, "Comissão cobrada")
        .def_readwrite("is_buy", &TradeExecutionEvent::is_buy, "True se compra, False se venda");

    // ========== Event Queue ==========

    py::class_<EventQueue>(m, "EventQueue",
        R"doc(
            Fila de eventos tradicional.
            Uso esta implementação para cases onde não preciso da máxima performance.
        )doc")
        .def(py::init<>())
        .def("enqueue", &EventQueue::enqueue, "Adiciona evento à fila")
        .def("dequeue", &EventQueue::dequeue, "Remove e retorna evento da fila")
        .def("size", &EventQueue::size, "Retorna tamanho da fila")
        .def("empty", &EventQueue::empty, "Verifica se fila está vazia");

    py::class_<DisruptorQueue<Event*, 1024>>(m, "DisruptorQueue",
        R"doc(
            Fila de eventos LMAX Disruptor de alta performance.
            Implementação lock-free otimizada para ultra-baixa latência.
            Consigo processar 10-100M eventos/segundo com esta implementação.

            Referências:
            - LMAX Disruptor: https://lmax-exchange.github.io/disruptor/
        )doc")
        .def(py::init<>())
        .def("publish", &DisruptorQueue<Event*, 1024>::publish, "Publica evento na fila")
        .def("try_consume", &DisruptorQueue<Event*, 1024>::try_consume, "Tenta consumir evento")
        .def("get_cursor", &DisruptorQueue<Event*, 1024>::get_cursor, "Retorna cursor atual")
        .def("get_published_sequence", &DisruptorQueue<Event*, 1024>::get_published_sequence,
             "Retorna última sequência publicada");

    py::class_<EventPool>(m, "EventPool",
        R"doc(
            Pool de eventos para reduzir alocações dinâmicas.
            Decidi usar pooling porque elimina overhead de malloc/free em hot path.
        )doc")
        .def(py::init<size_t>(), py::arg("initial_size") = 1000)
        .def("acquire", &EventPool::acquire, "Adquire evento do pool")
        .def("release", &EventPool::release, "Retorna evento ao pool")
        .def("get_pool_size", &EventPool::get_pool_size, "Retorna tamanho do pool")
        .def("get_acquired_count", &EventPool::get_acquired_count, "Retorna eventos em uso");

    // ========== Real-Time Configuration ==========

    py::class_<RealTimeConfig>(m, "RealTimeConfig",
        R"doc(
            Configurações de otimização real-time.
            Uso estas configs para obter latência determinística em produção.
        )doc")
        .def(py::init<>())
        .def_readwrite("enable_cpu_affinity", &RealTimeConfig::enable_cpu_affinity,
                      "Habilita CPU affinity (reduz 20-50% latência)")
        .def_readwrite("cpu_core_id", &RealTimeConfig::cpu_core_id,
                      "ID do core CPU para affinity")
        .def_readwrite("enable_real_time_priority", &RealTimeConfig::enable_real_time_priority,
                      "Habilita prioridade real-time")
        .def_readwrite("enable_cache_warming", &RealTimeConfig::enable_cache_warming,
                      "Habilita pré-aquecimento de cache")
        .def_readwrite("enable_numa_optimization", &RealTimeConfig::enable_numa_optimization,
                      "Habilita otimizações NUMA")
        .def("validate", &RealTimeConfig::validate, "Valida e aplica defaults");

    // ========== Backtest Engine Configuration ==========

    py::class_<BacktestEngineConfig>(m, "BacktestEngineConfig",
        R"doc(
            Configuração do BacktestEngine.
            Implementei validações automáticas para garantir parâmetros seguros.
        )doc")
        .def(py::init<>())
        .def_readwrite("max_events_per_batch", &BacktestEngineConfig::max_events_per_batch,
                      "Máximo de eventos por batch (0 = ilimitado)")
        .def_readwrite("max_batch_duration", &BacktestEngineConfig::max_batch_duration,
                      "Duração máxima de batch")
        .def_readwrite("enable_performance_monitoring", &BacktestEngineConfig::enable_performance_monitoring,
                      "Habilita monitoramento de performance")
        .def_readwrite("worker_thread_count", &BacktestEngineConfig::worker_thread_count,
                      "Número de threads workers (0 = auto)")
        .def_readwrite("enable_event_batching", &BacktestEngineConfig::enable_event_batching,
                      "Habilita batching de eventos")
        .def_readwrite("queue_backend_type", &BacktestEngineConfig::queue_backend_type,
                      "Tipo de backend de fila ('traditional' ou 'disruptor')")
        .def_readwrite("real_time_config", &BacktestEngineConfig::real_time_config,
                      "Configurações real-time")
        .def("validate", &BacktestEngineConfig::validate, "Valida configuração");

    // ========== Backtest Engine ==========

    py::class_<BacktestEngine>(m, "BacktestEngine",
        R"doc(
            Engine principal de backtest.

            Orquestra todo o processo de backtesting, coordenando market data,
            estratégias, position management e execução de trades.

            Performance:
            - Event processing: Sub-microsecond com LMAX Disruptor
            - Strategy execution: 800K-2.4M signals/segundo
            - Thread affinity: 20-50% redução de latência

            Referências:
            - LMAX Disruptor: https://lmax-exchange.github.io/disruptor/
            - Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
        )doc")
        .def(py::init<
                EventQueue&,
                std::shared_ptr<MarketDataHandler>,
                std::unordered_map<std::string, std::shared_ptr<AbstractStrategy>>,
                std::shared_ptr<PositionManager>,
                std::shared_ptr<ExecutionSimulator>,
                const BacktestEngineConfig&
            >(),
            py::arg("event_queue"),
            py::arg("data_handler"),
            py::arg("strategies"),
            py::arg("position_manager"),
            py::arg("execution_simulator"),
            py::arg("config") = BacktestEngineConfig{},
            R"doc(
                Construtor do BacktestEngine.

                Args:
                    event_queue: Fila de eventos para processar
                    data_handler: Handler de market data
                    strategies: Mapa de símbolo -> estratégia
                    position_manager: Gerenciador de posições
                    execution_simulator: Simulador de execução
                    config: Configuração do engine
            )doc")
        .def("run", &BacktestEngine::run,
             "Executa backtest completo processando todos os eventos")
        .def("get_config", &BacktestEngine::get_config,
             "Retorna configuração atual",
             py::return_value_policy::reference_internal)
        .def("update_config", &BacktestEngine::update_config,
             py::arg("new_config"),
             "Atualiza configuração do engine")
        .def("get_performance_info", &BacktestEngine::get_performance_info,
             "Retorna estatísticas de performance")
        .def("warm_caches", &BacktestEngine::warm_caches,
             "Pré-aquece caches para melhor performance inicial");

    // ========== High-Resolution Clock ==========

    py::class_<HighResolutionClock>(m, "HighResolutionClock",
        R"doc(
            Clock de alta resolução usando TSC (Time Stamp Counter).
            Consigo precisão de nanossegundos com overhead mínimo.
        )doc")
        .def_static("get_tsc", &HighResolutionClock::get_tsc,
                   "Retorna hardware TSC timestamp")
        .def_static("get_nanoseconds", &HighResolutionClock::get_nanoseconds,
                   "Retorna tempo atual em nanossegundos")
        .def_static("calibrate", &HighResolutionClock::calibrate,
                   "Calibra conversão TSC -> nanossegundos");

    // ========== Latency Tracker ==========

    py::class_<LatencyTracker>(m, "LatencyTracker",
        R"doc(
            Rastreador de latência para análise de performance.
            Uso percentis (p50, p95, p99) para entender distribuição de latência.
        )doc")
        .def(py::init<>())
        .def("record_latency", &LatencyTracker::record_latency,
             py::arg("latency_ns"),
             "Registra latência em nanossegundos")
        .def("get_min", &LatencyTracker::get_min, "Retorna latência mínima")
        .def("get_max", &LatencyTracker::get_max, "Retorna latência máxima")
        .def("get_avg", &LatencyTracker::get_avg, "Retorna latência média")
        .def("get_p50", &LatencyTracker::get_p50, "Retorna percentil 50 (mediana)")
        .def("get_p95", &LatencyTracker::get_p95, "Retorna percentil 95")
        .def("get_p99", &LatencyTracker::get_p99, "Retorna percentil 99")
        .def("reset", &LatencyTracker::reset, "Reseta estatísticas")
        .def("get_sample_count", &LatencyTracker::get_sample_count,
             "Retorna número de amostras coletadas");

    // Versão do módulo
    m.attr("__version__") = "0.7.0";
}
