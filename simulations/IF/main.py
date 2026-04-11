# main.py
# Este es el punto de entrada de la aplicación. Aquí se crea la instancia de 
# la aplicación Qt, se carga la configuración de la simulación, se crea la 
# ventana principal y se inicia el bucle de eventos de la aplicación. Es un 
# archivo muy simple que solo se encarga de inicializar todo lo necesario para
# que la aplicación funcione correctamente.

import sys # para el manejo de argumentos y la salida del programa
from PySide6 import QtWidgets # pyside es un binding de Qt para Python, QtWidgets contiene clases para crear interfaces gráficas

from config import SimulationConfig # uviene de config.py, contiene la configuración de la simulación
from main_window import MainWindow # viene de main_window.py, contiene la clase MainWindow que define la ventana principal de la aplicación


if __name__ == "__main__": 
    app = QtWidgets.QApplication(sys.argv) # crea una instancia de la aplicación Qt, necesaria para cualquier aplicación gráfica con Qt
    config = SimulationConfig() # crea una instancia de la configuración de la simulación

    window = MainWindow(config=config) # crea una instancia de la ventana principal, pasando la configuración de la simulación como argumento
    window.resize(1200, 800) 
    window.show() 

    sys.exit(app.exec()) # asegura que la aplicación se cierre correctamente cuando el usuario cierre la ventana, ejecutando el bucle de eventos de la aplicación y esperando a que termine antes de salir del programa
