# main_window.py
"""
Ventana principal de la aplicación.
Configura la interfaz gráfica (PySide6), aplica el estilo visual claro
y conecta los controles con el motor de simulación en OpenGL (GridWidget).
"""

from PySide6 import QtCore, QtWidgets
from config import SimulationConfig
from grid_widget import GridWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config: SimulationConfig):
        super().__init__()
        self.setWindowTitle("Propagación de Incendios Forestales — Motor GPU")

        self.grid_widget = GridWidget(config=config)
        self.grid_widget.metrics_updated.connect(self.update_sir_labels)
        self.grid_widget.fire_extinguished.connect(self.on_fire_extinguished)

        # --- Tarjetas de métricas SIR ---
        self.lbl_s = QtWidgets.QLabel("S (Vegetación): 100.0 %")
        self.lbl_s.setObjectName("card_s")
        self.lbl_i = QtWidgets.QLabel("I (Fuego Activo): 0.0 %")
        self.lbl_i.setObjectName("card_i")
        self.lbl_r = QtWidgets.QLabel("R (Quemado / Cortafuegos): 0.0 %")
        self.lbl_r.setObjectName("card_r")

        metrics_box = QtWidgets.QVBoxLayout()
        metrics_box.setSpacing(4)
        metrics_box.addWidget(self.lbl_s)
        metrics_box.addWidget(self.lbl_i)
        metrics_box.addWidget(self.lbl_r)

        # --- Escenario ---
        lbl_escenario = QtWidgets.QLabel("Escenario")
        lbl_escenario.setObjectName("section_header")

        self.map_combo = QtWidgets.QComboBox()
        self.map_combo.addItems([
            "Valdeiglesias (Pinar)",
            "La Pedriza (Montaña)",
            "Mar de Ontígola (Humedal)",
            "Rivas (IUF)",
            "Sierra de Guadarrama (Real)",
        ])
        self.map_combo.currentIndexChanged.connect(self.on_map_preset_changed)

        self.load_custom_button = QtWidgets.QPushButton("Cargar Mapa Externo…")
        self.load_custom_button.clicked.connect(self.load_custom_map)

        # --- Vistas ---
        lbl_vistas = QtWidgets.QLabel("Vista del mapa")
        lbl_vistas.setObjectName("subsection_header")

        self.view_combo = QtWidgets.QComboBox()
        self.view_combo.addItems([
            "Modo SIR (Fuego y Vegetación)",
            "Modo Orografía (Blanco y Negro)",
            "Modo Combustible (Azul)",
            "Modo Satélite / Raster",
        ])
        self.view_combo.currentIndexChanged.connect(self.on_view_mode_changed)

        # --- Parámetros SIR ---
        lbl_sir = QtWidgets.QLabel("Parámetros SIR")
        lbl_sir.setObjectName("section_header")

        self.beta_label = QtWidgets.QLabel("<b>β</b> (Tasa de contagio por radiación / 1 - H)")
        self.beta_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.beta_slider.setRange(0, 100)
        self.beta_slider.setValue(60)
        self.beta_value_label = QtWidgets.QLabel("β = 0.60  (H = 40 %)")
        self.beta_value_label.setMinimumWidth(150)
        self.beta_slider.valueChanged.connect(self.on_beta_changed)

        self.gamma_label = QtWidgets.QLabel("<b>γ</b>  (Consumo / τ = 1/γ)")
        self.gamma_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gamma_slider.setRange(1, 200)
        self.gamma_slider.setValue(10)
        self.gamma_value_label = QtWidgets.QLabel("γ = 0.010  (τ = 100 pasos)")
        self.gamma_value_label.setMinimumWidth(150)
        self.gamma_slider.valueChanged.connect(self.on_gamma_changed)

        self.r0_label = QtWidgets.QLabel("<b>R<sub>0</sub></b> = β / γ = 60.00")
        self.r0_label.setObjectName("r0_label")

        # --- Viento (Proceso Ornstein-Uhlenbeck) ---
        self.wind_label = QtWidgets.QLabel("<b>||u||</b> (Magnitud)")
        self.wind_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.wind_slider.setRange(0, 50)
        self.wind_slider.setValue(0)
        self.wind_value_label = QtWidgets.QLabel("0.0")
        self.wind_value_label.setMinimumWidth(30)
        self.wind_slider.valueChanged.connect(self.on_wind_strength_changed)

        self.wind_dir_label = QtWidgets.QLabel("<b>θ<sub>base</sub></b> (Dirección media)")
        self.wind_dir_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.wind_dir_slider.setRange(0, 360)
        self.wind_dir_slider.setValue(0)
        self.wind_dir_value_label = QtWidgets.QLabel("0°")
        self.wind_dir_value_label.setMinimumWidth(30)
        self.wind_dir_slider.valueChanged.connect(self.on_wind_direction_changed)

        self.markov_checkbox = QtWidgets.QCheckBox("Viento Estocástico (Ornstein-Uhlenbeck)")
        self.markov_checkbox.setChecked(False)
        self.markov_checkbox.toggled.connect(self.grid_widget.set_markov_wind_enabled)

        self.markov_amp_label = QtWidgets.QLabel("<b>σ</b> (Varianza del ruido): 0.15 rad")
        self.markov_amp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.markov_amp_slider.setRange(0, 50)
        self.markov_amp_slider.setValue(15)
        self.markov_amp_slider.valueChanged.connect(self.on_markov_amplitude_changed)

        # Configuración del estado habilitado/deshabilitado de Markov
        self.markov_amp_label.setEnabled(False)
        self.markov_amp_slider.setEnabled(False)
        self.markov_checkbox.toggled.connect(self.markov_amp_label.setEnabled)
        self.markov_checkbox.toggled.connect(self.markov_amp_slider.setEnabled)

        # --- Pavesas (Saltos no locales) ---
        self.pavesas_label = QtWidgets.QLabel("<b>λ</b> (Prob. de foco secundario por paso)")
        self.pavesas_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pavesas_slider.setRange(0, 100)
        self.pavesas_slider.setValue(0)
        self.pavesas_value_label = QtWidgets.QLabel("0.0e+00")
        self.pavesas_value_label.setMinimumWidth(50)
        self.pavesas_slider.valueChanged.connect(self.on_pavesas_prob_changed)

        # --- Herramientas ---
        self.radio_ignicion = QtWidgets.QRadioButton("🔥 Ignición")
        self.radio_extincion = QtWidgets.QRadioButton("💧 Cortafuegos / Extinción")
        self.radio_ignicion.setChecked(True)
        self.radio_ignicion.toggled.connect(self.on_ignicion_toggled)
        self.radio_extincion.toggled.connect(self.on_extincion_toggled)

        # --- Botones de control ---
        self.step_button = QtWidgets.QPushButton("Paso")
        self.step_button.clicked.connect(self.grid_widget.step_once)

        self.play_button = QtWidgets.QPushButton("Iniciar")
        self.play_button.setCheckable(True)
        self.play_button.setObjectName("play_button")
        self.play_button.toggled.connect(self.toggle_timer)

        self.reset_button = QtWidgets.QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.grid_widget.reset_state)

        controls = QtWidgets.QHBoxLayout()
        controls.setSpacing(6)
        controls.addWidget(self.step_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.reset_button)

        # =========================================================
        # MONTAJE DEL PANEL LATERAL
        # =========================================================
        panel_inner = QtWidgets.QVBoxLayout()
        panel_inner.setContentsMargins(10, 10, 10, 10)
        panel_inner.setSpacing(6)

        # Métricas
        panel_inner.addLayout(metrics_box)
        panel_inner.addSpacing(6)

        # Escenario
        panel_inner.addWidget(lbl_escenario)
        panel_inner.addWidget(self.map_combo)
        panel_inner.addWidget(self.load_custom_button)
        panel_inner.addSpacing(4)

        # Vistas (Subordinadas al escenario visualmente)
        panel_inner.addWidget(lbl_vistas)
        vistas_indent = QtWidgets.QHBoxLayout()
        vistas_indent.setContentsMargins(12, 0, 0, 0)
        vistas_indent.addWidget(self.view_combo)
        panel_inner.addLayout(vistas_indent)
        panel_inner.addSpacing(10)

        # Parámetros SIR
        panel_inner.addWidget(lbl_sir)
        panel_inner.addWidget(self.beta_label)
        beta_row = QtWidgets.QHBoxLayout()
        beta_row.addWidget(self.beta_slider)
        beta_row.addWidget(self.beta_value_label)
        panel_inner.addLayout(beta_row)

        panel_inner.addWidget(self.gamma_label)
        gamma_row = QtWidgets.QHBoxLayout()
        gamma_row.addWidget(self.gamma_slider)
        gamma_row.addWidget(self.gamma_value_label)
        panel_inner.addLayout(gamma_row)
        panel_inner.addWidget(self.r0_label)
        panel_inner.addSpacing(6)

        # Viento (Panel Desplegable)
        self.btn_viento = QtWidgets.QPushButton("▶ Viento Atmosférico")
        self.btn_viento.setCheckable(True)
        self.btn_viento.setChecked(False)
        self.btn_viento.setObjectName("toggle_btn")
        self.btn_viento.toggled.connect(self.toggle_viento)

        self.frame_viento = QtWidgets.QFrame()
        self.frame_viento.setVisible(False)
        viento_layout = QtWidgets.QVBoxLayout(self.frame_viento)
        viento_layout.setContentsMargins(12, 4, 0, 4)
        viento_layout.setSpacing(4)
        
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

        # Pavesas (Panel Desplegable)
        self.btn_pavesas = QtWidgets.QPushButton("▶ Pavesas (Dispersión no local)")
        self.btn_pavesas.setCheckable(True)
        self.btn_pavesas.setChecked(False)
        self.btn_pavesas.setObjectName("toggle_btn")
        self.btn_pavesas.toggled.connect(self.toggle_pavesas)

        self.frame_pavesas = QtWidgets.QFrame()
        self.frame_pavesas.setVisible(False)
        pavesas_layout = QtWidgets.QVBoxLayout(self.frame_pavesas)
        pavesas_layout.setContentsMargins(12, 4, 0, 4)
        pavesas_layout.setSpacing(4)
        
        pavesas_layout.addWidget(self.pavesas_label)
        pavesas_row = QtWidgets.QHBoxLayout()
        pavesas_row.addWidget(self.pavesas_slider)
        pavesas_row.addWidget(self.pavesas_value_label)
        pavesas_layout.addLayout(pavesas_row)

        panel_inner.addWidget(self.btn_viento)
        panel_inner.addWidget(self.frame_viento)
        panel_inner.addWidget(self.btn_pavesas)
        panel_inner.addWidget(self.frame_pavesas)

        # Modos de herramienta de interacción
        panel_inner.addSpacing(10)
        panel_inner.addWidget(self.radio_ignicion)
        panel_inner.addWidget(self.radio_extincion)
        
        panel_inner.addStretch(1)
        panel_inner.addLayout(controls)

        # Widget interior del scroll
        panel_content = QtWidgets.QWidget()
        panel_content.setObjectName("panel_content")
        panel_content.setLayout(panel_inner)

        # ScrollArea lateral
        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("panel_scroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel_content)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(340)
        scroll.setMaximumWidth(400)

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================
        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.grid_widget, 4)
        main_layout.addWidget(scroll, 1)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Inicializado | 0 iteraciones")

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

        self.setStyleSheet(LIGHT_STYLESHEET)

    # ----- Slots -----

    @QtCore.Slot(bool)
    def toggle_timer(self, checked: bool):
        if checked:
            self.play_button.setText("Pausar")
            self.timer.start()
            return
        self.play_button.setText("Iniciar")
        self.timer.stop()

    @QtCore.Slot(bool)
    def toggle_viento(self, checked: bool):
        self.frame_viento.setVisible(checked)
        self.btn_viento.setText("▼ Viento Atmosférico" if checked else "▶ Viento Atmosférico")

    @QtCore.Slot(bool)
    def toggle_pavesas(self, checked: bool):
        self.frame_pavesas.setVisible(checked)
        self.btn_pavesas.setText("▼ Pavesas (Dispersión no local)" if checked else "▶ Pavesas (Dispersión no local)")

    @QtCore.Slot(float, float, float, float, int)
    def update_sir_labels(self, susceptible: float, infected: float,
                          recovered: float, actual_fps: float, total_steps: int):
        self.lbl_s.setText(f"S (Vegetación): {susceptible:.1f} %")
        self.lbl_i.setText(f"I (Fuego Activo): {infected:.1f} %")
        self.lbl_r.setText(f"R (Quemado / Cortafuegos): {recovered:.1f} %")
        self.statusBar().showMessage(
            f"Pasos: {total_steps}  |  {actual_fps:.1f} it/s  "
            f"(Objetivo: {self.grid_widget.config.fps} FPS)"
        )

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
        beta = value / 100.0
        humedad = 100 - value
        self.beta_value_label.setText(f"β = {beta:.2f} (H = {humedad}%)")
        self.grid_widget.set_beta(beta)
        self.update_r0_label()

    @QtCore.Slot(int)
    def on_markov_amplitude_changed(self, value: int):
        amplitude = value / 100.0
        self.markov_amp_label.setText(f"<b>σ</b> (Varianza ruido): {amplitude:.2f} rad")
        self.grid_widget.set_markov_amplitude(value)

    @QtCore.Slot(int)
    def on_pavesas_prob_changed(self, value: int):
        prob = value / 1e4
        self.pavesas_value_label.setText(f"{prob:.1e}")
        self.grid_widget.set_pavesas_prob(prob)

    @QtCore.Slot(int)
    def on_view_mode_changed(self, index: int):
        self.grid_widget.set_view_mode(index)

    @QtCore.Slot(int)
    def on_gamma_changed(self, value: int):
        gamma = value / 1000.0
        t_llama = int(1.0 / gamma) if gamma > 0 else 9999
        self.gamma_value_label.setText(f"γ = {gamma:.3f} (τ = {t_llama}p)")
        self.grid_widget.set_gamma(gamma)
        self.update_r0_label()

    def update_r0_label(self):
        beta = self.beta_slider.value() / 100.0
        gamma = self.gamma_slider.value() / 1000.0
        if gamma > 0:
            r0 = beta / gamma
            self.r0_label.setText(f"<b>R<sub>0</sub></b> = β / γ = {r0:.2f}")
        else:
            self.r0_label.setText("<b>R<sub>0</sub></b> = β / γ = ∞  (γ = 0)")

    @QtCore.Slot(int)
    def on_map_preset_changed(self, index: int):
        presets = {
            0: {"wind": 0, "beta": 60, "gamma": 10, "pavesas": 0},
            1: {"wind": 0, "beta": 48, "gamma": 20, "pavesas": 0},
            2: {"wind": 0, "beta": 42, "gamma": 80, "pavesas": 0},
            3: {"wind": 0, "beta": 54, "gamma": 30, "pavesas": 0},
            4: {"wind": 0, "beta": 48, "gamma": 20, "pavesas": 0},
        }
        preset = presets.get(index)
        if preset is None:
            return

        self.wind_slider.setValue(preset["wind"])
        self.beta_slider.setValue(preset["beta"])
        self.gamma_slider.setValue(preset["gamma"])
        self.pavesas_slider.setValue(preset["pavesas"])
        
        map_files = {
            0: "valdeiglesias.png",
            1: "pedriza.png",
            2: "ontigola.png",
            3: "rivas.png",
            4: "guadarrama1_real.png"
        }
        self.grid_widget.current_map_file = map_files.get(index, "valdeiglesias.png")
        self.grid_widget.custom_map_path = None
        if self.grid_widget.ctx is not None and self.grid_widget._is_initialized:
            self.grid_widget.reset_state()
        
        self._adapt_window_to_current_grid()

    def _adapt_window_to_current_grid(self):
        if self.isMaximized() or self.isFullScreen():
            return
        grid_w = max(1, int(self.grid_widget.config.grid_width))
        grid_h = max(1, int(self.grid_widget.config.grid_height))
        map_ratio = grid_w / grid_h
        target_w = int(self.height() * map_ratio * 1.25)
        target_w = max(target_w, 950)
        screen = self.screen()
        if screen is not None:
            target_w = min(target_w, screen.availableGeometry().width())
        if abs(self.width() - target_w) > 8:
            self.resize(target_w, self.height())

    @QtCore.Slot()
    def on_fire_extinguished(self):
        if self.play_button.isChecked():
            self.play_button.setChecked(False)
            return
        self.play_button.setText("Iniciar")

    @QtCore.Slot()
    def load_custom_map(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar mapa externo", "",
            "Imágenes (*.png *.jpg *.jpeg)")
        if not file_path:
            return
        self.grid_widget.load_custom_map(file_path)
        self._adapt_window_to_current_grid()


