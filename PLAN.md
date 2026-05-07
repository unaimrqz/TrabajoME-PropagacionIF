# PLAN DE PROYECTO: Wildfire-Madrid-GPU 🌲🔥

## 1. VISIÓN GENERAL
Software de simulación táctica en tiempo real de incendios forestales basado en un modelo SIR modificado. Ejecutado en GPU (GLSL Shaders) e interfaz en Python (PySide). Diseñado para una presentación de 15 minutos destacando la Mecánica Estadística (Transiciones de Fase, Longitud de Correlación, Cadenas de Markov) aplicada a 4 escenarios reales de la Comunidad de Madrid.

## 2. DICCIONARIO DE DATOS (Textura GPU - RGBA)
Cada píxel de la textura de simulación representa un autómata celular:
*   **Canal R (Rojo) -> ESTADO SIR:** 0.0 (Susceptible), 1.0 (Infectado/Ardiendo), > 0.0 & < 1.0 (Recuperado/Ceniza).
*   **Canal G (Verde) -> OROGRAFÍA / ELEVACIÓN:** 0.0 a 1.0 representa la altura del terreno. Permite calcular el gradiente de pendiente.
*   **Canal B (Azul) -> TIPO DE COMBUSTIBLE / BARRERAS:** 
    *   `0.0`: Agua / Asfalto (Barrera R inmutable).
    *   `0.2`: Pasto / Carrizo ($\gamma$ alto, fuego rápido).
    *   `0.5`: Matorral / Coscoja (IUF).
    *   `0.8`: Pino silvestre.
    *   `1.0`: Pino piñonero (Alta HRR, Pavesas).
    *   `> 1.0` (o usando canal Alpha): Zonas urbanas/Casas a proteger.

## 3. LÓGICA FÍSICA DEL SHADER
*   **$\beta$ (Contagio/Propagación):** Modificado por el Viento (vector direccional) y la Pendiente (gradiente del canal G).
*   **$\gamma$ (Consumo):** Depende del canal B (combustible).
*   **Pavesas (Non-local interaction):** Si el canal B indica "Pino piñonero", se lee un píxel aleatorio a distancia `d` en la dirección del viento para simular saltos de fuego.

## 4. SPRINTS Y ESTADO DE TAREAS

### SPRINT 1: Limpieza y Setup Base [COMPLETADO]
- [x] Tarea 1.1: Eliminar código residual.
- [x] Tarea 1.2: Solucionar error `u_grid_size` y estabilizar arranque.
- [x] Tarea 1.3: Conectar clicks de ratón (Fuego y Cortafuegos).

### SPRINT 2: Motor Físico (El GLSL Shader) [EN PROGRESO]
- [x] Tarea 2.1: Implementar lógica SIR en `step.glsl`.
- [x] Tarea 2.2: Implementar el Viento en `step.glsl`.
- [x] Tarea 2.3: Actualizar `display.glsl` para visualización.
- [x] Tarea 2.4: Implementar Topografía. Usar el canal G (Verde) como elevación. Si la celda actual es más alta que la celda vecina en llamas, el contagio se multiplica drásticamente (el fuego sube laderas muy rápido por convección).
- [x] Tarea 2.5: Implementar "Pavesas" (saltos de fuego). Si el viento es fuerte y el combustible es Pino Piñonero (Canal B >= 0.9), el fuego puede saltar a gran distancia a favor del viento usando una función pseudoaleatoria (Proceso estocástico en GPU).
### SPRINT 2: Motor Físico (El GLSL Shader) [COMPLETADO]
- [x] Tarea 2.1: Implementar lógica SIR en `step.glsl`.
- [x] Tarea 2.2: Implementar el Viento en `step.glsl`.
- [x] Tarea 2.3: Actualizar `display.glsl` para visualización.
- [x] Tarea 2.4: Implementar Topografía (Pendientes).
- [x] Tarea 2.5: Implementar "Pavesas" (saltos de fuego).

### SPRINT 3: Dinámica Estocástica y Cuantificación [COMPLETADO]
- [x] Tarea 3.1: Naturalidad del Frente de Llama.
- [x] Tarea 3.2: Cadena de Markov para el viento.
- [x] Tarea 3.3: Cuantificación del modelo SIR (Métricas).

