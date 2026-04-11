# map_generator.py
# Este script se encarga de generar los mapas iniciales para la simulación. 
# Cada mapa es una imagen RGBA donde el canal verde representa la elevación 
# del terreno (0.0 para el nivel del mar, 1.0 para la montaña más alta), el 
# canal azul representa la vegetación (0.0 para sin vegetación, 1.0 para 
# vegetación densa), y el canal alfa representa la opacidad (1.0 para 
# completamente opaco, 0.0 para completamente transparente). Estos mapas se
# guardan en formato PNG en la carpeta "maps" dentro del directorio de este 
# script.

from pathlib import Path

import numpy as np
from PIL import Image


MAP_SIZE = 500


def _save_rgba(path: Path, rgba_float: np.ndarray) -> None:
    rgba_uint8 = np.clip(rgba_float * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgba_uint8)
    img.save(path)


def _base_rgba(size: int) -> np.ndarray:
    rgba = np.zeros((size, size, 4), dtype=np.float32)
    rgba[:, :, 3] = 1.0
    return rgba


def generate_pedriza(size: int = MAP_SIZE) -> np.ndarray:
    rgba = _base_rgba(size)

    yy, xx = np.mgrid[0:size, 0:size]
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    r_norm = r / r.max()

    elev = np.clip(1.0 - r_norm, 0.0, 1.0)
    rgba[:, :, 1] = elev
    rgba[:, :, 2] = 0.8
    return rgba


def generate_valdeiglesias(size: int = MAP_SIZE) -> np.ndarray:
    rgba = _base_rgba(size)
    rgba[:, :, 1] = 0.0
    rgba[:, :, 2] = 1.0
    return rgba


def generate_ontigola(size: int = MAP_SIZE) -> np.ndarray:
    rgba = _base_rgba(size)
    rgba[:, :, 1] = 0.0
    rgba[:, :, 2] = 0.2

    band_half = size // 12
    center = size // 2
    rgba[center - band_half:center + band_half, :, 2] = 0.0
    return rgba


def generate_rivas(size: int = MAP_SIZE) -> np.ndarray:
    rgba = _base_rgba(size)
    rgba[:, :, 1] = 0.15
    rgba[:, :, 2] = 0.5

    yy, xx = np.mgrid[0:size, 0:size]
    cx = size // 2
    cy = size // 2
    radius = size // 7
    urban_mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2

    rgba[urban_mask, 2] = 0.0
    rgba[urban_mask, 3] = 1.0
    return rgba


def generate_all_maps() -> None:
    maps_dir = Path(__file__).parent / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    _save_rgba(maps_dir / "pedriza.png", generate_pedriza())
    _save_rgba(maps_dir / "valdeiglesias.png", generate_valdeiglesias())
    _save_rgba(maps_dir / "ontigola.png", generate_ontigola())
    _save_rgba(maps_dir / "rivas.png", generate_rivas())


if __name__ == "__main__":
    generate_all_maps()
