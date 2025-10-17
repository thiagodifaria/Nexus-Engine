"""
Strategy ViewModel.

Implementei ViewModel para gerenciamento de estratégias seguindo MVVM.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional


class StrategyViewModel(QObject):
    """
    ViewModel para estratégias.

    Implementei CRUD completo para estratégias com validação.
    """

    # Signals
    strategies_loaded = pyqtSignal(list)
    strategy_created = pyqtSignal(dict)
    strategy_updated = pyqtSignal(dict)
    strategy_deleted = pyqtSignal(str)
    validation_failed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        """Inicializo ViewModel."""
        super().__init__()
        self._strategies_cache: List[Dict] = []

    def load_strategies(self) -> None:
        """
        Carrego todas as estratégias.

        Implementei carregamento com cache local.
        """
        try:
            # TODO: Chamar backend via BackendClient
            # Por enquanto, simulo dados

            strategies = [
                {
                    "id": "str-001",
                    "name": "SMA Crossover",
                    "type": "SMA",
                    "status": "active",
                    "parameters": {
                        "fast_period": 10,
                        "slow_period": 50,
                    },
                    "description": "Simple Moving Average crossover strategy",
                    "created_at": "2025-09-01",
                },
                {
                    "id": "str-002",
                    "name": "RSI Mean Reversion",
                    "type": "RSI",
                    "status": "active",
                    "parameters": {
                        "period": 14,
                        "oversold": 30,
                        "overbought": 70,
                    },
                    "description": "RSI-based mean reversion strategy",
                    "created_at": "2025-09-15",
                },
                {
                    "id": "str-003",
                    "name": "MACD Momentum",
                    "type": "MACD",
                    "status": "paused",
                    "parameters": {
                        "fast": 12,
                        "slow": 26,
                        "signal": 9,
                    },
                    "description": "MACD momentum trading strategy",
                    "created_at": "2025-10-01",
                },
            ]

            self._strategies_cache = strategies
            self.strategies_loaded.emit(strategies)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def create_strategy(
        self,
        name: str,
        strategy_type: str,
        parameters: Dict[str, float],
        description: str = "",
    ) -> None:
        """
        Crio nova estratégia.

        Args:
            name: Nome da estratégia
            strategy_type: Tipo (SMA, RSI, MACD)
            parameters: Parâmetros da estratégia
            description: Descrição opcional
        """
        # Valido inputs
        validation_error = self._validate_strategy_inputs(
            name, strategy_type, parameters
        )
        if validation_error:
            self.validation_failed.emit(validation_error)
            return

        try:
            # TODO: Chamar backend via BackendClient
            # Por enquanto, simulo criação

            new_strategy = {
                "id": f"str-{len(self._strategies_cache) + 1:03d}",
                "name": name,
                "type": strategy_type,
                "status": "active",
                "parameters": parameters,
                "description": description,
                "created_at": "2025-10-16",
            }

            self._strategies_cache.append(new_strategy)
            self.strategy_created.emit(new_strategy)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_strategy(
        self,
        strategy_id: str,
        name: Optional[str] = None,
        parameters: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """
        Atualizo estratégia existente.

        Args:
            strategy_id: ID da estratégia
            name: Novo nome (opcional)
            parameters: Novos parâmetros (opcional)
            description: Nova descrição (opcional)
            status: Novo status (opcional)
        """
        try:
            # TODO: Chamar backend via BackendClient
            # Por enquanto, atualizo cache local

            strategy = self._find_strategy_by_id(strategy_id)
            if not strategy:
                self.error_occurred.emit(f"Strategy {strategy_id} not found")
                return

            if name:
                strategy["name"] = name
            if parameters:
                strategy["parameters"] = parameters
            if description is not None:
                strategy["description"] = description
            if status:
                strategy["status"] = status

            self.strategy_updated.emit(strategy)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def delete_strategy(self, strategy_id: str) -> None:
        """
        Deleto estratégia.

        Args:
            strategy_id: ID da estratégia
        """
        try:
            # TODO: Chamar backend via BackendClient
            # Por enquanto, removo do cache

            strategy = self._find_strategy_by_id(strategy_id)
            if not strategy:
                self.error_occurred.emit(f"Strategy {strategy_id} not found")
                return

            self._strategies_cache.remove(strategy)
            self.strategy_deleted.emit(strategy_id)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def get_strategy_by_id(self, strategy_id: str) -> Optional[Dict]:
        """
        Busco estratégia por ID.

        Args:
            strategy_id: ID da estratégia

        Returns:
            Dict com estratégia ou None
        """
        return self._find_strategy_by_id(strategy_id)

    def get_available_strategy_types(self) -> List[Dict[str, str]]:
        """
        Retorno tipos de estratégia disponíveis.

        Returns:
            Lista de tipos com templates de parâmetros
        """
        return [
            {
                "type": "SMA",
                "name": "Simple Moving Average",
                "parameters": {
                    "fast_period": 10,
                    "slow_period": 50,
                },
            },
            {
                "type": "RSI",
                "name": "Relative Strength Index",
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70,
                },
            },
            {
                "type": "MACD",
                "name": "MACD",
                "parameters": {
                    "fast": 12,
                    "slow": 26,
                    "signal": 9,
                },
            },
        ]

    def _validate_strategy_inputs(
        self, name: str, strategy_type: str, parameters: Dict[str, float]
    ) -> Optional[str]:
        """
        Valido inputs de estratégia.

        Args:
            name: Nome da estratégia
            strategy_type: Tipo da estratégia
            parameters: Parâmetros

        Returns:
            Mensagem de erro ou None se válido
        """
        if not name or len(name.strip()) == 0:
            return "Strategy name cannot be empty"

        if len(name) > 255:
            return "Strategy name too long (max 255 characters)"

        valid_types = ["SMA", "RSI", "MACD"]
        if strategy_type not in valid_types:
            return f"Invalid strategy type. Must be one of: {', '.join(valid_types)}"

        if not parameters:
            return "Parameters cannot be empty"

        # Valido parâmetros específicos por tipo
        if strategy_type == "SMA":
            if "fast_period" not in parameters or "slow_period" not in parameters:
                return "SMA requires fast_period and slow_period"
            if parameters["fast_period"] >= parameters["slow_period"]:
                return "fast_period must be less than slow_period"

        elif strategy_type == "RSI":
            if "period" not in parameters:
                return "RSI requires period"
            if "oversold" not in parameters or "overbought" not in parameters:
                return "RSI requires oversold and overbought thresholds"
            if parameters["oversold"] >= parameters["overbought"]:
                return "oversold must be less than overbought"

        elif strategy_type == "MACD":
            if "fast" not in parameters or "slow" not in parameters or "signal" not in parameters:
                return "MACD requires fast, slow, and signal periods"
            if parameters["fast"] >= parameters["slow"]:
                return "fast period must be less than slow period"

        return None

    def _find_strategy_by_id(self, strategy_id: str) -> Optional[Dict]:
        """
        Busco estratégia no cache.

        Args:
            strategy_id: ID da estratégia

        Returns:
            Dict com estratégia ou None
        """
        for strategy in self._strategies_cache:
            if strategy["id"] == strategy_id:
                return strategy
        return None
