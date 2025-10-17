FROM ubuntu:22.04 AS cpp-builder

# Metadados
LABEL maintainer="Nexus Engine Team"
LABEL description="Nexus Trading Engine - C++ Core Builder"
LABEL version="1.0"

# Prevenir prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências de build C++
# Aprendi que Ubuntu 22.04 tem as versões mais recentes de GCC e CMake
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    cmake \
    ninja-build \
    git \
    # C++ compilers
    g++-12 \
    gcc-12 \
    # C++ libraries
    libstdc++-12-dev \
    # Testing frameworks
    libgtest-dev \
    libgmock-dev \
    # Benchmarking
    libbenchmark-dev \
    # SQLite
    libsqlite3-dev \
    # Threading
    libtbb-dev \
    # Limpeza
    && rm -rf /var/lib/apt/lists/*

# Configurar GCC 12 como padrão
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100

# Criar diretório de build
WORKDIR /build

# Copiar código C++
COPY backend/cpp/ ./backend/cpp/
COPY CMakeLists.txt ./

# Build com otimizações máximas
# Implementei flags de otimização agressivas para máxima performance
# -O3: Otimização máxima
# -march=native: Otimizar para CPU do host (trocar por -march=x86-64-v3 para portabilidade)
# -mtune=native: Tuning específico da CPU
# -flto: Link Time Optimization
# -DNDEBUG: Desabilitar assertions
RUN mkdir -p build && cd build && \
    cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=g++-12 \
    -DCMAKE_C_COMPILER=gcc-12 \
    -DCMAKE_CXX_STANDARD=20 \
    -DCMAKE_CXX_FLAGS="-O3 -march=native -mtune=native -flto -DNDEBUG" \
    -DBUILD_TESTING=ON \
    -DBUILD_BENCHMARKS=ON \
    .. && \
    ninja

# Rodar testes para validar build
# Decidi incluir testes no build para garantir qualidade
RUN cd build && ctest --output-on-failure

# Instalar binários e libraries
RUN cd build && ninja install

# ============================================
# Stage 2: Runtime - Imagem mínima com binários
# ============================================
FROM ubuntu:22.04 AS runtime

# Metadados
LABEL maintainer="Nexus Engine Team"
LABEL description="Nexus Trading Engine - C++ Core Runtime"
LABEL version="1.0"

# Instalar apenas dependências de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    libsqlite3-0 \
    libtbb12 \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r nexus && useradd -r -g nexus -u 1000 nexus

# Copiar binários compilados
COPY --from=cpp-builder /usr/local/lib/libnexus* /usr/local/lib/
COPY --from=cpp-builder /usr/local/include/nexus /usr/local/include/nexus
COPY --from=cpp-builder /usr/local/bin/nexus* /usr/local/bin/

# Atualizar ldconfig
RUN ldconfig

# Criar diretórios de dados
RUN mkdir -p /app/data && chown -R nexus:nexus /app

WORKDIR /app

# Trocar para usuário não-root
USER nexus

# Comando padrão: mostrar versão e informações
CMD ["sh", "-c", "echo 'Nexus C++ Engine'; echo 'Build: Release'; echo 'Optimization: O3 + LTO'; ls -lh /usr/local/lib/libnexus*"]