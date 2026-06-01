# Simulación de Propagación de Incendios Forestales (SIR) en GPU

Este repositorio contiene un simulador interactivo de propagación de incendios forestales basado en Autómatas Celulares (CA) acelerados por GPU. El proyecto ha sido desarrollado como entregable principal para la asignatura de **Mecánica Estadística** (4º curso del Grado en Física, Universidad Autónoma de Madrid).

## Contexto Académico

* **Institución:** Universidad Autónoma de Madrid (UAM)
* **Asignatura:** Mecánica Estadística (Grado en Física)
* **Autor:** Unai Márquez Sánchez
* **Mentor del motor base:** Ander (autor del núcleo de renderizado en GPU)

---

## Fundamentos Físicos y Matemáticos del Modelo

El simulador implementa un autómata celular estocástico que acopla el modelo epidemiológico SIR tradicional con dinámicas termodinámicas y de viento:

1. **Modelo SIR en Redes:**
   * **Susceptible ($S$):** Celdas con vegetación intacta (combustible disponible). Representado en el canal verde.
   * **Infectado ($I$):** Celdas en combustión activa (fuego). Representado en el canal rojo.
   * **Recuperado ($R$):** Celdas consumidas (ceniza) o barreras inertes (cortafuegos). Su tasa de transición hacia susceptible es nula ($W(R \to S) = 0$), definiendo la naturaleza irreversible del estado absorbente del sistema.

2. **Transición de Fase y Criticidad (Percolación):**
   * El comportamiento macroscópico del incendio viene regido por el número reproductivo básico $R_0 = \beta / \gamma$, donde $\beta$ es la tasa de propagación por radiación/contacto y $\gamma$ es la tasa de consumo de combustible.
   * Modificando estos parámetros, el sistema experimenta una **transición de fase de segundo orden** en torno a un umbral crítico $R_c$. Por debajo de este valor ($R_0 < R_c$), el fuego se autoextingue rápidamente en islas locales de ceniza. Por encima ($R_0 > R_c$), el fuego percola y se propaga de forma global a todo el mapa.

3. **Viento como Proceso Estocástico (Langevin):**
   * El viento añade una deriva (*drift*) anisotropy en el contagio local.
   * La magnitud y dirección del viento se modelan dinámicamente mediante la **ecuación estocástica de Langevin** acoplada a un **proceso de Ornstein-Uhlenbeck**. Esto garantiza fluctuaciones realistas en torno a una velocidad y dirección medias sin discontinuidades bruscas.

4. **Propagación por Pavesas (Spotting):**
   * Incorporación de eventos de salto de fuego no locales. Las pavesas desprendidas por el incendio activo son arrastradas por el viento y pueden iniciar conatos secundarios a distancias considerables, modelados mediante una distribución de probabilidad de Poisson espacial.

---

## Arquitectura Computacional en GPU

Para permitir la simulación interactiva de mallas de gran resolución en tiempo real, el simulador evita el cuello de botella de la CPU paralelizando el algoritmo en la tarjeta gráfica:

* **Shaders de OpenGL (GLSL):** La lógica de actualización del autómata celular se ejecuta de forma *embarrassingly parallel* en un Fragment Shader (`step.glsl`), calculando el nuevo estado de cada celda a partir de sus vecinas de Moore simultáneamente.
* **Ping-Pong Rendering (Doble Buffer):** Para evitar condiciones de carrera de lectura/escritura en la GPU, se utilizan dos Framebuffer Objects (FBO) en alternancia. En cada paso de tiempo, un buffer actúa como lectura (estado actual $t$) y el otro como escritura (estado futuro $t+\Delta t$).
* **Codificación RGBA:** La información de cada celda se empaqueta en los canales de color de una textura de entrada:
  * **R (Rojo):** Estado de combustión (Fuego/Infección).
  * **G (Verde):** Densidad de vegetación disponible.
  * **B (Azul):** Presencia de celdas bloqueadas (cortafuegos manuales u orografía inaccesible).
  * **A (Alfa):** Información de alturas topográficas para el gradiente de pendiente.

---

## Estructura del Repositorio

```text
PropagacionIF/
├── LICENSE                         # Archivo de licencia MIT
├── environment.yml                 # Dependencias del entorno Conda
├── references/                     # Literatura científica y de protección civil
└── simulations/
    ├── IF/                         # Código de la aplicación en producción
    │   ├── main.py                 # Punto de entrada de la GUI
    │   ├── main_window.py          # Interfaz gráfica interactiva (PySide6)
    │   ├── grid_widget.py          # Enlace ModernGL y bucle de simulación
    │   ├── config.py               # Estructuras de datos de configuración
    │   ├── map_generator.py        # Procesador de mapas sintéticos y reales
    │   ├── maps/                   # Texturas y mapas topográficos (La Pedriza, etc.)
    │   └── shaders/                # Algoritmos paralelos GLSL (step, display...)
    └── legacy/                     # Código legado de autómatas celulares previos
```

---

## Requisitos y Configuración

La simulación requiere Python 3.10+ y dependencias científicas/gráficas estándar. 

### Instalación con Conda

Crea y activa el entorno virtual utilizando el archivo `environment.yml` adjunto:

```bash
conda env create -f environment.yml
conda activate incendios_env
```

### Ejecución de la Aplicación

Para iniciar el simulador interactivo con interfaz gráfica en tiempo real:

```bash
python simulations/IF/main.py
```

---

## Características de la GUI Interactiva

La interfaz de usuario construida en `PySide6` proporciona controles para experimentar con el sistema en tiempo real:
* **Sliders Dinámicos:** Modificación al vuelo de la tasa de contagio $\beta$, tasa de decaimiento $\gamma$, velocidad media del viento y su dirección.
* **Pintado en Vivo:** Dibuja cortafuegos (botón central del ratón/rueda) o enciende focos de fuego (botón izquierdo) directamente sobre el mapa durante la simulación.
* **Modos de Visualización:** Cambia entre vista SIR (fuego/vegetación), orografía, combustibles o mapa satélite rasterizado.
* **Escenarios Reales y Sintéticos:** Carga automática de perfiles de la Comunidad de Madrid (Pinar de Valdeiglesias, Montaña de La Pedriza, Humedal del Mar de Ontígola, Interfaz Urbano-Forestal de Rivas) o mapas personalizados.

---

## Autoría y Atribuciones

* **Desarrollo y Modelo SIR:** **Unai Márquez Sánchez** (estudiante de Física, UAM).
* **Base Tecnológica de Autómatas en GPU:** Este proyecto es una evolución directa de un desarrollo previo de **Ander**, quien diseñó el motor gráfico base en ModernGL y la estructura de buffers paralelos. Agradecemos enormemente su guía y la cesión de la infraestructura inicial.

## Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para ver los detalles de los derechos y exención de garantías de uso de este software.
