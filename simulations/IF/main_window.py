# main_window.py
# Este archivo define la clase MainWindow, que es la ventana principal de la aplicación. 
# Aquí se configuran todos los elementos de la interfaz gráfica, como botones, sliders, 
# combos, etc., y se conectan a las funciones correspondientes para manejar la interacción 
# del usuario. MainWindow también se encarga de mostrar las métricas de la simulación 
# (S, I, R) y de actualizar la vista en función de los cambios en la simulación.


from PySide6 import QtCore, QtWidgets # QtCore contiene clases para el manejo de señales, 
                                      # slots (funciones que se conectan a señales) y 
                                      # temporizadores, QtWidgets contiene clases para 
                                      # crear interfaces gráficas

from config import SimulationConfig # viene de config.py, contiene la configuración de la simulación
from grid_widget import GridWidget  # viene de grid_widget.py, contiene la clase GridWidget que define el widget principal donde se muestra la simulación y se maneja la lógica del modelo SIR para incendios forestales

# La clase MainWindow define la ventana principal de la aplicación, que incluye el widget de la simulación (GridWidget) y los controles para interactuar con ella (botones, sliders, combos, etc.). También maneja las señales emitidas por el GridWidget para actualizar la interfaz en función de los cambios en la simulación.

class MainWindow(QtWidgets.QMainWindow): # MainWindow hereda de QMainWindow, que es una clase de Qt que proporciona una ventana principal con características comunes como barra de menú, barra de herramientas y área central para mostrar contenido
    def __init__(self, config: SimulationConfig):
        super().__init__() 
        self.setWindowTitle("Propagacion IF - Motor Base") 

        self.grid_widget = GridWidget(config=config)
        self.grid_widget.metrics_updated.connect(self.update_sir_labels) # la funcion update_sir_labels se conecta a la señal metrics_updated emitida por grid_widget, lo que permite actualizar las etiquetas de métricas (S, I, R) en la interfaz cada vez que cambian los valores en la simulación
        self.grid_widget.fire_extinguished.connect(self.on_fire_extinguished)

        self.lbl_s = QtWidgets.QLabel("S (Vegetación): 100.0%") # QLabel incorpora texto estático a la interfaz, en este caso se usa para mostrar los porcentajes de cada estado del modelo SIR (Susceptible, Infectado, Recuperado) en la simulación de incendios forestales
        self.lbl_i = QtWidgets.QLabel("I (Fuego Activo): 0.0%")
        self.lbl_r = QtWidgets.QLabel("R (Área Quemada/Cortafuegos): 0.0%")

        metrics_style = "font-size: 20px; font-weight: 700;"
        self.lbl_s.setStyleSheet(metrics_style + " color: #2e7d32;") # setStyleSheet se usa para aplicar estilos CSS a los widgets de Qt, en este caso se define un estilo común para las etiquetas de métricas y luego se aplica un color diferente a cada una para diferenciarlas visualmente
        self.lbl_i.setStyleSheet(metrics_style + " color: #c62828;")
        self.lbl_r.setStyleSheet(metrics_style + " color: #424242;")

        metrics_box = QtWidgets.QVBoxLayout() # QVBoxLayout organiza los widgets en una disposición vertical, en este caso se usa para organizar las etiquetas de métricas (S, I, R) en la parte superior del panel lateral de la interfaz
        metrics_box.addWidget(self.lbl_s) # el método addWidget se usa para agregar widgets a un layout, en este caso se agregan las etiquetas de métricas al layout vertical
        metrics_box.addWidget(self.lbl_i)
        metrics_box.addWidget(self.lbl_r)

        self.map_combo = QtWidgets.QComboBox()
        self.map_combo.addItems(
            [
                "Valdeiglesias (Pinar)",
                "La Pedriza (Montaña)",
                "Mar de Ontígola (Humedal)",
                "Rivas (IUF)",
            ]
        )
        self.map_combo.currentIndexChanged.connect(self.on_map_preset_changed) # currentIndexChanged es una señal que se emite cuando el índice seleccionado en el QComboBox cambia, se conecta a un slot (función) que actualiza la simulación con los parámetros predefinidos para cada mapa

        self.view_label = QtWidgets.QLabel("Vistas")
        self.view_combo = QtWidgets.QComboBox()
        self.view_combo.addItems(
            [
                "Modo SIR (Fuego y Vegetación)",
                "Modo Orografía (Blanco y Negro)",
                "Modo Combustible (Azul)",
            ]
        )
        self.view_combo.currentIndexChanged.connect(self.on_view_mode_changed) # currentIndexChanged es una señal que se emite cuando el índice seleccionado en el QComboBox cambia, se conecta a un slot (función) que actualiza la simulación con los parámetros predefinidos para cada modo de vista

        self.load_custom_button = QtWidgets.QPushButton("Cargar Mapa Externo...")
        self.load_custom_button.clicked.connect(self.load_custom_map)

        self.wind_label = QtWidgets.QLabel("Fuerza del Viento")
        self.wind_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.wind_slider.setRange(0, 50)
        self.wind_slider.setValue(15)
        self.wind_value_label = QtWidgets.QLabel("1.5")
        self.wind_slider.valueChanged.connect(self.on_wind_strength_changed)

        self.wind_dir_label = QtWidgets.QLabel("Direccion del Viento (Grados)")
        self.wind_dir_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.wind_dir_slider.setRange(0, 360)
        self.wind_dir_slider.setValue(0)
        self.wind_dir_value_label = QtWidgets.QLabel("0°")
        self.wind_dir_slider.valueChanged.connect(self.on_wind_direction_changed)

        self.markov_checkbox = QtWidgets.QCheckBox("Viento Estocástico (Markov)")
        self.markov_checkbox.setChecked(True)
        self.markov_checkbox.toggled.connect(self.grid_widget.set_markov_wind_enabled)

        self.markov_amp_label = QtWidgets.QLabel("Caos del Viento (Markov): 0.15")
        self.markov_amp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.markov_amp_slider.setRange(0, 50)
        self.markov_amp_slider.setValue(15)
        self.markov_amp_slider.valueChanged.connect(self.on_markov_amplitude_changed)

        self.beta_label = QtWidgets.QLabel("Capacidad de contagio (β)")
        self.beta_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.beta_slider.setRange(0, 100)
        self.beta_slider.setValue(50)
        self.beta_value_label = QtWidgets.QLabel("0.60")
        self.beta_slider.valueChanged.connect(self.on_beta_changed)

        self.gamma_label = QtWidgets.QLabel("Tasa de recuperación (γ / Consumo de madera)")
        self.gamma_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gamma_slider.setRange(1, 100)
        self.gamma_slider.setValue(20)
        self.gamma_value_label = QtWidgets.QLabel("0.020")
        self.gamma_slider.valueChanged.connect(self.on_gamma_changed)

        self.pavesas_label = QtWidgets.QLabel("Focos Secundarios (Pavesas)")
        self.pavesas_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pavesas_slider.setRange(0, 100)
        self.pavesas_slider.setValue(0)
        self.pavesas_value_label = QtWidgets.QLabel("0.000")
        self.pavesas_slider.valueChanged.connect(self.on_pavesas_prob_changed)

        self.radio_ignicion = QtWidgets.QRadioButton("🔥 Ignición")
        self.radio_extincion = QtWidgets.QRadioButton("💧 Cortafuegos / Extinción")
        self.radio_ignicion.setChecked(True)
        self.radio_ignicion.toggled.connect(self.on_ignicion_toggled)
        self.radio_extincion.toggled.connect(self.on_extincion_toggled)

        self.step_button = QtWidgets.QPushButton("Paso")
        self.step_button.clicked.connect(self.grid_widget.step_once)

        self.reset_button = QtWidgets.QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.grid_widget.reset_state)

        self.play_button = QtWidgets.QPushButton("Iniciar")
        self.play_button.setCheckable(True)
        self.play_button.toggled.connect(self.toggle_timer)

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.step_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.reset_button)

        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(container)

        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.addLayout(metrics_box)
        panel_layout.addSpacing(12)
        panel_layout.addWidget(QtWidgets.QLabel("Escenario"))
        panel_layout.addWidget(self.map_combo)
        panel_layout.addWidget(self.view_label)
        panel_layout.addWidget(self.view_combo)
        panel_layout.addWidget(self.load_custom_button)
        panel_layout.addSpacing(12)
        panel_layout.addWidget(self.beta_label)
        beta_row = QtWidgets.QHBoxLayout()
        beta_row.addWidget(self.beta_slider)
        beta_row.addWidget(self.beta_value_label)
        panel_layout.addLayout(beta_row)
        panel_layout.addWidget(self.gamma_label)
        gamma_row = QtWidgets.QHBoxLayout()
        gamma_row.addWidget(self.gamma_slider)
        gamma_row.addWidget(self.gamma_value_label)
        panel_layout.addLayout(gamma_row)

        viento_box = QtWidgets.QGroupBox("Viento")
        viento_layout = QtWidgets.QVBoxLayout(viento_box)
        viento_layout.addWidget(self.wind_label)
        wind_row = QtWidgets.QHBoxLayout()
        wind_row.addWidget(self.wind_slider)
        wind_row.addWidget(self.wind_value_label)
        viento_layout.addLayout(wind_row)
        viento_layout.addWidget(self.wind_dir_label)
        wind_dir_row = QtWidgets.QHBoxLayout()
        wind_dir_row.addWidget(self.wind_dir_slider)
        wind_dir_row.addWidget(self.wind_dir_value_label)
        viento_layout.addLayout(wind_dir_row)
        viento_layout.addWidget(self.markov_checkbox)
        viento_layout.addWidget(self.markov_amp_label)
        viento_layout.addWidget(self.markov_amp_slider)
        panel_layout.addWidget(viento_box)

        pavesas_box = QtWidgets.QGroupBox("Pavesas")
        pavesas_layout = QtWidgets.QVBoxLayout(pavesas_box)
        pavesas_layout.addWidget(self.pavesas_label)
        pavesas_row = QtWidgets.QHBoxLayout()
        pavesas_row.addWidget(self.pavesas_slider)
        pavesas_row.addWidget(self.pavesas_value_label)
        pavesas_layout.addLayout(pavesas_row)
        panel_layout.addWidget(pavesas_box)
        panel_layout.addSpacing(12)
        panel_layout.addWidget(self.radio_ignicion)
        panel_layout.addWidget(self.radio_extincion)
        panel_layout.addStretch(1)
        panel_layout.addLayout(controls)

        panel_widget = QtWidgets.QWidget()
        panel_widget.setStyleSheet(
            "QGroupBox { border: 1px solid #777; border-radius: 6px; margin-top: 10px; padding-top: 8px; font-weight: 600; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
        )
        panel_widget.setLayout(panel_layout)

        main_layout.addWidget(self.grid_widget, 4)
        main_layout.addWidget(panel_widget, 1)

        self.setCentralWidget(container)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(max(1, int(1000 / max(config.fps, 1))))
        self.timer.timeout.connect(self.grid_widget.step_once)
        self.grid_widget.set_sim_timer(self.timer)

        self.grid_widget.set_markov_wind_enabled(self.markov_checkbox.isChecked())
        self.on_pavesas_prob_changed(self.pavesas_slider.value())
        self.grid_widget.set_view_mode(self.view_combo.currentIndex())
        self.grid_widget.set_tool_mode("fire")
        self.on_map_preset_changed(self.map_combo.currentIndex())
        self.on_beta_changed(self.beta_slider.value())
        self.on_gamma_changed(self.gamma_slider.value())


