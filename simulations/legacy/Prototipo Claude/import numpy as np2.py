import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

# =====================
# PARAMETROS
# =====================

N = 60
beta = 0.35
gamma = 0.25      # I -> Q
delta = 0.15      # Q -> R
steps = 120

# viento
wind_direction = "down"
wind_strength = 1.8

# =====================
# ESTADOS
# =====================

S = 0   # vivo
I = 1   # ardiendo fuerte
Q = 2   # semiquemado
R = 3   # quemado total / cortafuegos

# =====================
# INICIALIZACION
# =====================

forest = np.zeros((N, N), dtype=int)

# fuego inicial
forest[-35, N//2] = I

# cortafuegos
forest[27:28, 5:6] = R
forest[30:32, 5:8] = R
# =====================
# CURVAS
# =====================

S_curve = []
I_curve = []
Q_curve = []
R_curve = []

# =====================
# FUNCIONES
# =====================

def vecinos(i, j, N):
    v = []
    if i > 0: v.append((i-1, j))
    if i < N-1: v.append((i+1, j))
    if j > 0: v.append((i, j-1))
    if j < N-1: v.append((i, j+1))
    return v


def factor_viento(i, j, x, y):

    if wind_direction == "down" and x == i-1:
        return wind_strength
    if wind_direction == "up" and x == i+1:
        return wind_strength
    if wind_direction == "right" and y == j-1:
        return wind_strength
    if wind_direction == "left" and y == j+1:
        return wind_strength

    return 1.0


def step(forest):

    new_forest = forest.copy()

    for i in range(N):
        for j in range(N):

            # -------- SANO --------
            if forest[i,j] == S:

                p_no_fire = 1.0

                for x,y in vecinos(i,j,N):
                    if forest[x,y] in [I, Q]:

                        factor = factor_viento(i,j,x,y)

                        # brasas contagian menos
                        beta_eff = beta * factor
                        if forest[x,y] == Q:
                            beta_eff *= 0.4

                        beta_eff = min(beta_eff, 1.0)

                        p_no_fire *= (1 - beta_eff)

                p_fire = 1 - p_no_fire

                if np.random.rand() < p_fire:
                    new_forest[i,j] = I

            # -------- ARDIENDO --------
            elif forest[i,j] == I:
                if np.random.rand() < gamma:
                    new_forest[i,j] = Q

            # -------- SEMIQUEMADO --------
            elif forest[i,j] == Q:
                if np.random.rand() < delta:
                    new_forest[i,j] = R

    return new_forest


# =====================
# VISUALIZACION
# =====================

# verde, rojo, naranja, negro
cmap = colors.ListedColormap(["green","red","orange","black"])

plt.figure(figsize=(6,6))

for t in range(steps):

    # guardar curvas
    S_curve.append(np.sum(forest == S))
    I_curve.append(np.sum(forest == I))
    Q_curve.append(np.sum(forest == Q))
    R_curve.append(np.sum(forest == R))

    plt.clf()
    plt.imshow(forest, cmap=cmap, vmin=0, vmax=3)
    plt.title(f"Paso {t} | viento: {wind_direction}")
    plt.pause(0.1)

    forest = step(forest)

plt.show()

# =====================
# CURVAS TEMPORALES
# =====================

plt.figure(figsize=(8,5))

plt.plot(S_curve, label="S vivos")
plt.plot(I_curve, label="I ardiendo")
plt.plot(Q_curve, label="Q semiquemados")
plt.plot(R_curve, label="R quemados")

plt.xlabel("Tiempo")
plt.ylabel("Numero de arboles")
plt.title("Modelo incendios S-I-Q-R")
plt.legend()
plt.grid()
plt.show()