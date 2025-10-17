"""
Main Window da aplicação PyQt6.

Implementei janela principal seguindo MVVM pattern.
Decidi usar QTabWidget para organizar diferentes funcionalidades.

Referências:
- PyQt6 Main Window: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
    QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

# Importo todas as views
from presentation.views.dashboard_view import DashboardView
from presentation.views.backtest_view import BacktestView
from presentation.views.strategy_editor_view import StrategyEditorView
from presentation.views.live_trading_view import LiveTradingView
from presentation.views.observability_view import ObservabilityView


class MainWindow(QMainWindow):
    """
    Janela principal do Nexus Engine.

    Implementei com menu bar, tab widget e status bar.
    Uso MVVM separando lógica de apresentação.
    """

    def __init__(self):
        """Inicializo main window."""
        super().__init__()

        self.setWindowTitle("Nexus Engine - Trading Platform")
        self.setGeometry(100, 100, 1400, 900)

        # Crio interface
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

        # Aplico dark theme
        self._apply_dark_theme()

    def _create_menu_bar(self) -> None:
        """
        Crio menu bar.

        Implementei menus principais: File, Tools, Help.
        """
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_strategy_action = QAction("&New Strategy", self)
        new_strategy_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_strategy_action)

        open_backtest_action = QAction("&Open Backtest", self)
        open_backtest_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_backtest_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        help_menu.addAction(about_action)

        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut("F1")
        help_menu.addAction(docs_action)

    def _create_central_widget(self) -> None:
        """
        Crio widget central com tabs.

        Implementei tab widget para organizar funcionalidades:
        - Dashboard: Overview e métricas
        - Backtests: Executar e visualizar backtests
        - Strategies: Gerenciar estratégias
        - Live Trading: Trading em tempo real
        - Observability: Métricas Prometheus
        """
        # Tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Crio views
        self.dashboard_view = DashboardView()
        self.backtest_view = BacktestView()
        self.strategy_editor_view = StrategyEditorView()
        self.live_trading_view = LiveTradingView()
        self.observability_view = ObservabilityView()

        # Adiciono tabs com views reais
        self.tab_widget.addTab(self.dashboard_view, "Dashboard")
        self.tab_widget.addTab(self.backtest_view, "Backtests")
        self.tab_widget.addTab(self.strategy_editor_view, "Strategies")
        self.tab_widget.addTab(self.live_trading_view, "Live Trading")
        self.tab_widget.addTab(self.observability_view, "Observability")

    def _create_status_bar(self) -> None:
        """
        Crio status bar.

        Implementei status bar com informações úteis.
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Connection status (direita)
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.connection_label)

    def _apply_dark_theme(self) -> None:
        """
        Aplico dark theme.

        Implementei tema escuro profissional para trading.
        """
        dark_stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
        }
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
            background: #252526;
        }
        QTabBar::tab {
            background: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #007acc;
            color: white;
        }
        QTabBar::tab:hover {
            background: #3e3e42;
        }
        QMenuBar {
            background-color: #2d2d30;
            color: #cccccc;
        }
        QMenuBar::item:selected {
            background: #007acc;
        }
        QMenu {
            background-color: #252526;
            color: #cccccc;
        }
        QMenu::item:selected {
            background-color: #007acc;
        }
        QStatusBar {
            background: #007acc;
            color: white;
        }
        QLabel {
            color: #cccccc;
        }
        """
        self.setStyleSheet(dark_stylesheet)
