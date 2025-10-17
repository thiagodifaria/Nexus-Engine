"""
Finnhub API Adapter para dados real-time.

Implementei adapter para WebSocket real-time da Finnhub.
Decidi usar WebSocket para latência mínima em live trading.

Referências:
- Finnhub API: https://finnhub.io/docs/api
- WebSocket Protocol: https://websocket-client.readthedocs.io/
"""

import json
import time
from typing import Callable, List, Optional
from datetime import datetime

import websocket
from finnhub import Client as FinnhubClient

from config.settings import get_settings
from domain.value_objects.symbol import Symbol
from domain.repositories.market_data_repository import MarketDataBar, MarketDataAPIError


class FinnhubAdapter:
    """
    Adapter para Finnhub API (WebSocket real-time).

    Implementei WebSocket connection para dados real-time de trading.
    Uso callbacks para processar dados assincronamente.

    Referência: https://finnhub.io/docs/api/websocket-trades
    """

    def __init__(self):
        """Inicializo adapter Finnhub."""
        settings = get_settings()
        self._api_key = settings.finnhub_api_key

        if not self._api_key:
            raise ValueError("FINNHUB_API_KEY not configured in settings")

        # REST client para dados históricos
        self._rest_client = FinnhubClient(api_key=self._api_key)

        # WebSocket para real-time
        self._ws: Optional[websocket.WebSocketApp] = None
        self._is_connected = False
        self._subscribed_symbols: List[str] = []

    def get_historical_daily(
        self, symbol: Symbol, start_date: datetime, end_date: datetime
    ) -> List[MarketDataBar]:
        """
        Busco dados históricos diários via REST API.

        Implementei usando candles endpoint da Finnhub.

        Args:
            symbol: Símbolo do ativo
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de barras OHLCV

        Raises:
            MarketDataAPIError: Se API falhar
        """
        try:
            # Converto datas para timestamps Unix
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())

            # Busco candles (resolução diária = 'D')
            response = self._rest_client.stock_candles(
                symbol.value, "D", start_ts, end_ts
            )

            if response["s"] != "ok":
                raise MarketDataAPIError(
                    "Finnhub", f"API returned status: {response['s']}"
                )

            # Converto para MarketDataBar
            bars = []
            for i in range(len(response["t"])):
                bars.append(
                    MarketDataBar(
                        symbol=symbol.value,
                        timestamp=datetime.fromtimestamp(response["t"][i]),
                        open=response["o"][i],
                        high=response["h"][i],
                        low=response["l"][i],
                        close=response["c"][i],
                        volume=response["v"][i],
                    )
                )

            return bars

        except Exception as e:
            raise MarketDataAPIError("Finnhub", f"Failed to fetch candles: {e}")

    def connect_websocket(
        self, on_trade_callback: Callable[[dict], None]
    ) -> None:
        """
        Conecto ao WebSocket da Finnhub para dados real-time.

        Implementei com callbacks para processar trades assincronamente.

        Args:
            on_trade_callback: Função chamada para cada trade recebido

        Raises:
            MarketDataAPIError: Se conexão falhar
        """
        try:
            ws_url = f"wss://ws.finnhub.io?token={self._api_key}"

            def on_message(ws, message):
                """Callback quando mensagem é recebida."""
                data = json.loads(message)
                if data["type"] == "trade":
                    for trade in data["data"]:
                        on_trade_callback(trade)

            def on_error(ws, error):
                """Callback em caso de erro."""
                print(f"WebSocket error: {error}")
                self._is_connected = False

            def on_close(ws, close_status_code, close_msg):
                """Callback quando conexão fecha."""
                print(f"WebSocket closed: {close_status_code} - {close_msg}")
                self._is_connected = False

            def on_open(ws):
                """Callback quando conexão abre."""
                print("Finnhub WebSocket connected")
                self._is_connected = True

            self._ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
            )

        except Exception as e:
            raise MarketDataAPIError("Finnhub", f"Failed to connect WebSocket: {e}")

    def subscribe(self, symbol: Symbol) -> None:
        """
        Inscrevo em trades real-time de um símbolo.

        Args:
            symbol: Símbolo para monitorar

        Raises:
            MarketDataAPIError: Se inscrição falhar
        """
        if not self._is_connected:
            raise MarketDataAPIError("Finnhub", "WebSocket not connected")

        try:
            subscribe_msg = json.dumps({"type": "subscribe", "symbol": symbol.value})
            self._ws.send(subscribe_msg)
            self._subscribed_symbols.append(symbol.value)
            print(f"Subscribed to {symbol.value}")

        except Exception as e:
            raise MarketDataAPIError("Finnhub", f"Failed to subscribe: {e}")

    def unsubscribe(self, symbol: Symbol) -> None:
        """
        Cancelo inscrição de um símbolo.

        Args:
            symbol: Símbolo para parar de monitorar
        """
        if not self._is_connected:
            return

        try:
            unsubscribe_msg = json.dumps({"type": "unsubscribe", "symbol": symbol.value})
            self._ws.send(unsubscribe_msg)
            if symbol.value in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol.value)
            print(f"Unsubscribed from {symbol.value}")

        except Exception as e:
            print(f"Failed to unsubscribe: {e}")

    def disconnect(self) -> None:
        """Desconecto WebSocket."""
        if self._ws:
            self._ws.close()
            self._is_connected = False

    def is_connected(self) -> bool:
        """Verifico se WebSocket está conectado."""
        return self._is_connected