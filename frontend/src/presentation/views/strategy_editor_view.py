"""
Strategy Editor View.

Implementei view para criar e editar estratégias com validação.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QGroupBox, QFormLayout, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from presentation.viewmodels.strategy_vm import StrategyViewModel


class StrategyEditorView(QWidget):
    """
    View de editor de estratégias.

    Implementei interface para criar, editar e deletar estratégias
    com editores de parâmetros dinâmicos.
    """

    def __init__(self):
        """Inicializo view."""
        super().__init__()
        self.viewmodel = StrategyViewModel()
        self._current_strategy_id: str | None = None
        self._parameter_editors: dict = {}

        self._init_ui()
        self._connect_signals()

        # Carrego estratégias iniciais
        self.viewmodel.load_strategies()

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QHBoxLayout()

        # Left panel - Lista de estratégias
        left_panel = self._create_strategies_list()
        main_layout.addWidget(left_panel, stretch=1)

        # Right panel - Editor
        right_panel = self._create_editor_panel()
        main_layout.addWidget(right_panel, stretch=2)

        self.setLayout(main_layout)

    def _create_strategies_list(self) -> QGroupBox:
        """
        Crio painel com lista de estratégias.

        Returns:
            GroupBox com lista
        """
        group = QGroupBox("Strategies")
        layout = QVBoxLayout()

        # Tabela de estratégias
        self.strategies_table = QTableWidget()
        self.strategies_table.setColumnCount(3)
        self.strategies_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status"
        ])
        self.strategies_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.strategies_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.strategies_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.strategies_table.itemSelectionChanged.connect(
            self._on_strategy_selected
        )

        layout.addWidget(self.strategies_table)

        # Botões
        buttons_layout = QHBoxLayout()

        new_button = QPushButton("New Strategy")
        new_button.clicked.connect(self._on_new_clicked)
        buttons_layout.addWidget(new_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._on_delete_clicked)
        buttons_layout.addWidget(delete_button)

        layout.addLayout(buttons_layout)

        group.setLayout(layout)
        return group

    def _create_editor_panel(self) -> QGroupBox:
        """
        Crio painel de edição.

        Returns:
            GroupBox com editor
        """
        group = QGroupBox("Strategy Editor")
        layout = QVBoxLayout()

        # Form de edição
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Strategy name")
        form_layout.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("Type:", self.type_combo)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Strategy description (optional)")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)

        layout.addLayout(form_layout)

        # Parameters section
        self.parameters_group = QGroupBox("Parameters")
        self.parameters_layout = QFormLayout()
        self.parameters_group.setLayout(self.parameters_layout)
        layout.addWidget(self.parameters_group)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Strategy")
        self.save_button.clicked.connect(self._on_save_clicked)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Conecto signals do ViewModel."""
        self.viewmodel.strategies_loaded.connect(self._on_strategies_loaded)
        self.viewmodel.strategy_created.connect(self._on_strategy_saved)
        self.viewmodel.strategy_updated.connect(self._on_strategy_saved)
        self.viewmodel.strategy_deleted.connect(self._on_strategy_deleted)
        self.viewmodel.validation_failed.connect(self._on_validation_failed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def _on_strategies_loaded(self, strategies: list) -> None:
        """
        Handler quando estratégias são carregadas.

        Args:
            strategies: Lista de estratégias
        """
        self.strategies_table.setRowCount(len(strategies))

        for row, strategy in enumerate(strategies):
            self.strategies_table.setItem(
                row, 0, QTableWidgetItem(strategy["name"])
            )
            self.strategies_table.setItem(
                row, 1, QTableWidgetItem(strategy["type"])
            )

            status_item = QTableWidgetItem(strategy["status"])
            if strategy["status"] == "active":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.strategies_table.setItem(row, 2, status_item)

        # Populo combo de tipos
        if self.type_combo.count() == 0:
            types = self.viewmodel.get_available_strategy_types()
            for type_info in types:
                self.type_combo.addItem(
                    f"{type_info['type']} - {type_info['name']}",
                    type_info
                )

    def _on_strategy_selected(self) -> None:
        """Handler quando estratégia é selecionada."""
        selected_rows = self.strategies_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        strategy_name = self.strategies_table.item(row, 0).text()

        # Busco estratégia completa
        strategies = self.viewmodel._strategies_cache
        strategy = next(
            (s for s in strategies if s["name"] == strategy_name),
            None
        )

        if strategy:
            self._load_strategy_to_editor(strategy)

    def _load_strategy_to_editor(self, strategy: dict) -> None:
        """
        Carrego estratégia no editor.

        Args:
            strategy: Dict com dados da estratégia
        """
        self._current_strategy_id = strategy["id"]

        self.name_input.setText(strategy["name"])
        self.description_input.setPlainText(strategy.get("description", ""))

        # Seleciono tipo correto
        for i in range(self.type_combo.count()):
            type_info = self.type_combo.itemData(i)
            if type_info["type"] == strategy["type"]:
                self.type_combo.setCurrentIndex(i)
                break

        # Carrego parâmetros
        self._create_parameter_editors(strategy["type"], strategy["parameters"])

    def _on_type_changed(self, text: str) -> None:
        """
        Handler quando tipo é alterado.

        Args:
            text: Texto do combo
        """
        type_info = self.type_combo.currentData()
        if type_info:
            self._create_parameter_editors(
                type_info["type"],
                type_info["parameters"]
            )

    def _create_parameter_editors(
        self, strategy_type: str, parameters: dict
    ) -> None:
        """
        Crio editores de parâmetros dinamicamente.

        Args:
            strategy_type: Tipo da estratégia
            parameters: Dict com parâmetros
        """
        # Limpo editores existentes
        while self.parameters_layout.count():
            child = self.parameters_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._parameter_editors = {}

        # Crio novos editores
        for param_name, param_value in parameters.items():
            editor = QDoubleSpinBox()
            editor.setDecimals(2)
            editor.setMinimum(0.01)
            editor.setMaximum(10000.0)
            editor.setValue(float(param_value))

            self._parameter_editors[param_name] = editor
            self.parameters_layout.addRow(f"{param_name}:", editor)

    def _on_new_clicked(self) -> None:
        """Handler do botão New."""
        self._current_strategy_id = None
        self.name_input.clear()
        self.description_input.clear()
        self.type_combo.setCurrentIndex(0)

        self.strategies_table.clearSelection()

    def _on_save_clicked(self) -> None:
        """Handler do botão Save."""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()

        type_info = self.type_combo.currentData()
        if not type_info:
            return

        strategy_type = type_info["type"]

        # Coleto parâmetros dos editores
        parameters = {}
        for param_name, editor in self._parameter_editors.items():
            parameters[param_name] = editor.value()

        if self._current_strategy_id:
            # Update
            self.viewmodel.update_strategy(
                self._current_strategy_id,
                name=name,
                parameters=parameters,
                description=description,
            )
        else:
            # Create
            self.viewmodel.create_strategy(
                name=name,
                strategy_type=strategy_type,
                parameters=parameters,
                description=description,
            )

    def _on_cancel_clicked(self) -> None:
        """Handler do botão Cancel."""
        self._on_new_clicked()

    def _on_delete_clicked(self) -> None:
        """Handler do botão Delete."""
        if not self._current_strategy_id:
            QMessageBox.warning(
                self, "No Selection", "Please select a strategy to delete"
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this strategy?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.delete_strategy(self._current_strategy_id)

    def _on_strategy_saved(self, strategy: dict) -> None:
        """
        Handler quando estratégia é salva.

        Args:
            strategy: Dict com estratégia
        """
        QMessageBox.information(
            self, "Success", f"Strategy '{strategy['name']}' saved successfully"
        )
        self.viewmodel.load_strategies()
        self._on_new_clicked()

    def _on_strategy_deleted(self, strategy_id: str) -> None:
        """
        Handler quando estratégia é deletada.

        Args:
            strategy_id: ID da estratégia
        """
        QMessageBox.information(
            self, "Success", "Strategy deleted successfully"
        )
        self.viewmodel.load_strategies()
        self._on_new_clicked()

    def _on_validation_failed(self, error: str) -> None:
        """
        Handler quando validação falha.

        Args:
            error: Mensagem de erro
        """
        QMessageBox.warning(self, "Validation Error", error)

    def _on_error(self, error: str) -> None:
        """
        Handler quando erro ocorre.

        Args:
            error: Mensagem de erro
        """
        QMessageBox.critical(self, "Error", f"An error occurred: {error}")