# Slots para manejar las interacciones de la interfaz y actualizar la simulación en consecuencia
# Toda la comunicación con glsl está aislada dentro de GridWidget, MainWindow solo se encarga de 
# manejar la interfaz y las señales/slots para actualizar los controles y mostrar la información 
# relevante al usuario. Son funciones decoradas con @QtCore.Slot para indicar que son slots 
# que pueden ser conectados a señales emitidas por los widgets de Qt, lo que permite una 
# comunicación eficiente entre la interfaz gráfica y la lógica de la simulación sin acoplar 
# directamente el código de la simulación con el código de la interfaz.
    @QtCore.Slot(bool)
    def toggle_timer(self, checked: bool):
        if checked:
            self.play_button.setText("Pausar")
            self.timer.start()
            return

        self.play_button.setText("Iniciar")
        self.timer.stop()

    @QtCore.Slot(float, float, float)
    def update_sir_labels(self, susceptible: float, infected: float, recovered: float):
        self.lbl_s.setText(f"S (Vegetación): {susceptible:.1f}%")
        self.lbl_i.setText(f"I (Fuego Activo): {infected:.1f}%")
        self.lbl_r.setText(f"R (Área Quemada/Cortafuegos): {recovered:.1f}%")

    @QtCore.Slot(bool)
    def on_ignicion_toggled(self, checked: bool):
        if checked:
            self.grid_widget.set_tool_mode("fire")

    @QtCore.Slot(bool)
    def on_extincion_toggled(self, checked: bool):
        if checked:
            self.grid_widget.set_tool_mode("firebreak")

    @QtCore.Slot(int)
    def on_wind_strength_changed(self, value: int):
        wind_speed = value / 10.0
        self.wind_value_label.setText(f"{wind_speed:.1f}")
        self.grid_widget.set_wind_strength(value)

    @QtCore.Slot(int)
    def on_wind_direction_changed(self, value: int):
        self.wind_dir_value_label.setText(f"{value}°")
        self.grid_widget.set_wind_direction_degrees(value)

    @QtCore.Slot(int)
    def on_beta_changed(self, value: int):
        beta = (value / 100.0) * 1.2
        humedad = 100 - value
        self.beta_value_label.setText(f"{beta:.2f} (Humedad: {humedad}%)")
        self.grid_widget.set_beta(value)

    @QtCore.Slot(int)
    def on_markov_amplitude_changed(self, value: int):
        amplitude = value / 100.0
        self.markov_amp_label.setText(f"Caos del Viento (Markov): {amplitude:.2f}")
        self.grid_widget.set_markov_amplitude(value)

  
    @QtCore.Slot(int)
    def on_pavesas_prob_changed(self, value: int):
        # Hay que usar un valor pequeño
        prob = value / 1e4
        self.pavesas_value_label.setText(f"{prob:.1e}")
        self.grid_widget.set_pavesas_prob(prob)

    @QtCore.Slot(int)
    def on_view_mode_changed(self, index: int):
        self.grid_widget.set_view_mode(index)

    @QtCore.Slot(int)
    def on_gamma_changed(self, value: int):
        gamma = value / 1000.0
        tiempo_minutos = int(1.0 / gamma)
        self.gamma_value_label.setText(f"{gamma:.3f} (Tiempo de llama: {tiempo_minutos} min)")
        self.grid_widget.set_gamma(gamma)

    @QtCore.Slot(int)
    def on_map_preset_changed(self, index: int):
        presets = {
            0: {"wind": 25, "beta": 50, "gamma": 10, "pavesas": 0},  # Valdeiglesias
            1: {"wind": 15, "beta": 40, "gamma": 20, "pavesas": 0},  # Pedriza
            2: {"wind": 10, "beta": 35, "gamma": 80, "pavesas": 0},  # Ontigola
            3: {"wind": 20, "beta": 45, "gamma": 30, "pavesas": 0},  # Rivas
        }
        preset = presets.get(index)
        if preset is None:
            return

        self.wind_slider.setValue(preset["wind"])
        self.beta_slider.setValue(preset["beta"])
        self.gamma_slider.setValue(preset["gamma"])
        self.pavesas_slider.setValue(preset["pavesas"])
        self.grid_widget.load_map(self.map_combo.currentText())

    @QtCore.Slot()
    def on_fire_extinguished(self):
        if self.play_button.isChecked():
            self.play_button.setChecked(False)
            return

        self.play_button.setText("Iniciar")

    @QtCore.Slot()
    def load_custom_map(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Seleccionar mapa externo",
            "",
            "Imagenes (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return

        self.grid_widget.load_custom_map(file_path)
