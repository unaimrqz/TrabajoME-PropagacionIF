# Guía rápida de setup (Propagación de Incendios Forestales)

## 1) Estado actual detectado

- La raíz `Propagación de Incendios Forestales` **sí** tiene Git inicializado (`main`, sin commits todavía).
- El `.git` interno de `TFG-automatas-celulares` se apartó como backup en `.git_backup_20260304_160603`.
- Tienes bibliografía y enunciado en `referencias/` (PDFs).
- En Conda tienes detectados los entornos: `base` y `tfg_econofisica`.
- En VS Code se detectó que en PowerShell no está inicializado Conda/Python (por eso aparece "conda no se reconoce").

---

## 1.1) Mapa mental profesional (muy importante)

Piensa que hay 4 capas separadas:

1. **Git (versionado):** guarda historial de archivos y cambios.
2. **Entorno Python (Conda):** define qué Python y qué paquetes usa cada proyecto.
3. **Editor VS Code:** interfaz para trabajar (no "instala" Python por sí solo).
4. **Extensiones de VS Code:** añaden capacidades (autocompletado, notebooks, LaTeX, PDF...).

Si separas estas 4 capas en tu cabeza, desaparece el 80% del lío típico de inicio.

---

## 2) Repo dentro de repo: cómo evitar problemas

Cuando conviertas la raíz en repo, tener `TFG-automatas-celulares/.git` dentro puede dar conflictos (Git lo detecta como repositorio embebido).

### Opción A (recomendada para tu caso): unificar en un solo repo

Si quieres versionar todo junto (tu trabajo + referencias + código base), elimina el `.git` interno.

En tu caso ya está apartado como backup, así que no hace falta repetirlo.

Si quisieras borrarlo definitivamente más adelante:

```powershell
Remove-Item -Recurse -Force .\TFG-automatas-celulares\.git_backup_20260304_160603
```

Luego inicializa Git en la raíz:

```powershell
git add .
git commit -m "Inicio proyecto incendios forestales"
```

### Opción B: mantener `TFG-automatas-celulares` separado

Si quieres que siga siendo un repo independiente, en la raíz ignóralo:

```gitignore
/TFG-automatas-celulares/
```

### Opción C: submódulo (solo si quieres enlazarlo formalmente)

Úsalo si el código de tu amigo sigue evolucionando y quieres traer cambios de su remoto:

```powershell
git submodule add <url-del-repo-de-tu-amigo> TFG-automatas-celulares
```

---

## 3) Python y entorno

El proyecto `TFG-automatas-celulares` ya trae `environment.yml` (Conda, PySide6, ModernGL, NumPy, SciPy, pandas, Jupyter).

### ¿Qué es `environment.yml` y por qué es tan útil?

Es la "receta reproducible" del entorno del proyecto:

- `name`: nombre del entorno (`automatas_env`).
- `channels`: de dónde descarga paquetes (`conda-forge`, `defaults`).
- `dependencies`: paquetes Conda con versiones fijadas.
- `pip`: paquetes que Conda no gestiona directamente.

Sí, **es parecido a `requirements.txt`**, pero más completo:

- `requirements.txt` suele cubrir solo paquetes `pip`.
- `environment.yml` define también versión de Python y paquetes de sistema, por lo que replica mejor el entorno científico.

Nota: el campo `prefix` apunta al PC de tu compañero; para ti no es crítico.

### Crear entorno desde el YAML

```powershell
C:\Users\gshad\anaconda3\Scripts\conda.exe env create -f .\TFG-automatas-celulares\environment.yml
```

Si ya existe:

```powershell
C:\Users\gshad\anaconda3\Scripts\conda.exe env update -f .\TFG-automatas-celulares\environment.yml --prune
```

Activación (en terminal con Conda inicializado):

```powershell
conda activate automatas_env
```

Si PowerShell no reconoce `conda`, usa **Anaconda Prompt** o ejecuta una sola vez:

```powershell
C:\Users\gshad\anaconda3\Scripts\conda.exe init powershell
```

y reinicia VS Code.

### Ejecutar simulacion base (PySide + motor de shaders)

Ejemplo:

```powershell
python .\simulations\IF\main.py
```

Este ejecutable carga la ventana PySide y el motor base de shaders para la malla.

---

## 4) VS Code recomendado

Se añadió `.vscode/extensions.json` con extensiones sugeridas para:

- Python + Pylance
- Jupyter
- GitLens
- LaTeX Workshop
- Visor PDF en editor

Abre el workspace y acepta las recomendaciones de extensiones.

### ¿Qué hace `.vscode/extensions.json`?

Ese archivo **solo recomienda** extensiones al abrir este proyecto.

- No instala por fuerza.
- No cambia tu sistema operativo.
- Sirve para que cualquier persona (o tú en otro PC) sepa qué extensiones conviene tener para este repo.

Por eso se crea la carpeta `.vscode`: es configuración local del proyecto.

