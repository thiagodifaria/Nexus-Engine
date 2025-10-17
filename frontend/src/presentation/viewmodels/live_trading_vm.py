"""
Live Trading ViewModel.

Implementei ViewModel para live trading com WebSocket real-time.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
from datetime import datetime


class LiveTradingViewModel(QObject):
    """
    ViewModel para live trading.

    Implementei gerenciamento de conexão WebSocket e atualização
    de preços em tempo real.
    """

    # Signals
    connection_status_changed = pyqtSignal(bool, str)  # connected, message
    price_updated = pyqtSignal(dict)  # {symbol, price, timestamp, change}
    positions_updated = pyqtSignal(list)
    order_executed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        """Inicializo ViewModel."""
        super().__init__()
        self._is_connected = False
        self._active_strategy_id: Optional[str] = None
        self._subscribed_symbols: List[str] = []
        self._current_positions: List[Dict] = []

        # Timer para simular atualizações (WebSocket mock)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._simulate_price_update)

    def connect(self, strategy_id: str, symbols: List[str]) -> None:
        """
        Conecto ao live trading.

        Args:
            strategy_id: ID da estratégia ativa
            symbols: Lista de símbolos para monitorar
        """
        if self._is_connected:
            self.error_occurred.emit("Already connected")
            return

        try:
            # TODO: Conectar WebSocket real via Finnhub
            # Por enquanto, simulo conexão

            self._active_strategy_id = strategy_id
            self._subscribed_symbols = symbols
            self._is_connected = True

            self.connection_status_changed.emit(True, "Connected to live market")

            # Inicio timer de simulação (1s updates)
            self._update_timer.start(1000)

            # Emito posições iniciais vazias
            self.positions_updated.emit([])

        except Exception as e:
            self.error_occurred.emit(str(e))

    def disconnect(self) -> None:
        """Desconecto do live trading."""
        if not self._is_connected:
            return

        try:
            # TODO: Desconectar WebSocket real
            # Por enquanto, paro timer

            self._update_timer.stop()
            self._is_connected = False
            self._active_strategy_id = None
            self._subscribed_symbols = []
            self._current_positions = []

            self.connection_status_changed.emit(False, "Disconnected")

        except Exception as e:
            self.error_occurred.emit(str(e))

    def place_order(
        self,
        symbol: str,
        order_type: str,  # BUY, SELL
        quantity: float,
    ) -> None:
        """
        Faço ordem manual.

        Args:
            symbol: Símbolo
            order_type: Tipo da ordem (BUY/SELL)
            quantity: Quantidade
        """
        if not self._is_connected:
            self.error_occurred.emit("Not connected")
            return

        try:
            # TODO: Enviar ordem via backend
            # Por enquanto, simulo execução

            order = {
                "symbol": symbol,
                "type": order_type,
                "quantity": quantity,
                "price": self._get_simulated_price(symbol),
                "timestamp": datetime.now().isoformat(),
                "status": "FILLED",
            }

            self.order_executed.emit(order)

            # Atualizo posições
            self._update_positions_after_order(order)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def get_current_positions(self) -> List[Dict]:
        """
        Retorno posições atuais.

        Returns:
            Lista de posições
        """
        return self._current_positions.copy()

    def _simulate_price_update(self) -> None:
        """Simulo atualização de preço (mock WebSocket)."""
        import random

        for symbol in self._subscribed_symbols:
            price = self._get_simulated_price(symbol)
            change = random.uniform(-0.5, 0.5)

            price_data = {
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "change": change,
                "change_percent": (change / price) * 100,
            }

            self.price_updated.emit(price_data)

    def _get_simulated_price(self, symbol: str) -> float:
        """
        Retorno preço simulado.

        Args:
            symbol: Símbolo

        Returns:
            Preço simulado
        """
        import random

        base_prices = {
            "AAPL": 175.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "TSLA": 240.0,
            "SPY": 450.0,
        }

        base = base_prices.get(symbol, 100.0)
        return round(base + random.uniform(-2.0, 2.0), 2)

    def _update_positions_after_order(self, order: Dict) -> None:
        """
        Atualizo posições após ordem.

        Args:
            order: Dict com ordem executada
        """
        symbol = order["symbol"]
        quantity = order["quantity"]
        price = order["price"]

        # Busco posição existente
        existing_position = next(
            (p for p in self._current_positions if p["symbol"] == symbol),
            None
        )

        if order["type"] == "BUY":
            if existing_position:
                # Atualizo posição existente
                total_value = (existing_position["quantity"] * existing_position["avg_price"]) + (quantity * price)
                total_quantity = existing_position["quantity"] + quantity
                existing_position["quantity"] = total_quantity
                existing_position["avg_price"] = total_value / total_quantity
            else:
                # Crio nova posição
                self._current_positions.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": price,
                    "current_price": price,
                    "pnl": 0.0,
                    "pnl_percent": 0.0,
                })

        elif order["type"] == "SELL":
            if existing_position:
                existing_position["quantity"] -= quantity
                if existing_position["quantity"] <= 0:
                    self._current_positions.remove(existing_position)

        self.positions_updated.emit(self._current_positions)

    def update_position_prices(self, price_data: Dict) -> None:
        """
        Atualizo preços das posições.

        Args:
            price_data: Dict com dados de preço
        """
        symbol = price_data["symbol"]
        current_price = price_data["price"]

        for position in self._current_positions:
            if position["symbol"] == symbol:
                position["current_price"] = current_price
                pnl = (current_price - position["avg_price"]) * position["quantity"]
                position["pnl"] = pnl
                position["pnl_percent"] = ((current_price / position["avg_price"]) - 1) * 100

        self.positions_updated.emit(self._current_positions)

    @property
    def is_connected(self) -> bool:
        """Retorno status de conexão."""
        return self._is_connected