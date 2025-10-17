// backend/python/src/nexus_bindings/optimization_bindings.cpp
//
// Bindings PyBind11 para otimização de estratégias.
// Implementei estes bindings para permitir otimização automatizada de parâmetros.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "optimization/strategy_optimizer.h"
#include "optimization/grid_search.h"
#include "optimization/genetic_algorithm.h"
#include "strategies/abstract_strategy.h"
#include "analytics/performance_metrics.h"

namespace py = pybind11;

using namespace nexus::optimization;
using namespace nexus::strategies;
using namespace nexus::analytics;

PYBIND11_MODULE(nexus_optimization, m) {
    m.doc() = R"doc(
        Nexus Strategy Optimization Python Bindings

        Otimização automatizada de parâmetros de estratégias usando:
        - Grid Search: Busca exaustiva
        - Genetic Algorithms: Otimização evolutiva

        Referências:
        - Grid Search: https://en.wikipedia.org/wiki/Hyperparameter_optimization
        - Genetic Algorithms: https://en.wikipedia.org/wiki/Genetic_algorithm
    )doc";

    // ========== Optimization Result ==========

    py::class_<OptimizationResult>(m, "OptimizationResult",
        R"doc(
            Resultado de uma iteração de otimização.

            Armazena parâmetros testados, métricas de performance e fitness score.
            Uso fitness_score para ranking de resultados durante otimização.
        )doc")
        .def(py::init<>())
        .def_readwrite("parameters", &OptimizationResult::parameters,
                      "Parâmetros testados (dict)")
        .def_readwrite("performance", &OptimizationResult::performance,
                      "Métricas de performance")
        .def_readwrite("fitness_score", &OptimizationResult::fitness_score,
                      "Score de fitness para ranking");

    // ========== Strategy Optimizer ==========

    py::class_<StrategyOptimizer>(m, "StrategyOptimizer",
        R"doc(
            Otimizador de estratégias.

            Executa múltiplos backtests com diferentes parâmetros para encontrar
            configuração ótima baseado em métrica de performance escolhida.

            Decidi implementar grid search como baseline. Algoritmos genéticos
            virão em fases futuras para otimizar busca em espaços grandes.
        )doc")
        .def(py::init<std::unique_ptr<AbstractStrategy>>(),
             py::arg("strategy_template"),
             "Construtor com estratégia template")
        .def("grid_search", &StrategyOptimizer::grid_search,
             py::arg("parameter_grid"),
             "Executa grid search exaustivo")
        .def("get_best_result", &StrategyOptimizer::get_best_result,
             "Retorna melhor resultado da última otimização");

    // ========== Grid Search ==========

    py::class_<GridSearch>(m, "GridSearch",
        R"doc(
            Grid Search para otimização de parâmetros.

            Busca exaustiva testando todas combinações de parâmetros.
            Uso quando o espaço de parâmetros é pequeno o suficiente.

            Complexidade: O(n^k) onde n=valores e k=parâmetros
        )doc")
        .def(py::init<std::unique_ptr<AbstractStrategy>>(),
             py::arg("strategy_template"))
        .def("search", &GridSearch::search,
             py::arg("parameter_grid"),
             "Executa busca em grid de parâmetros")
        .def("get_best_result", &GridSearch::get_best_result,
             "Retorna melhor resultado encontrado");

    // ========== Genetic Algorithm ==========

    py::class_<GeneticAlgorithm>(m, "GeneticAlgorithm",
        R"doc(
            Algoritmo genético para otimização.

            Usa evolução simulada para explorar espaço de parâmetros:
            - Selection: Escolhe melhores indivíduos
            - Crossover: Combina parâmetros
            - Mutation: Adiciona variação aleatória

            Uso quando espaço de parâmetros é grande demais para grid search.

            Referência: https://en.wikipedia.org/wiki/Genetic_algorithm
        )doc")
        .def(py::init<std::unique_ptr<AbstractStrategy>, size_t, size_t, double, double>(),
             py::arg("strategy_template"),
             py::arg("population_size") = 50,
             py::arg("num_generations") = 100,
             py::arg("mutation_rate") = 0.1,
             py::arg("crossover_rate") = 0.7,
             "Construtor com hiperparâmetros do algoritmo genético")
        .def("optimize", &GeneticAlgorithm::optimize,
             py::arg("parameter_ranges"),
             "Executa otimização genética")
        .def("get_best_result", &GeneticAlgorithm::get_best_result,
             "Retorna melhor resultado (indivíduo)")
        .def("get_population_statistics", &GeneticAlgorithm::get_population_statistics,
             "Retorna estatísticas da população atual");

    m.attr("__version__") = "0.7.0";
}
