#!/usr/bin/env python3
"""Genera datos/ejemplo/ con registros SIMULADOS de un pendulo y de una viga voladiza.

Los datos son simulados con modelos fisicos simples mas ruido, sesgo del giroscopio y un
error de ganancia del acelerometro. No son mediciones reales: sirven para probar el analisis
y el panel sin hardware.
"""

import csv
from pathlib import Path

import numpy as np

SALIDA = Path(__file__).resolve().parent.parent / "datos" / "ejemplo"
G = 9.81
GANANCIA_ACEL = 1.02
SESGO_GIRO = (0.8, -0.5, 0.3)


def escribir(ruta, t, ax, ay, az, gx, gy, gz):
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["t_s", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"])
        for fila in zip(t, ax, ay, az, gx, gy, gz):
            escritor.writerow([f"{fila[0]:.4f}"] + [f"{v:.4f}" for v in fila[1:4]] + [f"{v:.3f}" for v in fila[4:]])


def ruido(azar, n, escala):
    return azar.normal(0.0, escala, n)


def tiempos(azar, fs, duracion):
    n = int(fs * duracion)
    # Pequeno jitter de tiempo, como el de un microcontrolador real.
    return np.arange(n) / fs + azar.uniform(-0.0002, 0.0002, n), n


def quieto(azar):
    fs, duracion = 100.0, 5.0
    t, n = tiempos(azar, fs, duracion)
    escribir(
        SALIDA / "quieto.csv",
        t,
        ruido(azar, n, 0.01),
        ruido(azar, n, 0.01),
        GANANCIA_ACEL + ruido(azar, n, 0.01),
        SESGO_GIRO[0] + ruido(azar, n, 0.3),
        SESGO_GIRO[1] + ruido(azar, n, 0.3),
        SESGO_GIRO[2] + ruido(azar, n, 0.3),
    )


def pendulo(azar, longitud_m):
    fs, duracion = 100.0, 10.0
    t, n = tiempos(azar, fs, duracion)
    theta0, amortiguamiento = np.radians(10.0), 0.03
    omega = np.sqrt(G / longitud_m)
    omega_d = np.sqrt(omega**2 - amortiguamiento**2)
    envolvente = np.exp(-amortiguamiento * t)
    theta = theta0 * envolvente * np.cos(omega_d * t)
    theta_p = -theta0 * envolvente * (amortiguamiento * np.cos(omega_d * t) + omega_d * np.sin(omega_d * t))
    # Un punto material colgado: la fuerza especifica es radial, g cos(theta) + L theta'^2.
    radial = np.cos(theta) + longitud_m * theta_p**2 / G
    escribir(
        SALIDA / f"pendulo_{round(longitud_m * 100)}cm.csv",
        t,
        ruido(azar, n, 0.01),
        ruido(azar, n, 0.01),
        GANANCIA_ACEL * radial + ruido(azar, n, 0.01),
        SESGO_GIRO[0] + ruido(azar, n, 0.3),
        np.degrees(theta_p) + SESGO_GIRO[1] + ruido(azar, n, 0.3),
        SESGO_GIRO[2] + ruido(azar, n, 0.3),
    )


def viga(azar, longitud_m):
    fs, duracion = 400.0, 3.0
    t, n = tiempos(azar, fs, duracion)
    k = 0.30  # Hz * m^2 : f = k / L^2 (valor inventado para la simulacion)
    frecuencia = k / (longitud_m * (1.0 + azar.normal(0.0, 0.01))) ** 2
    omega = 2.0 * np.pi * frecuencia
    zeta = 0.02
    oscilacion = 0.4 * np.exp(-zeta * omega * t) * np.sin(omega * t)
    escribir(
        SALIDA / f"vibracion_{round(longitud_m * 100)}cm.csv",
        t,
        ruido(azar, n, 0.01),
        ruido(azar, n, 0.01),
        GANANCIA_ACEL * (1.0 + oscilacion) + ruido(azar, n, 0.01),
        SESGO_GIRO[0] + ruido(azar, n, 0.3),
        SESGO_GIRO[1] + ruido(azar, n, 0.3),
        SESGO_GIRO[2] + ruido(azar, n, 0.3),
    )


def main():
    azar = np.random.default_rng(2026)
    SALIDA.mkdir(parents=True, exist_ok=True)
    quieto(azar)
    for longitud in (0.30, 0.45, 0.60, 0.80, 1.00):
        pendulo(azar, longitud)
    for longitud in (0.08, 0.10, 0.12, 0.15, 0.18):
        viga(azar, longitud)
    print(f"Generado {SALIDA}")


if __name__ == "__main__":
    main()
