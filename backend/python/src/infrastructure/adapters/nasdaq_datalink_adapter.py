"""
Nasdaq Data Link Adapter.

Implementei adapter para Nasdaq Data Link (Quandl) API.
Decidi usar para dados históricos extensos e datasets premium.

Referências:
- Nasdaq Data Link: https://data.nasdaq.com/tools/api
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
from infrastructure.telemetry.loki_logger import LokiLogger


class NasdaqDataLinkAdapter:
    """
    Adapter para Nasdaq Data Link API.

    Implementei acesso a datasets históricos de alta qualidade.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Construtor.

        Args:
            api_key: API key do Nasdaq Data Link
        """
        from config.settings import Settings

        settings = Settings()
        self.api_key = api_key or settings.nasdaq_data_link_api_key
        self.base_url = "https://data.nasdaq.com/api/v3"
        self._logger = LokiLogger()
        self._timeout = 30

    def get_dataset(
        self,
        dataset_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco dataset do Nasdaq Data Link.

        Args:
            dataset_code: Código do dataset (ex: "WIKI/AAPL")
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)

        Returns:
            Lista de dados do dataset

        Raises:
            RuntimeError: Se falha na requisição
        """
        try:
            url = f"{self.base_url}/datasets/{dataset_code}/data.json"

            params = {"api_key": self.api_key}

            if start_date:
                params["start_date"] = start_date.strftime("%Y-%m-%d")

            if end_date:
                params["end_date"] = end_date.strftime("%Y-%m-%d")

            self._logger.info(
                f"Fetching Nasdaq Data Link dataset: {dataset_code}",
                extra={"dataset": dataset_code, "provider": "nasdaq_datalink"},
            )

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            # Extraio dados e transformo em formato padrão
            dataset_data = data.get("dataset_data", {})
            column_names = dataset_data.get("column_names", [])
            data_rows = dataset_data.get("data", [])

            # Converto para lista de dicts
            result = []
            for row in data_rows:
                row_dict = dict(zip(column_names, row))
                result.append(row_dict)

            self._logger.info(
                f"Fetched {len(result)} rows from Nasdaq Data Link",
                extra={"rows": len(result), "dataset": dataset_code},
            )

            return result

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error fetching Nasdaq Data Link data: {e}",
                extra={"error": str(e), "dataset": dataset_code},
            )
            raise RuntimeError(f"Failed to fetch Nasdaq Data Link data: {e}")

    def get_tables_data(
        self,
        datatable_code: str,
        ticker: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Busco dados de tabela (Nasdaq Data Link Tables).

        Args:
            datatable_code: Código da tabela (ex: "ZACKS/FC")
            ticker: Ticker do ativo (opcional)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)

        Returns:
            Lista de dados da tabela
        """
        try:
            url = f"{self.base_url}/datatables/{datatable_code}.json"

            params = {"api_key": self.api_key}

            if ticker:
                params["ticker"] = ticker

            if start_date:
                params["date.gte"] = start_date.strftime("%Y-%m-%d")

            if end_date:
                params["date.lte"] = end_date.strftime("%Y-%m-%d")

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            # Extraio dados
            datatable = data.get("datatable", {})
            column_names = [col["name"] for col in datatable.get("columns", [])]
            data_rows = datatable.get("data", [])

            # Converto para lista de dicts
            result = []
            for row in data_rows:
                row_dict = dict(zip(column_names, row))
                result.append(row_dict)

            return result

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error fetching Nasdaq Data Link table: {e}",
                extra={"error": str(e), "datatable": datatable_code},
            )
            raise RuntimeError(f"Failed to fetch Nasdaq Data Link table: {e}")

    def search_datasets(self, query: str, per_page: int = 10) -> List[Dict]:
        """
        Busco datasets por query.

        Args:
            query: Termo de busca
            per_page: Resultados por página

        Returns:
            Lista de datasets encontrados
        """
        try:
            url = f"{self.base_url}/datasets.json"

            params = {
                "api_key": self.api_key,
                "query": query,
                "per_page": per_page,
            }

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()
            datasets = data.get("datasets", [])

            return datasets

        except requests.exceptions.RequestException as e:
            self._logger.error(
                f"Error searching Nasdaq Data Link: {e}",
                extra={"error": str(e), "query": query},
            )
            return []

    def get_supported_symbols(self) -> List[str]:
        """
        Retorno lista de símbolos suportados.

        Returns:
            Lista de símbolos (limitada)

        Note:
            Nasdaq Data Link não tem endpoint específico para isso.
            Retorno lista básica de símbolos conhecidos.
        """
        # Símbolos populares disponíveis no WIKI dataset
        return [
            "AAPL",
            "GOOGL",
            "MSFT",
            "AMZN",
            "TSLA",
            "FB",
            "NVDA",
            "JPM",
            "V",
            "JNJ",
        ]