### SPRINT 4: Escenarios de Madrid y Fix de UI [COMPLETADO]
- [x] Tarea 4.1: Fix UI (Layout y etiquetas SIR).
- [x] Tarea 4.2: Generador de mapas topográficos y de combustible.
- [x] Tarea 4.3: Carga dinámica de imagen PNG inicial.

### SPRINT 4: Escenarios de Madrid y Fix de UI [COMPLETADO]
- [x] Tarea 4.1, 4.2, 4.3: Mapas base y UI arreglada.

### SPRINT 5: Puesto de Mando Avanzado (Panel UI) [COMPLETADO]
- [x] Tarea 5.1 a 5.4: Controles básicos de Viento, Pavesas y Herramientas tácticas integrados.

### SPRINT 6: Cuantificación Física y Control Total [EN PROGRESO]
- [x] Tarea 6.1: Mostrar Valores Numéricos. Añadir etiquetas dinámicas al lado de los sliders (ej. "Viento: 25 km/h").
- [x] Tarea 6.2: Control del Viento Completo. Añadir un `QSlider` (0-360) para la Dirección del Viento. Añadir un `QCheckBox` "Viento Estocástico (Markov)" para alternar entre viento constante (pide el profe) y viento caótico (realidad).
- [x] Tarea 6.3: Parámetros SIR en vivo. Añadir sliders para $\beta$ (Tasa de Contagio / Calor) y $\gamma$ (Tasa de Consumo). Conectarlos a uniforms en el shader para responder a la pregunta de evaluación del proyecto ("¿Para qué valores es más peligroso?").


### SPRINT 7: Pulido Físico, Topografía y Mapas [COMPLETADO]
- [x] Tarea 7.1: Fix Pavesas. Eliminar la restricción de combustible en `step.glsl` y hacer que la probabilidad dependa de $\beta$.
- [x] Tarea 7.2: Fix Markov. Aumentar la amplitud del Random Walk en `grid_widget.py` a $\pm 0.5$ radianes para que la turbulencia sea visible.
- [x] Tarea 7.3: Shader Topográfico. En `display.glsl`, añadir un algoritmo que dibuje "curvas de nivel" leyendo los saltos en el canal G (Elevación).
- [x] Tarea 7.4: Preparación para Google Earth. Explicar el formato para cargar mapas custom.

### SPRINT 8: Fix de Magnitudes Físicas y Sistema de Capas [COMPLETADO]
- [x] Tarea 8.1: Corregir magnitud del Desnivel. En `step.glsl`, aumentar drásticamente el multiplicador de `slope` y dividirlo por el tamaño del píxel para calcular el gradiente real y que el fuego vuele montaña arriba.
- [x] Tarea 8.2: Corregir artefactos en Pavesas. Arreglar la semilla del `rand()` en `step.glsl` para que los focos secundarios no creen patrones matemáticos raros.
- [x] Tarea 8.3: Sistema de Vistas (Capas). En `main_window.py`, añadir un `QComboBox` llamado "Vista de Satélite / Mapa" con opciones: "Modo SIR (Táctico)", "Orografía (Elevación)", "Combustible". Pasar esta variable al shader `display.glsl` para alternar colores sin alterar la física.

### SPRINT 9: Calibración y Pavesas en Abanico (Scatter) [COMPLETADO]
- [x] Tarea 9.1: UI de Pavesas. En `main_window.py`, cambiar el CheckBox de Pavesas por un `QSlider` (0-100) llamado "Probabilidad de Pavesas", mapeado a un uniform `u_pavesas_prob` de 0.0 a 0.05.
- [x] Tarea 9.2: Dispersión Estocástica (Cone Scatter). En `step.glsl`, modificar el vector de búsqueda de pavesas. Aplicar una matriz de rotación con un ángulo aleatorio (±30 grados) y una distancia aleatoria, para que las pavesas caigan en forma de abanico y no en línea recta.
- [x] Tarea 9.3: Calibrar Presets. En `main_window.py`, bajar drásticamente los valores por defecto de $\beta$ en los presets de los mapas (ej. 0.5 a 1.5 máximo) para evitar el "efecto flecha determinista".

