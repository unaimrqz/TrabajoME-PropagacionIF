# config.py
# Este archivo define la clase SimulationConfig, que es una estructura 
# de datos simple que contiene la configuración de la simulación. Aquí 
# se pueden ajustar parámetros como el tamaño de la cuadrícula, la tasa
# de difusión, la tasa de decaimiento, y los FPS de la simulación.

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    grid_width: int = 10
    grid_height: int = 10
    diffusion: float = 0.12
    decay: float = 0.015
    fps: int = 24
