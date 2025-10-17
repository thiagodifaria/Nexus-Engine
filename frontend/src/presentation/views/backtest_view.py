"""
Backtest View.

Implementei view de backtest com MVVM pattern.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QLineEdit,
    QProgressBar, QTextEdit
)
from PyQt6.QtCore import QDate

from presentation.viewmodels.backtest_vm import BacktestViewModel


class BacktestView(QWidget):
    """
    View de backtest.

    Implementei interface para configurar e executar backtests.
    """

    def __init__(self):
        """Inicializo view."""
        super().__init__()
        self.viewmodel = BacktestViewModel()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Crio interface."""
        layout = QVBoxLayout()

        # Strategy selector
        layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        layout.addWidget(self.strategy_combo)

        # Symbols
        layout.addWidget(QLabel("Symbols (comma-separated):"))
        self.symbols_input = QLineEdit()
        self.symbols_input.setPlaceholderText("AAPL, GOOGL, MSFT")
        layout.addWidget(self.symbols_input)

        # Date range
        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel("Start:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        dates_layout.addWidget(self.start_date)

        dates_layout.addWidget(QLabel("End:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        dates_layout.addWidget(self.end_date)
        layout.addLayout(dates_layout)

        # Run button
        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self._on_run_clicked)
        layout.addWidget(self.run_button)

        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Results
        layout.addWidget(QLabel("Results:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def _connect_signals(self) -> None:
        """Conecto signals do ViewModel."""
        self.viewmodel.backtest_completed.connect(self._on_completed)

    def _on_run_clicked(self) -> None:
        """Handler do botão Run."""
        symbols = [s.strip() for s in self.symbols_input.text().split(",")]
        self.viewmodel.start_backtest(
            strategy_id="test",
            symbols=symbols,
            start_date=self.start_date.date().toString("yyyy-MM-dd"),
            end_date=self.end_date.date().toString("yyyy-MM-dd"),
            initial_capital=10000.0,
        )

    def _on_completed(self, results: dict) -> None:
        """Handler quando backtest completa."""
        text = f"Return: {results['return']}%\n"
        text += f"Sharpe Ratio: {results['sharpe']}\n"
        text += f"Trades: {results['trades']}\n"
        self.results_text.setText(text)
