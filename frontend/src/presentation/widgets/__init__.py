"""
Widgets package.

Implementei widgets reutilizáveis para a interface.
"""

from presentation.widgets.charts.candlestick_chart import CandlestickChart
from presentation.widgets.charts.equity_curve_chart import EquityCurveChart
from presentation.widgets.charts.performance_metrics_widget import PerformanceMetricsWidget
from presentation.widgets.charts.live_metrics_dashboard import LiveMetricsDashboard

__all__ = [
    "CandlestickChart",
    "EquityCurveChart",
    "PerformanceMetricsWidget",
    "LiveMetricsDashboard",
]