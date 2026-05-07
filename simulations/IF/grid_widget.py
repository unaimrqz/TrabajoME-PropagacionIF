# grid_widget.py
# Es el motor de la simulación: aquí es donde se realiza toda la lógica de renderizado,
# simulación, y manejo de la interacción del usuario. Este widget se encarga de crear el 
# contexto de OpenGL, cargar los shaders, configurar las texturas y FBOs para almacenar 
# el estado de la simulación, y ejecutar el ciclo principal de la simulación en la GPU.
# También maneja la interacción del usuario para activar o bloquear células, y actualiza 
# las métricas de SIR que se muestran en la interfaz gráfica.


from pathlib import Path                                    # para cuando se necesite cargar archivos, como los shaders o los mapas iniciales
import math                                                 # ¿Por qué math y no numpy? Porque math es más rápido para operaciones escalares, y aquí solo necesitamos funciones trigonométricas para el viento, no operaciones vectoriales complejas.
import random                                               # ¿Por qué random y no numpy.random? Porque random es más simple y suficiente para generar variaciones de viento, no necesitamos la funcionalidad avanzada de numpy.random para esto.

import moderngl                                             # Moderngl es un wrapper (un wrapper es ) de OpenGL para Python que facilita la creación de gráficos acelerados por hardware. Nos permite escribir shaders personalizados para simular el comportamiento del fuego y renderizarlo eficientemente en la GPU.
import numpy as np 
from PIL import Image                                       # para cargar mapas iniciales desde archivos de imagen, convertirlos a RGBA y luego a arrays de numpy que podemos subir como texturas a la GPU.
from PySide6 import QtCore                                  # para señales, slots, temporizadores y manejo de eventos en la interfaz gráfica
from PySide6.QtOpenGLWidgets import QOpenGLWidget           # QOpenGLWidget es un widget de Qt que nos permite renderizar gráficos usando OpenGL. Es la base sobre la que construiremos toda la simulación visual del fuego, permitiéndonos aprovechar la potencia de la GPU para simular y renderizar el comportamiento del fuego en tiempo real.

