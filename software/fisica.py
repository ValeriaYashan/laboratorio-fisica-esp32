"""Funciones de analisis de los experimentos (sin entrada/salida de consola).

Todas trabajan con arreglos de numpy. Los datos de un registro se representan como un
diccionario con las claves t_s, ax_g, ay_g, az_g, gx_dps, gy_dps y gz_dps.
"""

import csv
import math

import numpy as np

ACEL = ["ax_g", "ay_g", "az_g"]
GIRO = ["gx_dps", "gy_dps", "gz_dps"]
COLUMNAS = ["t_s"] + ACEL + GIRO


def leer_csv(ruta):
    """Lee un CSV del dispositivo. Ignora las lineas que empiezan con #."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lineas = [l for l in archivo if l.strip() and not l.startswith("#")]
    datos = {c: [] for c in COLUMNAS}
    for fila in csv.DictReader(lineas):
        try:
            valores = {c: float(fila[c]) for c in COLUMNAS}
        except (KeyError, ValueError, TypeError):
            continue
        for c in COLUMNAS:
            datos[c].append(valores[c])
    return {c: np.asarray(v, dtype=float) for c, v in datos.items()}


def frecuencia_muestreo(t):
    """Frecuencia de muestreo en Hz, a partir de la mediana de los intervalos."""
    return 1.0 / float(np.median(np.diff(t)))


def modulo_aceleracion(datos):
    """Modulo del vector aceleracion, en g."""
    return np.sqrt(sum(datos[c] ** 2 for c in ACEL))


def resumen_registro(datos):
    t = datos["t_s"]
    return {
        "muestras": int(len(t)),
        "duracion_s": float(t[-1] - t[0]),
        "frecuencia_hz": frecuencia_muestreo(t),
        "modulo_medio_g": float(np.mean(modulo_aceleracion(datos))),
    }


def parametros_calibracion(quieto):
    """Calcula la correccion a partir de un registro con el dispositivo quieto.

    El sesgo del giroscopio es el promedio de cada eje (deberia ser cero). La escala del
    acelerometro es el factor que hace que el modulo en reposo valga exactamente 1 g.
    """
    sesgo = [float(np.mean(quieto[c])) for c in GIRO]
    medio = np.array([np.mean(quieto[c]) for c in ACEL])
    escala = 1.0 / float(np.linalg.norm(medio))
    return {"sesgo_giro_dps": sesgo, "escala_acel": escala}


def aplicar_calibracion(datos, parametros):
    corregido = {c: np.array(v, dtype=float) for c, v in datos.items()}
    for c, sesgo in zip(GIRO, parametros["sesgo_giro_dps"]):
        corregido[c] = corregido[c] - sesgo
    for c in ACEL:
        corregido[c] = corregido[c] * parametros["escala_acel"]
    return corregido


def eje_dominante(datos, canales):
    """Canal con mayor desvio estandar: el eje en el que mas se mueve el sensor."""
    return max(canales, key=lambda c: float(np.std(datos[c])))


def periodo_por_cruces(t, y, max_ciclos=10):
    """Periodo de una senal oscilante a partir de sus cruces ascendentes por cero.

    Un cruce solo cuenta si antes hubo un valle claro (mas profundo que el 10 % de la
    amplitud maxima), para que el ruido cerca de cero no genere cruces falsos. Usa los
    primeros `max_ciclos` ciclos y devuelve la mediana de los periodos.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    y = y - np.mean(y)
    umbral = 0.1 * float(np.max(np.abs(y)))
    cruces = []
    ultimo = 0
    for i in range(1, len(y)):
        if y[i - 1] < 0.0 <= y[i] and float(np.min(y[ultimo:i])) < -umbral:
            fraccion = -y[i - 1] / (y[i] - y[i - 1])
            cruces.append(t[i - 1] + fraccion * (t[i] - t[i - 1]))
            ultimo = i
            if len(cruces) > max_ciclos:
                break
    if len(cruces) < 3:
        raise ValueError("No hay suficientes oscilaciones para medir el periodo.")
    return float(np.median(np.diff(cruces)))


def espectro(t, y):
    """Espectro de amplitud (con ventana de Hann). Devuelve (frecuencias_hz, amplitudes)."""
    y = np.asarray(y, dtype=float)
    y = y - np.mean(y)
    fs = frecuencia_muestreo(t)
    ventana = np.hanning(len(y))
    n_fft = 1 << int(math.ceil(math.log2(len(y) * 8)))
    amplitudes = np.abs(np.fft.rfft(y * ventana, n_fft)) * 2.0 / np.sum(ventana)
    frecuencias = np.fft.rfftfreq(n_fft, d=1.0 / fs)
    return frecuencias, amplitudes


def frecuencia_dominante(t, y, f_min=1.0):
    """Frecuencia del pico principal del espectro, en Hz, ignorando lo que esta bajo f_min."""
    frecuencias, amplitudes = espectro(t, y)
    mascara = frecuencias >= f_min
    indices = np.flatnonzero(mascara)
    pico = int(indices[np.argmax(amplitudes[mascara])])
    if 0 < pico < len(amplitudes) - 1:
        a, b, c = amplitudes[pico - 1], amplitudes[pico], amplitudes[pico + 1]
        denominador = a - 2 * b + c
        desplazamiento = 0.5 * (a - c) / denominador if denominador != 0 else 0.0
        paso = frecuencias[1] - frecuencias[0]
        return float(frecuencias[pico] + desplazamiento * paso)
    return float(frecuencias[pico])


def ajuste_lineal(x, y):
    """Ajuste y = m x + b. Devuelve (m, b, incertidumbre_de_m)."""
    (m, b), covarianza = np.polyfit(x, y, 1, cov=True)
    return float(m), float(b), float(math.sqrt(covarianza[0, 0]))


def g_desde_pendulo(longitudes_m, periodos_s):
    """Estima g con T^2 = (4 pi^2 / g) L. Devuelve (g, incertidumbre) en m/s^2."""
    longitudes = np.asarray(longitudes_m, dtype=float)
    cuadrados = np.asarray(periodos_s, dtype=float) ** 2
    pendiente, _, error = ajuste_lineal(longitudes, cuadrados)
    g = 4.0 * math.pi**2 / pendiente
    return g, g * error / pendiente


def ajuste_potencia(x, y):
    """Ajuste y = k x^n en escala logaritmica. Devuelve (n, k, incertidumbre_de_n)."""
    (n, logk), covarianza = np.polyfit(np.log(x), np.log(y), 1, cov=True)
    return float(n), float(math.exp(logk)), float(math.sqrt(covarianza[0, 0]))
