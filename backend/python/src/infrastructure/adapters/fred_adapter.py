"""
FRED (Federal Reserve Economic Data) Adapter.

Implementei adapter para FRED API - dados macroeconômicos.
Decidi usar para contexto econômico em estratégias de trading.

Referências:
- FRED API: https://fred.stlouisfed.org/docs/api/fred/
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
from infrastructure.telemetry.loki_logger import LokiLogger


class FredAdapter:
    """
    Adapter para FRED API.

    Implementei acesso a dados macroeconômicos do Federal Reserve.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Construtor.

        Args:
            api_key: API key do FRED
        """
        from config.settings import Settings

        settings = Settings()
        self.api_key = api_key or settings.fred_api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self._logger = LokiLogger()
        self._timeout = 30

    def get_series(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco série temporal do FRED.

        Args:
            series_id: ID da série (ex: "GDP", "UNRATE", "DFF")
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)

        Returns:
            Lista de observações da série

        Raises:
            RuntimeError: Se falha na requisição
        """
        try:
            url = f"{self.base_url}/series/observations"

            params = {
                "api_key": self.api_key,
                "series_id": series_id,
                "file_type": "json",
            }

            if start_date:
                params["observation_start"] = start_date.strftime("%Y-%m-%d")

            if end_date:
                params["observation_end"] = end_date.strftime("%Y-%m-%d")

            self._logger.info(
                f"Fetching FRED series: {series_id}",
                extra={"series": series_id, "provider": "fred"},
            )

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()
            observations = data.get("observations", [])

            self._logger.info(
                f"Fetched {len(observations)} observations from FRED",
                extra={"observations": len(observations), "series": series_id},
            )

            return observations

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error fetching FRED data: {e}",
                extra={"error": str(e), "series": series_id},
            )
            raise RuntimeError(f"Failed to fetch FRED data: {e}")

    def get_series_info(self, series_id: str) -> Dict:
        """
        Busco informações sobre uma série.

        Args:
            series_id: ID da série

        Returns:
            Dict com metadados da série
        """
        try:
            url = f"{self.base_url}/series"

            params = {
                "api_key": self.api_key,
                "series_id": series_id,
                "file_type": "json",
            }

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()
            series_list = data.get("seriess", [])

            return series_list[0] if series_list else {}

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error fetching FRED series info: {e}",
                extra={"error": str(e), "series": series_id},
            )
            return {}

    def search_series(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Busco séries por query.

        Args:
            query: Termo de busca
            limit: Número máximo de resultados

        Returns:
            Lista de séries encontradas
        """
        try:
            url = f"{self.base_url}/series/search"

            params = {
                "api_key": self.api_key,
                "search_text": query,
                "file_type": "json",
                "limit": limit,
            }

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()
            series_list = data.get("seriess", [])

            return series_list

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error searching FRED: {e}",
                extra={"error": str(e), "query": query},
            )
            return []

    def get_gdp(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco dados de GDP (Gross Domestic Product).

        Atalho para série GDP.

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de observações de GDP
        """
        return self.get_series("GDP", start_date, end_date)

    def get_unemployment_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco taxa de desemprego (Unemployment Rate).

        Atalho para série UNRATE.

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de observações de desemprego
        """
        return self.get_series("UNRATE", start_date, end_date)

    def get_federal_funds_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco Federal Funds Rate.

        Atalho para série DFF (Daily) ou FEDFUNDS (Monthly).

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de observações de taxa de juros
        """
        return self.get_series("DFF", start_date, end_date)

    def get_inflation_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco taxa de inflação (CPI).

        Atalho para série CPIAUCSL.

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de observações de inflação
        """
        return self.get_series("CPIAUCSL", start_date, end_date)

    def get_popular_series(self) -> List[str]:
        """
        Retorno lista de séries populares.

        Returns:
            Lista de IDs de séries econômicas importantes
        """
        return [
            "GDP",  # Gross Domestic Product
            "UNRATE",  # Unemployment Rate
            "DFF",  # Federal Funds Rate (Daily)
            "FEDFUNDS",  # Federal Funds Rate (Monthly)
            "CPIAUCSL",  # Consumer Price Index
            "PPIACO",  # Producer Price Index
            "T10Y2Y",  # 10-Year Treasury Constant Maturity Minus 2-Year
            "DCOILWTICO",  # Crude Oil Prices: West Texas Intermediate
            "DEXCHUS",  # China / U.S. Foreign Exchange Rate
            "VIXCLS",  # VIX (CBOE Volatility Index)
        ]