### SPRINT 8.5: Renormalización Física y Auto-Stop [COMPLETADO]
- [x] Tarea 8.5.1: Calibración Estocástica de $\beta$. Modificar el slider de $\beta$ en `main_window.py` para que su máximo represente "Sequedad Extrema" limitando el valor enviado al shader a un máximo de `1.2`. Así garantizamos que el fuego siempre se mantenga en el régimen caótico/fractal y no sature la probabilidad al 100%.
- [x] Tarea 8.5.2: Auto-Stop del Modelo SIR. En `grid_widget.py`, añadir una lógica dentro de `update_sir_metrics`: si los frames simulados son mayores a 50 y los Infectados (I) llegan a 0, detener automáticamente la ejecución (pausar el timer de simulación).

### SPRINT 10: Pulido Académico y Calibración Final [COMPLETADO]
- [x] Tarea 10.1 (antes 9.1): Renombrar etiquetas UI. La interfaz muestra explícitamente "Parámetro β (Tasa de Contagio / Sequedad)", "Parámetro γ (Tasa de Consumo / Finura)" y "Focos Secundarios (Pavesas) [Extra]" para enlazar con el enunciado académico.
- [x] Tarea 10.2 (antes 9.2): Calibración fina de presets. En `main_window.py`, se reducen los valores por defecto de $\beta$ y se fijan las pavesas a 0 en todos los escenarios para preservar la física local y la estocasticidad visible.

### SPRINT 11: UI del Mundo Real (Traducción Física) [COMPLETADO]
- [x] Tarea 11.1: Renombrar etiquetas al texto exacto del enunciado. Cambiar la UI para que diga "Capacidad de contagio (β)" y "Tasa de recuperación (γ / Consumo de madera)".
- [x] Tarea 11.2: Traducción Matemática-Realidad en vivo. Modificar `main_window.py` para que, al mover los sliders, el texto muestre el valor matemático seguido de su interpretación física real en base al enunciado.
  - Para $\beta$: Mostrar la "Humedad del terreno (%)" inversamente proporcional al slider.
  - Para $\gamma$: Mostrar el "Tiempo de llama (minutos)", calculado como $1 / \gamma$.

  ### SPRINT 12: Integración de Mapas Reales GIS (Topografía y NDVI) [COMPLETADO]
- [x] Tarea 12.1: Script de Fusión RGBA. En `map_generator.py`, crear la función `generate_from_real_maps` para leer mapas crudos en escala de grises (MDT y vegetación) y empaquetarlos en la textura que requiere el Shader.
- [x] Tarea 12.2: Inyección de datos GIS. Usar capturas tratadas de QGIS (`guadarrama1_height.jpg` y `guadarrama1_fuel.jpg`) inyectando el Modelo Digital del Terreno en el canal Verde y el Índice de Combustible en el canal Azul.
- [x] Tarea 12.3: UI del Nuevo Escenario. Añadir "Sierra de Guadarrama (Real)" a la interfaz, permitiendo al usuario probar la Mecánica Estadística del fuego sobre un entorno asimétrico y topográficamente exacto.

### SPRINT 13: Fotorrealismo y Geometría Dinámica [COMPLETADO]
- [x] Tarea 13.1: Evitar deformación geométrica. Modificar `map_generator.py` para que respete el Aspect Ratio (ancho x alto) original de los mapas GIS de entrada, evitando artefactos en la propagación diagonal.
- [x] Tarea 13.2: Redimensionamiento Dinámico en GPU. Actualizar `grid_widget.py` para que reconfigure `u_grid_size` al vuelo dependiendo de las proporciones del mapa PNG cargado.
- [x] Tarea 13.3: Textura Visual Satelital. Cargar en paralelo (location=1) el mapa raster satelital (`guadarrama1_raster.jpg`).
- [x] Tarea 13.4: Renderizado Dinámico sobre Satélite. Modificar `display.glsl` para mostrar la fotografía real del satélite debajo del fuego, oscureciéndola (cenizas) donde el modelo físico indique que el combustible se ha agotado.