from config import SimulationConfig                         # importamos la configuración de la simulación, que nos proporciona parámetros como el tamaño de la cuadrícula, las tasas de infección y recuperación, etc. Esta configuración se utilizará para inicializar el estado de la simulación y para controlar su comportamiento a lo largo del tiempo.
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
    metrics_updated = QtCore.Signal(float, float, float)
    fire_extinguished = QtCore.Signal()
    REAL_MAP_FILES = {"guadarrama1_real.png", "guadarrama_real.png"}

    def __init__(self, config: SimulationConfig): # En el constructor inicializamos todas las variables necesarias para la simulación, como los programas de shaders, los VAOs, las texturas, los FBOs, y otros parámetros relacionados con el viento y la visualización. También configuramos un temporizador para actualizar las métricas de SIR cada segundo.
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

        self.metrics_timer = QtCore.QTimer(self)
        self.metrics_timer.setInterval(1000)
        self.metrics_timer.timeout.connect(self.update_sir_metrics)
        self.metrics_timer.start()

    def initializeGL(self): # El método clave, donde configuramos el contexto de OpenGL, cargamos los shaders, creamos los VAOs para renderizar un cuadrado que cubre toda la pantalla, y configuramos las texturas y FBOs para almacenar el estado de la simulación. También cargamos el mapa inicial y lo escribimos en las texturas para comenzar la simulación.
        self.ctx = moderngl.create_context() # Creamos el contexto de OpenGL, que es necesario para cualquier operación gráfica. Este contexto nos permitirá crear shaders, texturas, buffers y realizar renderizado en la GPU.

        # Cargamos los shaders desde archivos GLSL. Estos shaders son programas que se ejecutan en la GPU para realizar el renderizado y la simulación del fuego. El shader de vértices es común para todos, mientras que los shaders de fragmentos son específicos para cada etapa de la simulación (renderizado, paso de simulación, activación de células, bloqueo de células).
        vertex_source = load_shader_source("shaders/vertex.glsl")
        display_source = load_shader_source("shaders/display.glsl")
        step_source = load_shader_source("shaders/step.glsl")
        activate_source = load_shader_source("shaders/activate_cell.glsl")
        block_source = load_shader_source("shaders/block_cell.glsl")

        # Creamos los programas de shaders a partir del código fuente cargado. Cada programa de shader se compila y se vincula, y luego podemos usarlo para renderizar o simular el fuego. El programa de display se usará para renderizar la cuadrícula en la pantalla, el programa de step se usará para calcular el siguiente estado de la simulación, y los programas de activate y block se usarán para modificar el estado de células individuales cuando el usuario interactúe con la cuadrícula.
        self.display_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=display_source)
        self.step_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=step_source)
        self.activate_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=activate_source)
        self.block_program = self.ctx.program(vertex_shader=vertex_source, fragment_shader=block_source)

        # Creamos un VAO (Vertex Array Object) para cada programa de shader. El VAO define cómo se deben interpretar los datos de vértices que le pasamos. En este caso, estamos creando un cuadrado que cubre toda la pantalla, con coordenadas de vértices que van de -1 a 1 en ambas direcciones. Este cuadrado se usará para renderizar la simulación y para aplicar los shaders de paso, activación y bloqueo a toda la cuadrícula.
        vertices = np.array([-1, -1, 1, -1, 1, 1, -1, 1], dtype="f4") #  hay en total 4 vértices, cada uno con 2 componentes (x e y), que forman un cuadrado que cubre toda la pantalla. Las coordenadas van de -1 a 1 porque en OpenGL, el espacio de coordenadas normalizado para el renderizado va de -1 a 1 en ambas direcciones.
        indices = np.array([0, 1, 2, 0, 2, 3], dtype="i4") # Estos índices definen dos triángulos que forman el cuadrado. El primer triángulo está formado por los vértices 0, 1 y 2, y el segundo triángulo está formado por los vértices 0, 2 y 3. Esto es necesario porque OpenGL renderiza en términos de triángulos, así que necesitamos dividir nuestro cuadrado en dos triángulos para poder renderizarlo correctamente.
        vbo = self.ctx.buffer(vertices) 
        ebo = self.ctx.buffer(indices)

        # Creamos un VAO para cada programa de shader, usando el mismo VBO (vertices) y EBO (índices). Esto nos permite usar el mismo conjunto de vértices para renderizar con diferentes shaders, lo que es eficiente y conveniente. Cada VAO se configura para interpretar los datos del VBO como pares de floats (2f) que corresponden a la variable de entrada "aPos" en los shaders.
        self.display_vao = self.ctx.vertex_array(self.display_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.step_vao = self.ctx.vertex_array(self.step_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.activate_vao = self.ctx.vertex_array(self.activate_program, [(vbo, "2f", "aPos")], index_buffer=ebo)
        self.block_vao = self.ctx.vertex_array(self.block_program, [(vbo, "2f", "aPos")], index_buffer=ebo)

        self._create_sim_buffers(self.config.grid_width, self.config.grid_height)

        self.reset_state() # Carga el mapa inicial y lo escribe en las texturas para comenzar la simulación. Esto asegura que cuando la aplicación se inicie, ya tengamos un estado inicial de la simulación cargado y listo para ser renderizado y simulado.
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

    # El método paintGL se llama cada vez que la ventana necesita ser redibujada. En este método, configuramos el framebuffer para renderizar, limpiamos la pantalla con un color de fondo, y luego usamos el programa de display para renderizar la textura actual de la simulación en la pantalla. Esto nos permite ver el estado actual del fuego en la cuadrícula.
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

        # Conversión a píxeles reales del framebuffer para evitar errores HiDPI.
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

    # Es EL método: aquí es donde se realiza la lógica principal de la simulación. En cada paso, calculamos el nuevo estado de la simulación usando el shader de step, que toma como entrada la textura actual (estado actual) y produce una nueva textura (nuevo estado) basada en las reglas de propagación del fuego, el viento, y otros parámetros. Luego alternamos entre las texturas fuente y destino para el siguiente paso. Este método se llama repetidamente para avanzar la simulación a lo largo del tiempo.
    def step_once(self):
        if not self._is_initialized:
            return

        self.makeCurrent() # Usamos makeCurrent para asegurarnos de que el contexto de OpenGL esté activo antes de realizar cualquier operación gráfica. Esto es necesario porque podríamos tener múltiples widgets o contextos en la aplicación, y necesitamos asegurarnos de que estamos operando en el contexto correcto antes de renderizar o actualizar texturas. Al llamar a makeCurrent, nos aseguramos de que todas las operaciones gráficas que realizamos a continuación se apliquen al contexto de este widget específico.
        
        try:
            source_idx = self.current_texture_idx # el metodo current_texture_idx de donde sale? Es una variable de instancia que definimos en el constructor de la clase GridWidget. Esta variable se utiliza para llevar un seguimiento de cuál de las dos texturas (y sus correspondientes FBOs) estamos usando actualmente como fuente para la simulación. En cada paso de la simulación, alternamos entre las dos texturas, por lo que source_idx nos indica cuál es la textura actual que contiene el estado actual de la simulación, y dest_idx nos indica cuál es la textura destino donde vamos a escribir el nuevo estado calculado por el shader de step.
            dest_idx = 1 - source_idx # Al restar source_idx de 1, obtenemos el índice opuesto (si source_idx es 0, dest_idx será 1, y viceversa). Esto nos permite alternar entre las dos texturas de manera eficiente sin necesidad de usar condicionales adicionales. En cada paso de la simulación, renderizamos usando el shader de step para calcular el nuevo estado basado en la textura fuente (source_idx) y escribimos el resultado en la textura destino (dest_idx). Luego actualizamos current_texture_idx a dest_idx para que en el siguiente paso, la textura recién calculada se convierta en la nueva fuente.
            self.frame_count += 1 

            if self.markov_wind: 
                # En lugar de hacer aleatorio cada paso en un rango fijo, el proceso es:
                # 1. Tomamos el ángulo actual del viento (current_wind_angle).
                # 2. Le sumamos una pequeña variación aleatoria dentro del rago definido por markov_amplitude. 
                # 3. Le sumamos la resta entre el ángulo base del viento (base_wind_angle) y el ángulo actual, multiplicada por un factor de corrección (0.05 en este caso) que hace que el viento tienda a volver a su dirección base con el tiempo. Esto crea un efecto de "resorte" que evita que el viento se desvíe demasiado de su dirección base, pero aún así permite cierta variabilidad aleatoria en la dirección del viento a lo largo del tiempo, lo que simula un viento más realista y dinámico.
                self.current_wind_angle += random.uniform(-self.markov_amplitude, self.markov_amplitude) 
                self.current_wind_angle += (self.base_wind_angle - self.current_wind_angle) * 0.05 # Esta línea implementa un efecto de "resorte" que hace que el ángulo del viento tienda a volver a la dirección base con el tiempo. Al multiplicar la diferencia entre el ángulo base y el ángulo actual por 0.05, estamos aplicando una pequeña corrección en cada paso que hace que el viento no se desvíe demasiado de su dirección base, pero aún así permita cierta variabilidad aleatoria. Esto ayuda a simular un viento que cambia de dirección de manera realista sin volverse completamente errático. Si markov_wind está desactivado, simplemente mantenemos el ángulo del viento igual al ángulo base, lo que significa que el viento no cambiará de dirección a lo largo del tiempo.
            else:
                self.current_wind_angle = self.base_wind_angle

            # Calculamos las componentes x e y del viento:
            wind_x = math.cos(self.current_wind_angle) * self.wind_speed_base 
            wind_y = math.sin(self.current_wind_angle) * self.wind_speed_base

            # En lo que queda se configura el framebuffer destino para renderizar, 
            # se establecen los uniformes necesarios para el shader de step (como 
            # el tamaño de la cuadrícula, la dirección y velocidad del viento, el 
            # tiempo transcurrido, y los parámetros beta, gamma y pavesas_prob), 
            # se vincula la textura fuente (estado actual) para que el shader pueda
            # leerla, y luego se renderiza un cuadrado que cubre toda la pantalla
            # usando el shader de step. Esto hace que el shader de step se ejecute 
            # para cada píxel de la textura destino, calculando el nuevo estado de 
            # la simulación basado en el estado actual y las reglas definidas en el
            # shader. Finalmente, se actualiza current_texture_idx a dest_idx para
            # que en el siguiente paso, la nueva textura calculada se convierta en
            # la fuente para la siguiente iteración de la simulación.

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


    # De aquí en adelante, definimos métodos para reiniciar el estado de la simulación, 
    # cargar mapas iniciales, actualizar las métricas de SIR, manejar la interacción del 
    # usuario para activar o bloquear células, y convertir coordenadas de píxeles a 
    # coordenadas de cuadrícula. Estos métodos permiten controlar la simulación, modificar 
    # el estado de la cuadrícula en respuesta a la interacción del usuario, y actualizar 
    # las métricas que se muestran en la interfaz gráfica.

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
            raise ValueError("El mapa cargado no tiene 4 canales RGBA tras la conversión")
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
        self.metrics_updated.emit(susceptible_pct, infected_pct, recovered_pct)

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

    def set_beta(self, value: int):
        self.beta = (float(value) / 100.0) * 1.2

    def set_sim_timer(self, timer: QtCore.QTimer):
        self.sim_timer = timer

    def set_gamma(self, gamma_value: float):
        self.gamma = float(gamma_value)

    def set_tool_mode(self, tool_mode: str):
        self.selected_tool = tool_mode

    def load_map(self, map_name: str):
        map_names = {
            "Valdeiglesias (Pinar)": "valdeiglesias.png",
            "La Pedriza (Montaña)": "pedriza.png",
            "Mar de Ontígola (Humedal)": "ontigola.png",
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
        self.metrics_updated.emit(susceptible_pct, infected_pct, recovered_pct)

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
