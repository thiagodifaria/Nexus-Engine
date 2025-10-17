"""
Prometheus Client - client HTTP para query de métricas Prometheus.

Implementei client para consultar Prometheus API.
Decidi usar requests para HTTP simples.

Referências:
- Prometheus HTTP API: https://prometheus.io/docs/prometheus/latest/querying/api/
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class PrometheusClient:
    """
    Cliente para consultar Prometheus.

    Implementei queries instant e range queries.
    """

    def __init__(self, base_url: str = "http://localhost:9090"):
        """
        Construtor.

        Args:
            base_url: URL base do Prometheus
        """
        self.base_url = base_url.rstrip("/")
        self._timeout = 10

    def query_instant(self, query: str) -> Optional[Dict]:
        """
        Executo query instantânea.

        Args:
            query: PromQL query

        Returns:
            Resultado da query ou None em caso de erro
        """
        try:
            url = f"{self.base_url}/api/v1/query"
            params = {"query": query}

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                return data.get("data")

            return None

        except Exception as e:
            print(f"Erro ao consultar Prometheus: {e}")
            return None

    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s",
    ) -> Optional[Dict]:
        """
        Executo range query.

        Args:
            query: PromQL query
            start: Data/hora inicial
            end: Data/hora final
            step: Intervalo de amostragem (ex: "15s", "1m")

        Returns:
            Resultado da query ou None em caso de erro
        """
        try:
            url = f"{self.base_url}/api/v1/query_range"
            params = {
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
            }

            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                return data.get("data")

            return None

        except Exception as e:
            print(f"Erro ao consultar Prometheus: {e}")
            return None

    def get_metric_current_value(self, metric_name: str) -> Optional[float]:
        """
        Busco valor atual de uma métrica.

        Args:
            metric_name: Nome da métrica

        Returns:
            Valor atual ou None
        """
        result = self.query_instant(metric_name)

        if result and result.get("result"):
            values = result["result"]
            if values:
                return float(values[0]["value"][1])

        return None

    def get_metric_history(
        self,
        metric_name: str,
        duration_minutes: int = 60,
        step: str = "15s",
    ) -> List[tuple]:
        """
        Busco histórico de uma métrica.

        Args:
            metric_name: Nome da métrica
            duration_minutes: Duração em minutos (padrão: 60)
            step: Intervalo de amostragem

        Returns:
            Lista de tuplas (timestamp, valor)
        """
        end = datetime.now()
        start = end - timedelta(minutes=duration_minutes)

        result = self.query_range(metric_name, start, end, step)

        if result and result.get("result"):
            values = result["result"]
            if values:
                points = values[0]["values"]
                return [(float(ts), float(val)) for ts, val in points]

        return []

    def get_all_metrics(self) -> List[str]:
        """
        Listo todas as métricas disponíveis.

        Returns:
            Lista de nomes de métricas
        """
        try:
            url = f"{self.base_url}/api/v1/label/__name__/values"

            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                return data.get("data", [])

            return []

        except Exception as e:
            print(f"Erro ao listar métricas: {e}")
            return []

    def health_check(self) -> bool:
        """
        Verifico saúde do Prometheus.

        Returns:
            True se Prometheus está saudável
        """
        try:
            url = f"{self.base_url}/-/healthy"
            response = requests.get(url, timeout=self._timeout)
            return response.status_code == 200

        except Exception:
            return False