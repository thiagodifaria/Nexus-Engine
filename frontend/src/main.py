"""
Entry point da aplicação PyQt6.

Implementei main entry point seguindo boas práticas do Qt.
Decidi usar QApplication padrão com configurações otimizadas.

Referências:
- PyQt6 Application: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from presentation.views.main_window import MainWindow


def main() -> int:
    """
    Função principal da aplicação.

    Implementei inicialização do Qt e configurações globais.

    Returns:
        Exit code
    """
    # Habilito High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Crio aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus Engine")
    app.setOrganizationName("Nexus Trading")
    app.setApplicationVersion("0.7.0")

    # Crio e mostro janela principal
    window = MainWindow()
    window.show()

    # Executo event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())