# ==============================================================
# TEMA CLARO  —  Estilo científico limpio
# ==============================================================
LIGHT_STYLESHEET = """
/* --- Base --- */
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #222222;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* --- Panel lateral --- */
QWidget#panel_content {
    background-color: #ffffff;
}
QScrollArea#panel_scroll {
    background-color: #ffffff;
    border-left: 1px solid #d0d0d0;
}

/* --- Tarjetas SIR --- */
QLabel#card_s {
    background-color: #e8f5e9;
    color: #1b5e20;
    border: 1px solid #a5d6a7;
    border-radius: 5px;
    padding: 7px 10px;
    font-weight: bold;
    font-size: 13px;
}
QLabel#card_i {
    background-color: #fce4ec;
    color: #b71c1c;
    border: 1px solid #ef9a9a;
    border-radius: 5px;
    padding: 7px 10px;
    font-weight: bold;
    font-size: 13px;
}
QLabel#card_r {
    background-color: #eceff1;
    color: #37474f;
    border: 1px solid #b0bec5;
    border-radius: 5px;
    padding: 7px 10px;
    font-weight: bold;
    font-size: 13px;
}

/* --- Encabezados de sección --- */
QLabel#section_header {
    font-size: 13px;
    font-weight: bold;
    color: #1565c0;
    padding-top: 6px;
    padding-bottom: 2px;
}

QLabel#subsection_header {
    font-size: 12px;
    font-weight: bold;
    color: #546e7a;
    padding-top: 6px;
}

/* --- R0 --- */
QLabel#r0_label {
    font-size: 14px;
    color: #222222;
    padding: 2px 0px;
}

/* --- Frames internos de paneles desplegables --- */
QFrame {
    background-color: transparent;
    border: none;
}

/* --- Sliders --- */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    margin: 0px;
}
QSlider::handle:horizontal {
    background: #1976d2;
    border: none;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #42a5f5;
}

/* Sliders Desactivados */
QSlider:disabled::groove:horizontal {
    background: #f0f0f0;
}
QSlider:disabled::handle:horizontal {
    background: #cccccc;
}

/* Labels Desactivados */
QLabel:disabled {
    color: #9e9e9e;
}

/* --- Botones --- */
QPushButton {
    background-color: #e8eaf6;
    border: 1px solid #9fa8da;
    border-radius: 5px;
    padding: 6px 14px;
    color: #283593;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #c5cae9;
    border-color: #7986cb;
}
QPushButton:pressed {
    background-color: #3f51b5;
    color: #ffffff;
}
QPushButton:checked {
    background-color: #43a047;
    border-color: #388e3c;
    color: #ffffff;
}

/* --- ComboBox --- */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 5px;
    padding: 4px 8px;
    color: #222222;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #1976d2;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    selection-background-color: #bbdefb;
    selection-color: #0d47a1;
    color: #222222;
}

/* --- Radio y Checkbox --- */
QRadioButton, QCheckBox {
    spacing: 6px;
    color: #333333;
    font-size: 13px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QRadioButton::indicator { border-radius: 8px; }
QCheckBox::indicator   { border-radius: 3px; }
QRadioButton::indicator:unchecked, QCheckBox::indicator:unchecked {
    border: 1.5px solid #9e9e9e;
    background: #fafafa;
}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    border: 1.5px solid #1976d2;
    background: #1976d2;
}

/* Checkbox con cruz estilizada */
QCheckBox::indicator:checked {
    border: 1.5px solid #1976d2;
    background-color: #1976d2;
    image: url(none);
}

/* --- Barra de estado --- */
QStatusBar {
    background-color: #e8eaf6;
    border-top: 1px solid #c5cae9;
    color: #37474f;
    font-size: 12px;
}

/* --- ScrollBar vertical del panel --- */
QScrollBar:vertical {
    background: #f5f5f5;
    width: 8px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #bdbdbd;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #9e9e9e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* --- Botones Desplegables --- */
QPushButton#toggle_btn {
    background-color: transparent;
    border: none;
    color: #1565c0;
    text-align: left;
    font-weight: bold;
    font-size: 13px;
    padding: 4px 0px;
    margin-top: 6px;
}
QPushButton#toggle_btn:hover {
    color: #0d47a1;
    text-decoration: underline;
}
"""