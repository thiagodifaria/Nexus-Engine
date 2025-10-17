"""
Chart Widgets - Gráficos e visualizações.

Implementei widgets de charts para visualização de dados financeiros.
"""

from presentation.widgets.charts.equity_curve_chart import EquityCurveChart
from presentation.widgets.charts.candlestick_chart import CandlestickChart
from presentation.widgets.charts.performance_metrics_widget import PerformanceMetricsWidget
from presentation.widgets.charts.live_metrics_dashboard import LiveMetricsDashboard

__all__ = [
    "EquityCurveChart",
    "CandlestickChart",
    "PerformanceMetricsWidget",
    "LiveMetricsDashboard",
]
