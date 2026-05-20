# grid_widget.py
"""
Widget OpenGL para la simulación y renderizado en tiempo real.
Gestiona texturas, shaders y el estado del autómata celular SIR.
"""

from pathlib import Path
import math
import random
import time

import moderngl
import numpy as np
from PIL import Image
from PySide6 import QtCore
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from config import SimulationConfig
from map_generator import (
    generate_ontigola,
    generate_pedriza,
    generate_rivas,
    generate_valdeiglesias,
)


def load_shader_source(shader_file: str) -> str:
    shader_path = Path(__file__).parent / shader_file
    with open(shader_path, "r", encoding="utf-8") as f:
        return f.read()


class GridWidget(QOpenGLWidget):
    metrics_updated = QtCore.Signal(float, float, float, float, int)
    fire_extinguished = QtCore.Signal()
    REAL_MAP_FILES = {"guadarrama1_real.png", "guadarrama_real.png"}

    def __init__(self, config: SimulationConfig):
        super().__init__()
        self.config = config
        self._artificial_grid_size = (
            max(1, int(config.grid_width)),
            max(1, int(config.grid_height)),
        )

        self.ctx = None
        self.display_program = None
        self.step_program = None
        self.activate_program = None
        self.block_program = None

        self.display_vao = None
        self.step_vao = None
        self.activate_vao = None
        self.block_vao = None

        self.fbos = []
        self.textures = []
        self.bg_texture = None
        self.current_texture_idx = 0
        self.frame_count = 0
        self.base_wind_angle = 0.0
        self.current_wind_angle = 0.0
        self.wind_speed_base = 1.5
        self.markov_wind = True
        self.markov_amplitude = 0.15
        self.view_mode = 0
        self.beta = 1.0
        self.gamma = 0.02
        self.pavesas_prob = 0.0
        self.sim_timer = None
        self._fire_out_reported = False
        self.selected_tool = "fire"
        self.current_map_file = "valdeiglesias.png"
        self.custom_map_path = None
        self._is_initialized = False
        self._display_viewport = (0.0, 0.0, 1.0, 1.0)

        # Seguimiento del rendimiento para calcular iteraciones/segundo
        self.last_frame_count = 0
        self.last_metrics_time = time.time()

        self.metrics_timer = QtCore.QTimer(self)
        self.metrics_timer.setInterval(1000)
        self.metrics_timer.timeout.connect(self.update_sir_metrics)
        self.metrics_timer.start()

    def initializeGL(self): # El mÃ©todo clave, donde configuramos el contexto de OpenGL, cargamos los shaders, creamos los VAOs para renderizar un cuadrado que cubre toda la pantalla, y configuramos las texturas y FBOs para almacenar el estado de la simulaciÃ³n. TambiÃ©n cargamos el mapa inicial y lo escribimos en las texturas para comenzar la simulaciÃ³n.
        self.ctx = moderngl.create_context() # Creamos el contexto de OpenGL, que es necesario para cualquier operaciÃ³n grÃ¡fica. Este contexto nos permitirÃ¡ crear shaders, texturas, buffers y realizar renderizado en la GPU.

        # Cargamos los shaders desde archivos GLSL. Estos shaders son programas que se ejecutan en la GPU para realizar el renderizado y la simulaciÃ³n del fuego. El shader de vÃ©rtices es comÃºn para todos, mientras que los shaders de fragmentos son especÃ­ficos para cada etapa de la simulaciÃ³n (renderizado, paso de simulaciÃ³n, activaciÃ³n de cÃ©lulas, bloqueo de cÃ©lulas).
        vertex_source = load_shader_source("shaders/vertex.glsl")
        display_source = load_shader_source("shaders/display.glsl")
        step_source = load_shader_source("shaders/step.glsl")
        activate_source = load_shader_source("shaders/activate_cell.glsl")
        block_source = load_shader_source("shaders/block_cell.glsl")

        # Creamos los programas de shaders a partir del cÃ³digo fuente cargado. Cada programa de shader se compila y se vincula, y luego podemos usarlo para renderizar o simular el fuego. El programa de display se usarÃ¡ para renderizar la cuadrÃ­cula en la pantalla, el programa de step se usarÃ¡ para calcular el siguiente estado de la simulaciÃ³n, y los programas de activate y block se usarÃ¡n para modificar el estado de cÃ©lulas individuales cuando el usuario interactÃºe con la cuadrÃ­cula.
        self.display_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=display_source)
        self.step_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=step_source)
        self.activate_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=activate_source)
        self.block_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=block_source)

        # Creamos un VAO (Vertex Array Object) para cada programa de shader. El VAO define cÃ³mo se deben interpretar los datos de vÃ©rtices que le pasamos. En este caso, estamos creando un cuadrado que cubre toda la pantalla, con coordenadas de vÃ©rtices que van de -1 a 1 en ambas direcciones. Este cuadrado se usarÃ¡ para renderizar la simulaciÃ³n y para aplicar los shaders de paso, activaciÃ³n y bloqueo a toda la cuadrÃ­cula.
        vertices = np.array([-1, -1, 1, -1, 1, 1, -1, 1], dtype="f4") #  hay en total 4 vÃ©rtices, cada uno con 2 componentes (x e y), que forman un cuadrado que cubre toda la pantalla. Las coordenadas van de -1 a 1 porque en OpenGL, el espacio de coordenadas normalizado para el renderizado va de -1 a 1 en ambas direcciones.
        indices = np.array([0, 1, 2, 0, 2, 3], dtype="i4") # Estos Ã­ndices definen dos triÃ¡ngulos que forman el cuadrado. El primer triÃ¡ngulo estÃ¡ formado por los vÃ©rtices 0, 1 y 2, y el segundo triÃ¡ngulo estÃ¡ formado por los vÃ©rtices 0, 2 y 3. Esto es necesario porque OpenGL renderiza en tÃ©rminos de triÃ¡ngulos, asÃ­ que necesitamos dividir nuestro cuadrado en dos triÃ¡ngulos para poder renderizarlo correctamente.
        vbo = self.ctx.buffer(vertices) 
        ebo = self.ctx.buffer(indices)

        # Creamos un VAO para cada programa de shader, usando el mismo VBO (vertices) y EBO (Ã­ndices). Esto nos permite usar el mismo conjunto de vÃ©rtices para renderizar con diferentes shaders, lo que es eficiente y conveniente. Cada VAO se configura para interpretar los datos del VBO como pares de floats (2f) que corresponden a la variable de entrada "aPos" en los shaders.
        self.display_vao = self.ctx.vertex_array(self.display_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.step_vao = self.ctx.vertex_array(self.step_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.activate_vao = self.ctx.vertex_array(self.activate_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.block_vao = self.ctx.vertex_array(self.block_program, [(vbo, "2f", "aPos")], index_buffer=ebo)

        self._create_sim_buffers(self.config.grid_width, self.config.grid_height)

        self.reset_state() # Carga el mapa inicial y lo escribe en las texturas para comenzar la simulaciÃ³n. Esto asegura que cuando la aplicaciÃ³n se inicie, ya tengamos un estado inicial de la simulaciÃ³n cargado y listo para ser renderizado y simulado.
        self._is_initialized = True

    def _create_sim_buffers(self, width: int, height: int):
        for fbo in self.fbos:
            fbo.release()
        for tex in self.textures:
            tex.release()

        self.fbos = []
        self.textures = []
        for _ in range(2):
            tex = self.ctx.texture((width, height), 4, dtype="f4")
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            tex.repeat_x = False
            tex.repeat_y = False
            self.textures.append(tex)
            self.fbos.append(self.ctx.framebuffer(color_attachments=[tex]))

    # El mÃ©todo paintGL se llama cada vez que la ventana necesita ser redibujada. En este mÃ©todo, configuramos el framebuffer para renderizar, limpiamos la pantalla con un color de fondo, y luego usamos el programa de display para renderizar la textura actual de la simulaciÃ³n en la pantalla. Esto nos permite ver el estado actual del fuego en la cuadrÃ­cula.
    def paintGL(self): 
        if not self._is_initialized:
            return

        draw_fbo = self.ctx.detect_framebuffer() #
        draw_fbo.use()

        fb_w, fb_h = draw_fbo.size
        self.ctx.viewport = (0, 0, max(1, fb_w), max(1, fb_h))

        self.ctx.clear(0.06, 0.08, 0.09, 1.0)

        view_w = max(1.0, float(self.width()))
        view_h = max(1.0, float(self.height()))
        tex_w = max(1, self.config.grid_width)
        tex_h = max(1, self.config.grid_height)

        # Mostramos el mapa completo (fit) para mantener una correspondencia
        # estable entre celdas y vista al redimensionar la ventana.
        scale = min(view_w / tex_w, view_h / tex_h)
        vp_w = max(1.0, tex_w * scale)
        vp_h = max(1.0, tex_h * scale)
        vp_x = (view_w - vp_w) / 2.0
        vp_y = (view_h - vp_h) / 2.0
        self._display_viewport = (vp_x, vp_y, vp_w, vp_h)

        # ConversiÃ³n a pÃ­xeles reales del framebuffer para evitar errores HiDPI.
        scale_x = fb_w / view_w
        scale_y = fb_h / view_h
        gl_vp_x = int(round(vp_x * scale_x))
        gl_vp_y = int(round(vp_y * scale_y))
        gl_vp_w = max(1, int(round(vp_w * scale_x)))
        gl_vp_h = max(1, int(round(vp_h * scale_y)))
        self.ctx.viewport = (gl_vp_x, gl_vp_y, gl_vp_w, gl_vp_h)

        self.textures[self.current_texture_idx].use(location=0)
        self.display_program["u_state_texture"].value = 0
        self.display_program["u_bg_texture"].value = 1
        if self.bg_texture is not None:
            self.bg_texture.use(location=1)
            self.display_program["u_has_bg_texture"].value = 1
        else:
            self.display_program["u_has_bg_texture"].value = 0
        self.display_program["u_view_mode"].value = self.view_mode
        self.display_vao.render(moderngl.TRIANGLES)

    def step_once(self):
        if not self._is_initialized:
            return

        self.makeCurrent()
        try:
            source_idx = self.current_texture_idx
            dest_idx = 1 - source_idx
            self.frame_count += 1 

            if self.markov_wind: 
                self.current_wind_angle += random.uniform(-self.markov_amplitude, self.markov_amplitude) 
                self.current_wind_angle += (self.base_wind_angle - self.current_wind_angle) * 0.05
            else:
                self.current_wind_angle = self.base_wind_angle

            wind_x = math.cos(self.current_wind_angle) * self.wind_speed_base 
            wind_y = math.sin(self.current_wind_angle) * self.wind_speed_base

            self.fbos[dest_idx].use() 
            self.ctx.viewport = (0, 0, self.config.grid_width, self.config.grid_height)
            self.step_program["u_grid_size"].value = (self.config.grid_width, self.config.grid_height)
            self.step_program["u_wind"].value = (wind_x, wind_y)
            self.step_program["u_time"].value = float(self.frame_count)
            self.step_program["u_beta"].value = self.beta
            self.step_program["u_gamma"].value = self.gamma
            self.step_program["u_pavesas_prob"].value = self.pavesas_prob

            self.textures[source_idx].use(location=0)
            self.step_program["u_texture"].value = 0
            self.step_vao.render(moderngl.TRIANGLES)

            self.current_texture_idx = dest_idx
        finally:
            self.doneCurrent()

        self.update()

    # usuario para activar o bloquear cÃ©lulas, y convertir coordenadas de pÃ­xeles a 
    # coordenadas de cuadrÃ­cula. Estos mÃ©todos permiten controlar la simulaciÃ³n, modificar 
    # el estado de la cuadrÃ­cula en respuesta a la interacciÃ³n del usuario, y actualizar 
    # las mÃ©tricas que se muestran en la interfaz grÃ¡fica.

    def reset_state(self): 
        if self.ctx is None:
            return

        self.makeCurrent()
        try:
            target_width, target_height = self._target_grid_size_for_current_map()
            rgba_grid = self._load_initial_map_rgba(target_width, target_height)
            self.config.grid_width = target_width
            self.config.grid_height = target_height
            self._ensure_sim_buffers_size(target_width, target_height)
            self._update_background_texture_for_map()
            self._write_state_rgba(rgba_grid)
            self._reapply_step_uniforms()
        finally:
            self.doneCurrent()

        self._emit_metrics_from_array(rgba_grid)
        self.update()

    def _load_initial_map_rgba(self, target_width: int, target_height: int) -> np.ndarray:
        artificial_map_factories = {
            "valdeiglesias.png": generate_valdeiglesias,
            "pedriza.png": generate_pedriza,
            "ontigola.png": generate_ontigola,
            "rivas.png": generate_rivas,
        }
        if self.custom_map_path is None and self.current_map_file in artificial_map_factories:
            rgba = artificial_map_factories[self.current_map_file](target_width, target_height)
            return np.flipud(rgba).astype(np.float32, copy=False)

        if self.custom_map_path is not None:
            map_path = Path(self.custom_map_path)
        else:
            map_path = Path(__file__).parent / "maps" / self.current_map_file

        if not map_path.exists():
            raise FileNotFoundError(f"No se encontro el mapa inicial: {map_path}")
        return self._load_rgba_from_image_path(map_path, target_width, target_height)

    def _load_rgba_from_image_path(self, image_path: Path, target_width: int, target_height: int) -> np.ndarray:
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((target_width, target_height), Image.BILINEAR)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        rgba_grid = np.array(img, dtype=np.float32) / 255.0
        if rgba_grid.ndim != 3 or rgba_grid.shape[2] != 4:
            raise ValueError("El mapa cargado no tiene 4 canales RGBA tras la conversiÃ³n")
        return rgba_grid

    def _ensure_sim_buffers_size(self, width: int, height: int):
        if not self.textures:
            self._create_sim_buffers(width, height)
            return

        current_size = self.textures[0].size
        if current_size[0] != width or current_size[1] != height:
            self._create_sim_buffers(width, height)

    def _load_bg_texture(self):
        maps_dir = Path(__file__).parent / "maps"
        bg_path = maps_dir / "guadarrama1_satelite.png"
        if not bg_path.exists():
            bg_path = maps_dir / "guadarrama1_satelite.jpg"
        if not bg_path.exists():
            bg_path = maps_dir / "guadarrama1_raster.png"
        if not bg_path.exists():
            bg_path = maps_dir / "guadarrama1_raster.jpg"
        if not bg_path.exists():
            self._release_bg_texture()
            return

        bg_img = Image.open(bg_path).convert("RGBA")
        bg_img = bg_img.resize((self.config.grid_width, self.config.grid_height), Image.BILINEAR)
        bg_img = bg_img.transpose(Image.FLIP_TOP_BOTTOM)

        bg_array = np.array(bg_img, dtype=np.float32) / 255.0

        self._release_bg_texture()
        self.bg_texture = self.ctx.texture(
            (self.config.grid_width, self.config.grid_height),
            4,
            bg_array.tobytes(),
            dtype="f4",
        )
        self.bg_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.bg_texture.repeat_x = False
        self.bg_texture.repeat_y = False

    def _release_bg_texture(self):
        if self.bg_texture is not None:
            self.bg_texture.release()
            self.bg_texture = None

    def _update_background_texture_for_map(self):
        if self._is_real_map_file(self.current_map_file):
            self._load_bg_texture()
            return
        self._release_bg_texture()

    def _is_real_map_file(self, map_file: str) -> bool:
        return map_file in self.REAL_MAP_FILES

    def _use_native_map_resolution(self) -> bool:
        # Los mapas reales y externos usan su resolucion nativa.
        # Los artificiales respetan grid_width/grid_height de config.
        return self.custom_map_path is not None or self._is_real_map_file(self.current_map_file)

    def _target_grid_size_for_current_map(self) -> tuple[int, int]:
        if not self._use_native_map_resolution():
            return self._artificial_grid_size

        cfg_w = max(1, int(self.config.grid_width))
        cfg_h = max(1, int(self.config.grid_height))

        map_path = self._resolve_current_map_path()
        if not map_path.exists():
            return cfg_w, cfg_h

        width, height = self._read_image_size(map_path)
        return max(1, int(width)), max(1, int(height))

    def _resolve_current_map_path(self) -> Path:
        if self.custom_map_path is not None:
            return Path(self.custom_map_path)
        return Path(__file__).parent / "maps" / self.current_map_file

    def _read_image_size(self, image_path: Path) -> tuple[int, int]:
        with Image.open(image_path) as img:
            return img.size

    def _write_state_rgba(self, rgba_grid: np.ndarray):
        self.textures[0].write(rgba_grid.tobytes(), alignment=1)
        self.textures[1].write(rgba_grid.tobytes(), alignment=1)
        self.current_texture_idx = 0
        self.frame_count = 0
        self.current_wind_angle = self.base_wind_angle
        self._fire_out_reported = False

    def _reapply_step_uniforms(self):
        if self.step_program is None:
            return
        self.step_program["u_grid_size"].value = (self.config.grid_width, self.config.grid_height)
        self.step_program["u_beta"].value = self.beta
        self.step_program["u_gamma"].value = self.gamma
        self.step_program["u_pavesas_prob"].value = self.pavesas_prob

    def _emit_metrics_from_array(self, array: np.ndarray):
        red = array[:, :, 0]
        blue = array[:, :, 2]

        infected = np.count_nonzero(red > 0.0)
        susceptible = np.count_nonzero((red == 0.0) & (blue > 0.0))
        recovered = np.count_nonzero((red == 0.0) & (blue == 0.0))

        total = self.config.grid_width * self.config.grid_height
        if total <= 0:
            return

        susceptible_pct = (susceptible / total) * 100.0
        infected_pct = (infected / total) * 100.0
        recovered_pct = (recovered / total) * 100.0
        self.metrics_updated.emit(susceptible_pct, infected_pct, recovered_pct, 0.0, self.frame_count)

    def set_pavesas_prob(self, value):
        self.pavesas_prob = max(0.0, min(0.05, float(value)))

    def set_wind_strength(self, value: int):
        self.wind_speed_base = float(value) / 10.0

    def set_wind_direction_degrees(self, degrees: int):
        self.base_wind_angle = math.radians(float(degrees))
        if not self.markov_wind:
            self.current_wind_angle = self.base_wind_angle

    def set_markov_wind_enabled(self, enabled: bool):
        self.markov_wind = bool(enabled)
        if not self.markov_wind:
            self.current_wind_angle = self.base_wind_angle

    def set_markov_amplitude(self, value: int):
        self.markov_amplitude = float(value) / 100.0

    def set_view_mode(self, index: int):
        self.view_mode = int(index)
        self.update()

    def set_beta(self, beta_value: float):
        self.beta = float(beta_value)

    def set_sim_timer(self, timer: QtCore.QTimer):
        self.sim_timer = timer

    def set_gamma(self, gamma_value: float):
        self.gamma = float(gamma_value)

    def set_tool_mode(self, tool_mode: str):
        self.selected_tool = tool_mode

    def load_map(self, map_name: str):
        map_names = {
            "Valdeiglesias (Pinar)": "valdeiglesias.png",
            "La Pedriza (MontaÃ±a)": "pedriza.png",
            "Mar de OntÃ­gola (Humedal)": "ontigola.png",
            "Mar de Ontigola (Humedal)": "ontigola.png",
            "Rivas (IUF)": "rivas.png",
            "Sierra de Guadarrama (Real)": "guadarrama1_real.png",
        }
        self.current_map_file = map_names.get(map_name, "valdeiglesias.png")
        self.custom_map_path = None

        if self.ctx is not None and self._is_initialized:
            self.reset_state()

    def load_custom_map(self, filepath: str):
        self.custom_map_path = filepath
        if self.ctx is not None and self._is_initialized:
            self.reset_state()

    def update_sir_metrics(self):
        if not self._is_initialized or self.ctx is None:
            return

        self.makeCurrent()
        try:
            current_fbo = self.fbos[self.current_texture_idx]
            data = current_fbo.read(components=4, dtype="f4")
        finally:
            self.doneCurrent()

        array = np.frombuffer(data, dtype=np.float32).reshape(
            (self.config.grid_height, self.config.grid_width, 4)
        )

        red = array[:, :, 0]
        blue = array[:, :, 2]

        infected = np.count_nonzero(red > 0.0)
        susceptible = np.count_nonzero((red == 0.0) & (blue > 0.0))
        recovered = np.count_nonzero((red == 0.0) & (blue == 0.0))

        if self.frame_count > 50 and infected == 0:
            if self.sim_timer is not None and self.sim_timer.isActive():
                self.sim_timer.stop()

            if not self._fire_out_reported:
                print("Incendio Extinguido")
                self._fire_out_reported = True
                self.fire_extinguished.emit()

        total = self.config.grid_width * self.config.grid_height
        if total <= 0:
            return

        susceptible_pct = (susceptible / total) * 100.0
        infected_pct = (infected / total) * 100.0
        recovered_pct = (recovered / total) * 100.0

        # Cálculo de la velocidad de simulación real en it/s
        now = time.time()
        elapsed = now - self.last_metrics_time
        frames_diff = self.frame_count - self.last_frame_count
        actual_fps = frames_diff / elapsed if elapsed > 0 else 0.0

        self.last_frame_count = self.frame_count
        self.last_metrics_time = now

        self.metrics_updated.emit(susceptible_pct, infected_pct, recovered_pct, actual_fps, self.frame_count)

    def activate_cell(self, x: int, y: int):
        self._paint_cell(x, y, self.activate_program, self.activate_vao, "u_cell_coord")

    def block_cell(self, x: int, y: int):
        self._paint_cell(x, y, self.block_program, self.block_vao, "u_cell_coord")

    def _paint_selected_tool(self, grid_x: int, grid_y: int):
        if self.selected_tool == "firebreak":
            self.block_cell(grid_x, grid_y)
            return
        self.activate_cell(grid_x, grid_y)

    def _paint_cell(self, x: int, y: int, program, vao, coord_uniform: str):
        if not self._is_initialized:
            return

        self.makeCurrent()
        try:
            source_idx = self.current_texture_idx
            dest_idx = 1 - source_idx

            self.fbos[dest_idx].use()
            self.ctx.viewport = (0, 0, self.config.grid_width, self.config.grid_height)
            program["u_grid_size"].value = (self.config.grid_width, self.config.grid_height)
            program[coord_uniform].value = (x, y)

            self.textures[source_idx].use(location=0)
            program["u_state_texture"].value = 0
            vao.render(moderngl.TRIANGLES)
            self.current_texture_idx = dest_idx
        finally:
            self.doneCurrent()

        self.update()

    def mousePressEvent(self, event):
        grid_x, grid_y = self._pixel_to_grid(event.position().x(), event.position().y())
        if not (0 <= grid_x < self.config.grid_width and 0 <= grid_y < self.config.grid_height):
            return

        if event.button() == QtCore.Qt.LeftButton:
            self._paint_selected_tool(grid_x, grid_y)
            return

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return

        grid_x, grid_y = self._pixel_to_grid(event.position().x(), event.position().y())
        if not (0 <= grid_x < self.config.grid_width and 0 <= grid_y < self.config.grid_height):
            return

        self._paint_selected_tool(grid_x, grid_y)

    def _pixel_to_grid(self, px: float, py: float) -> tuple[int, int]:
        if self.width() <= 0 or self.height() <= 0:
            return 0, 0

        vp_x, vp_y, vp_w, vp_h = self._display_viewport

        gl_y = self.height() - py
        if px < vp_x or px >= (vp_x + vp_w) or gl_y < vp_y or gl_y >= (vp_y + vp_h):
            return -1, -1

        rel_x = (px - vp_x) / vp_w
        rel_y = (gl_y - vp_y) / vp_h

        gx = int(rel_x * self.config.grid_width)
        gy = int(rel_y * self.config.grid_height)
        gx = max(0, min(gx, self.config.grid_width - 1))
        gy = max(0, min(gy, self.config.grid_height - 1))
        return gx, gy
