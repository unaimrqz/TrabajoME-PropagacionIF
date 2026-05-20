# Simulación de Propagación de Incendios Forestales (SIR)

Este repositorio contiene el código de una simulación interactiva de propagación de incendios forestales basada en Autómatas Celulares utilizando el modelo SIR (Susceptible, Infectado, Recuperado). El proyecto forma parte del trabajo de la asignatura de **Mecánica Estadística** (4º curso).

## Descripción

El proyecto implementa un autómata celular acelerado por GPU (Graphics Processing Unit) para simular la propagación del fuego en diferentes terrenos y ecosistemas. Utiliza mapas topográficos o de vegetación específicos y calcula el avance del fuego en tiempo real utilizando *shaders* para un rendimiento óptimo.

### Características Principales

*   **Modelo Computacional SIR:** Implementación del modelo epidemiológico adaptado a la quema de vegetación (Bosque sano = Susceptible, Fuego = Infectado, Quemado = Recuperado/Vacío).
*   **Aceleración por GPU:** La simulación se ejecuta directamente en la tarjeta gráfica utilizando `ModernGL` y *shaders* de OpenGL (`GLSL`), permitiendo emular cuadrículas masivas de forma instantánea.
*   **Interfaz Gráfica (GUI):** Interfaz completa y dinámica construida con `PySide6` (Qt para Python) que permite configurar parámetros de simulación al vuelo, visualizar el terreno, y controlar el desarrollo del fuego (Pausar, reanudar, reiniciar).
*   **Generación de Mapas:** Soporte para cargar y procesar mapas reales mediante `map_generator.py` (ej. Ontígola, La Pedriza, Rivas, San Martín de Valdeiglesias).
*   **Múltiples Estados del Shader:** Lógica compleja distribuida en distintos archivos `.glsl` (visualización, propagación/step, bloqueo/activación de celdas).

## Estructura del Proyecto

```text
PropagacionIF/
├── environment.yml                  # Configuración del entorno de dependencias (Conda/Mamba)
├── references/                      # Documentación y referencias bibliográficas del proyecto
│   ├── bomberos_if/
│   └── mecanica_estadistica/
└── simulations/
    ├── IF/                          # Código principal de la aplicación
    │   ├── main.py                  # Punto de entrada de la aplicación
    │   ├── main_window.py           # Gestión gráfica interactiva (PySide6)
    │   ├── grid_widget.py           # Renderizado OpenGL y bucle de simulación principal
    │   ├── config.py                # Ajustes y parámetros del modelo general
    │   ├── map_generator.py         # Módulo para crear o cargar mapas topográficos predefinidos
    │   ├── maps/                    # Mapas y recursos 
    │   └── shaders/                 # Programas GLSL para cálculos de CA en la GPU
    └── legacy/                      # Archivos de la versión inicial en CPU y Automatas Celulares previos
```

## Requisitos y Configuración del Entorno

Esta aplicación requiere las siguientes librerías principales:
- `PySide6`
- `moderngl`
- `numpy`
- `Pillow` (PIL)

Puedes preparar el entorno fácilmente mediante *Conda* usando el archivo `environment.yml` provisto:

```bash
conda env create -f environment.yml
conda activate incendios_env
```

## Uso

Para lanzar la interfaz de la simulación, ubícate en el directorio base del entorno y ejecuta:

```bash
python simulations/IF/main.py
```

Desde la GUI podrás interactuar con la redecilla de estados, cambiar mapas o modificar ratios de propagación.

## Desarrollo y Legado

Este proyecto evoluciona de modelos previos de autómatas celulares generados para TFG (ej. modelo de Greenberg-Hastings). Dichos recursos explorísticos de versiones anteriores y borradores se encuentran preservados bajo la carpeta `simulations/legacy/`.
