# main.py
"""
Punto de entrada de la aplicación de simulación.
Inicializa el entorno Qt, la configuración por defecto y arranca la ventana principal.
"""

import sys
from PySide6 import QtWidgets

from config import SimulationConfig
from main_window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    config = SimulationConfig()

    window = MainWindow(config=config)
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())
