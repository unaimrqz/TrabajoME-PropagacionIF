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
from typing import Optional

import numpy as np
from PIL import Image


MAP_SIZE = 500


def _save_rgba(path: Path, rgba_float: np.ndarray) -> None:
    rgba_uint8 = np.clip(rgba_float * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgba_uint8)
    img.save(path)


def _base_rgba(width: int, height: Optional[int] = None) -> np.ndarray:
    if height is None:
        height = width
    rgba = np.zeros((height, width, 4), dtype=np.float32)
    rgba[:, :, 3] = 1.0
    return rgba


def generate_pedriza(size: int = MAP_SIZE, height: Optional[int] = None) -> np.ndarray:
    width = size
    if height is None:
        height = width
    rgba = _base_rgba(width, height)

    yy, xx = np.mgrid[0:height, 0:width]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    r_norm = r / r.max()

    elev = np.clip(1.0 - r_norm, 0.0, 1.0)
    rgba[:, :, 1] = elev
    rgba[:, :, 2] = 0.8
    return rgba


def generate_valdeiglesias(size: int = MAP_SIZE, height: Optional[int] = None) -> np.ndarray:
    width = size
    if height is None:
        height = width
    rgba = _base_rgba(width, height)
    rgba[:, :, 1] = 0.0
    rgba[:, :, 2] = 1.0
    return rgba


def generate_ontigola(size: int = MAP_SIZE, height: Optional[int] = None) -> np.ndarray:
    width = size
    if height is None:
        height = width
    rgba = _base_rgba(width, height)
    rgba[:, :, 1] = 0.0
    rgba[:, :, 2] = 0.2

    band_half = max(1, height // 12)
    center = height // 2
    rgba[center - band_half:center + band_half, :, 2] = 0.0
    return rgba


def generate_rivas(size: int = MAP_SIZE, height: Optional[int] = None) -> np.ndarray:
    width = size
    if height is None:
        height = width
    rgba = _base_rgba(width, height)
    rgba[:, :, 1] = 0.15
    rgba[:, :, 2] = 0.5

    yy, xx = np.mgrid[0:height, 0:width]
    cx = width // 2
    cy = height // 2
    radius = max(1, min(width, height) // 7)
    urban_mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2

    rgba[urban_mask, 2] = 0.0
    rgba[urban_mask, 3] = 1.0
    return rgba


def generate_from_real_maps(
    topo_path: str,
    fuel_path: str,
    output_name: str,
) -> np.ndarray:
    script_dir = Path(__file__).parent
    maps_dir = script_dir / "maps"

    def _resolve_input_path(raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute() and path.exists():
            return path

        candidates = []
        if path.suffix:
            candidates.append(path)
            for alt_ext in (".png", ".jpg", ".jpeg"):
                if alt_ext != path.suffix.lower():
                    candidates.append(path.with_suffix(alt_ext))
        else:
            candidates.append(path)
            candidates.extend(path.with_suffix(ext) for ext in (".png", ".jpg", ".jpeg"))

        for candidate in candidates:
            candidate_script = script_dir / candidate
            if candidate_script.exists():
                return candidate_script

            candidate_maps = maps_dir / candidate
            if candidate_maps.exists():
                return candidate_maps

        raise FileNotFoundError(
            f"No se encontro la imagen de entrada: {raw_path}. "
            f"Buscado en {candidate_script} y {candidate_maps}"
        )

    topo_file = _resolve_input_path(topo_path)
    fuel_file = _resolve_input_path(fuel_path)

    topo_img = Image.open(topo_file).convert("L")
    width, height = topo_img.size

    fuel_img = Image.open(fuel_file).convert("L")
    fuel_img = fuel_img.resize((width, height), Image.BILINEAR)

    topo = np.array(topo_img, dtype=np.float32) / 255.0
    fuel = np.array(fuel_img, dtype=np.float32) / 255.0

    rgba = np.zeros((height, width, 4), dtype=np.float32)
    rgba[:, :, 1] = topo
    rgba[:, :, 2] = fuel
    rgba[:, :, 3] = 1.0

    maps_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output_name)
    if not output_path.is_absolute():
        output_path = maps_dir / output_path

    _save_rgba(output_path, rgba)
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
    generate_from_real_maps(
        "guadarrama1_height.png",
        "guadarrama1_fuel.png",
        "guadarrama1_real.png",
    )