---

## 5) PDFs y figuras

- Puedes abrir directamente los PDFs de `referencias/` en VS Code.
- Para extraer notas rápidas por tema, crea un `resumen_*.md` al lado de cada PDF y enlaza figuras/páginas manualmente.

---

## 6) LaTeX

Si ya tenías LaTeX instalado, con LaTeX Workshop deberías poder compilar sin más.

Comprobación rápida:

```powershell
pdflatex --version
```

Si no aparece, instala TeX Live o MiKTeX y reinicia VS Code.

---

## 6.1) Jupyter y CUDA explicado sencillo

### Jupyter

Jupyter te permite trabajar en cuadernos (`.ipynb`) con:

- Texto explicativo
- Código Python
- Gráficas/salidas

Es ideal para explorar datos, probar ideas y documentar experimentos.

### CUDA

CUDA es una plataforma de NVIDIA para cálculo en GPU.

- Si un código está escrito para CUDA, puede acelerar mucho simulaciones.
- Pero no todo lo que usa GPU es CUDA.
- Tu proyecto base parece usar sobre todo OpenGL/ModernGL para computación/visualización en GPU.

Traducción práctica: puedes beneficiarte de GPU sin tener que entrar aún en CUDA puro.

---

## 6.2) Tu situación concreta (`tfg_econofisica`)

Tú ya tienes un entorno previo (`tfg_econofisica`) y eso está bien.

Regla profesional:

- **1 entorno por proyecto principal.**
- No mezclar paquetes de incendios dentro de `tfg_econofisica` si quieres reproducibilidad y menos errores.

Recomendación:

- Conserva `tfg_econofisica` para ese TFG anterior.
- Crea `automatas_env` (o `incendios_env`) para este proyecto.

---

## 7) Orden sugerido de trabajo (MVP)

1. Decidir Opción A/B/C de Git.
2. Crear/activar entorno Conda.
3. Verificar que corre al menos un `main_gpu_modern.py`.
4. Crear carpeta de trabajo propia (por ejemplo `incendios_modelo/`) para tu modelo.
5. Ir documentando hipótesis y resultados en Markdown/LaTeX.

---

## 8) Flujo profesional mínimo (día a día)

1. Abres VS Code en la raíz del proyecto.
2. Seleccionas intérprete Python del entorno del proyecto.
3. Haces cambios pequeños.
4. Ejecutas y validas.
5. `git add .` + `git commit -m "mensaje claro"`.
6. `git push`.

Consejo clave: commits pequeños y frecuentes > commits gigantes cada varios días.

---

## 9) Formato de mapas custom (Google Earth / QGIS / imágenes propias)

La opción **"Cargar Mapa Externo..."** de la interfaz acepta `*.png`, `*.jpg` y `*.jpeg`.

El motor siempre hace estos pasos al cargar tu archivo:

1. Convierte la imagen a **RGBA**.
2. Redimensiona al tamaño de simulación (actualmente `500x500`) con interpolación bilineal.
3. Aplica un **flip vertical** interno (no debes voltear la imagen manualmente antes).

### Semántica física por canales (RGBA)

Cada píxel es una celda del autómata:

- **R (rojo) -> fuego inicial**
	- `0.0`: sin fuego
	- `1.0`: celda encendida al inicio
- **G (verde) -> elevación**
	- `0.0` a `1.0`: altura normalizada (topografía)
- **B (azul) -> combustible / barrera**
	- `0.0`: barrera no combustible (agua, asfalto, cortafuegos)
	- `0.2`: combustible bajo (pasto/humedal)
	- `0.5`: combustible medio (matorral)
	- `0.8`: combustible alto (pinar)
	- `1.0`: combustible muy alto
- **A (alpha) -> reservado**
	- Se recomienda `1.0` en toda la imagen.

### Recomendación para preparación desde Google Earth

Google Earth no exporta directamente un PNG con significado RGBA físico, así que el flujo recomendado es:

1. Obtener base geográfica (captura o raster exportado).
2. Crear capa de elevación normalizada para canal **G**.
3. Crear capa de combustible categórico para canal **B** usando los valores anteriores.
4. Definir igniciones iniciales en canal **R** (normalmente todo a `0.0`, salvo focos concretos).
5. Exportar como **PNG** (mejor que JPG para no introducir artefactos con compresión).

### Requisitos prácticos para que funcione bien

- La imagen puede ser de cualquier resolución, pero `500x500` evita reescalados.
- Evita JPG si quieres reproducibilidad física fina (la compresión altera canales).
- No uses paletas indexadas; exporta como color real.
- Si el resultado sale "invertido" verticalmente, revisa la fuente: el simulador ya aplica flip interno.

### Carga en la app

1. Abrir la simulación.
2. Pulsar **Cargar Mapa Externo...**.
3. Elegir el PNG/JPG.
4. El mapa sustituye al preset actual y se reinicia el estado.

