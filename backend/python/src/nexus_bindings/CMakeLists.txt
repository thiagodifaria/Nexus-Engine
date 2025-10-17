# backend/python/src/nexus_bindings/CMakeLists.txt
#
# Sistema de build para PyBind11 bindings.
# Implementei este CMake script para compilar os bindings Python do C++ engine.
#
# Referências:
# - PyBind11 CMake: https://pybind11.readthedocs.io/en/stable/compiling.html
# - CMake Documentation: https://cmake.org/documentation/

cmake_minimum_required(VERSION 3.18)
project(nexus_python_bindings)

# Configurações do compilador C++
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Decidi usar C++20 porque o engine C++ já usa e preciso de compatibilidade
message(STATUS "Configurando bindings Python com C++20")

# Encontrar Python e PyBind11
# Uso find_package porque facilita integração com diferentes versões do Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

message(STATUS "Python encontrado: ${Python3_VERSION}")
message(STATUS "PyBind11 encontrado: ${pybind11_VERSION}")

# Incluir diretórios do C++ engine
# Aponto para o backend C++ para acessar os headers
set(CPP_ENGINE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../cpp")
include_directories(${CPP_ENGINE_DIR})

# Flags de compilação otimizadas
# Implementei estas flags para obter máxima performance nos bindings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(
        -O3                    # Máxima otimização
        -march=native          # Otimizações específicas da CPU
        -mtune=native
        -Wall                  # Todos warnings
        -Wextra
        -Wpedantic
        -fPIC                  # Position Independent Code para shared libraries
        -fvisibility=hidden    # Esconde símbolos não exportados
    )
elseif(MSVC)
    add_compile_options(
        /O2                    # Máxima otimização no MSVC
        /W4                    # Warning level 4
        /EHsc                  # Exception handling
        /MP                    # Multi-processor compilation
    )
endif()

# ========== Core Bindings ==========
# Binding para o core do engine (BacktestEngine, EventQueue, etc)

pybind11_add_module(nexus_core MODULE core_bindings.cpp)

# Linkar com a biblioteca do C++ engine
# Assumo que o engine C++ já foi compilado e está disponível
target_link_libraries(nexus_core PRIVATE
    # Se o engine C++ estiver compilado como biblioteca:
    # nexus_engine_core
    # nexus_engine_data
    # nexus_engine_position
    # nexus_engine_execution
    # nexus_engine_strategies
)

# Propriedades do módulo
set_target_properties(nexus_core PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    INTERPROCEDURAL_OPTIMIZATION TRUE
    PREFIX "${PYTHON_MODULE_PREFIX}"
    SUFFIX "${PYTHON_MODULE_EXTENSION}"
)

# Instalação do módulo Python
# Instalo no diretório src/nexus_bindings para fácil importação
install(TARGETS nexus_core
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# ========== Strategies Bindings ==========
# Será criado na FASE 3

# pybind11_add_module(nexus_strategies MODULE strategies_bindings.cpp)
# target_link_libraries(nexus_strategies PRIVATE nexus_engine_strategies)
# install(TARGETS nexus_strategies LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})

# ========== Execution Bindings ==========
# Será criado na FASE 4

# pybind11_add_module(nexus_execution MODULE execution_bindings.cpp)
# target_link_libraries(nexus_execution PRIVATE nexus_engine_execution)
# install(TARGETS nexus_execution LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})

# ========== Analytics Bindings ==========
# Será criado na FASE 4

# pybind11_add_module(nexus_analytics MODULE analytics_bindings.cpp)
# target_link_libraries(nexus_analytics PRIVATE nexus_engine_analytics)
# install(TARGETS nexus_analytics LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})

# ========== Optimization Bindings ==========
# Será criado na FASE 4

# pybind11_add_module(nexus_optimization MODULE optimization_bindings.cpp)
# target_link_libraries(nexus_optimization PRIVATE nexus_engine_optimization)
# install(TARGETS nexus_optimization LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})

# Mensagens de status
message(STATUS "Bindings configurados:")
message(STATUS "  - Core: nexus_core")
message(STATUS "  - Strategies: (FASE 3)")
message(STATUS "  - Execution: (FASE 4)")
message(STATUS "  - Analytics: (FASE 4)")
message(STATUS "  - Optimization: (FASE 4)")
