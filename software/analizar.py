#!/usr/bin/env python3
"""Analiza los experimentos del laboratorio: resumen, pendulo (estimar g) y viga (vibracion).

Ejemplos:
    python software/analizar.py resumen datos/ejemplo/pendulo_60cm.csv
    python software/analizar.py pendulo --archivos datos/ejemplo/pendulo_*cm.csv \\
        --quieto datos/ejemplo/quieto.csv --salida pendulo.png
    python software/analizar.py vibracion --archivos datos/ejemplo/vibracion_*cm.csv --salida vibracion.png

Si los archivos se llaman como pendulo_60cm.csv, la longitud se lee del nombre. Si no, pasala con
--longitudes (en metros, en el mismo orden que los archivos). Los datos se ordenan por longitud.
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib
import numpy as np

import fisica

COLOR_DATOS = "#378ADD"
COLOR_AJUSTE = "#D85A30"


def cargar(ruta, quieto):
    datos = fisica.leer_csv(ruta)
    if len(datos["t_s"]) < 10:
        sys.exit(f"{ruta} tiene muy pocas muestras para analizar.")
    if quieto is not None:
        datos = fisica.aplicar_calibracion(datos, quieto)
    return datos


def cargar_calibracion(ruta):
    if not ruta:
        return None
    parametros = fisica.parametros_calibracion(fisica.leer_csv(ruta))
    print(
        f"Calibracion ({ruta}): escala del acelerometro {parametros['escala_acel']:.4f}, "
        f"sesgo del giroscopio {[round(s, 2) for s in parametros['sesgo_giro_dps']]} dps"
    )
    return parametros


def longitud_desde_nombre(ruta):
    """Lee la longitud en metros de un nombre como pendulo_60cm.csv. Devuelve None si no la encuentra."""
    coincidencia = re.search(r"(\d+(?:[.,]\d+)?)cm", Path(ruta).name)
    if coincidencia is None:
        return None
    return float(coincidencia.group(1).replace(",", ".")) / 100.0


def validar_pares(args):
    """Ordena los archivos por longitud. Si no se dan --longitudes, las toma del nombre."""
    if args.longitudes is None:
        args.longitudes = [longitud_desde_nombre(r) for r in args.archivos]
        if any(l is None for l in args.longitudes):
            sys.exit("No pude leer la longitud del nombre de algun archivo (ej. pendulo_60cm.csv). Usa --longitudes.")
    if len(args.archivos) != len(args.longitudes):
        sys.exit("Tiene que haber una longitud por cada archivo.")
    if len(args.archivos) < 3:
        sys.exit("Hacen falta al menos 3 mediciones para ajustar y estimar la incertidumbre.")
    pares = sorted(zip(args.longitudes, args.archivos))
    args.longitudes = [p[0] for p in pares]
    args.archivos = [p[1] for p in pares]


def preparar_grafico(mostrar):
    if not mostrar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def finalizar(plt, fig, salida, mostrar):
    fig.tight_layout()
    if salida:
        fig.savefig(salida)
        print(f"Grafico guardado en {salida}")
    if mostrar:
        plt.show()
    plt.close(fig)


def cmd_resumen(args):
    for ruta in args.archivos:
        datos = cargar(ruta, cargar_calibracion(args.quieto))
        r = fisica.resumen_registro(datos)
        print(
            f"{ruta}: {r['muestras']} muestras, {r['duracion_s']:.2f} s, "
            f"{r['frecuencia_hz']:.1f} Hz, modulo medio {r['modulo_medio_g']:.3f} g"
        )


def cmd_pendulo(args):
    validar_pares(args)
    calibracion = cargar_calibracion(args.quieto)
    periodos, controles = [], []
    print(f"{'archivo':<34}{'L (m)':>8}{'eje':>9}{'T cruces (s)':>14}{'T espectro (s)':>16}")
    for ruta, longitud in zip(args.archivos, args.longitudes):
        datos = cargar(ruta, calibracion)
        eje = fisica.eje_dominante(datos, fisica.GIRO)
        periodo = fisica.periodo_por_cruces(datos["t_s"], datos[eje])
        control = 1.0 / fisica.frecuencia_dominante(datos["t_s"], datos[eje], f_min=0.2)
        periodos.append(periodo)
        controles.append(control)
        print(f"{ruta:<34}{longitud:>8.3f}{eje:>9}{periodo:>14.4f}{control:>16.4f}")

    g, incertidumbre = fisica.g_desde_pendulo(args.longitudes, periodos)
    print(f"\ng estimada = {g:.2f} +/- {incertidumbre:.2f} m/s^2 (referencia: 9,8 m/s^2)")

    plt = preparar_grafico(args.mostrar)
    fig, eje = plt.subplots(figsize=(7, 4.5), dpi=150)
    longitudes = np.asarray(args.longitudes)
    cuadrados = np.asarray(periodos) ** 2
    pendiente, ordenada, _ = fisica.ajuste_lineal(longitudes, cuadrados)
    x = np.linspace(0, longitudes.max() * 1.05, 50)
    eje.plot(x, pendiente * x + ordenada, color=COLOR_AJUSTE, linewidth=1.6, label="Ajuste lineal")
    eje.plot(longitudes, cuadrados, "o", color=COLOR_DATOS, label="Mediciones")
    eje.set_xlabel("Longitud L (m)")
    eje.set_ylabel("Período al cuadrado T² (s²)")
    eje.set_title(f"Péndulo: g = {g:.2f} ± {incertidumbre:.2f} m/s²")
    eje.grid(True, alpha=0.25)
    eje.legend(frameon=False)
    finalizar(plt, fig, args.salida, args.mostrar)


def cmd_vibracion(args):
    validar_pares(args)
    calibracion = cargar_calibracion(args.quieto)
    frecuencias, espectros = [], []
    print(f"{'archivo':<34}{'L (m)':>8}{'eje':>9}{'f espectro (Hz)':>17}{'f cruces (Hz)':>15}")
    for ruta, longitud in zip(args.archivos, args.longitudes):
        datos = cargar(ruta, calibracion)
        eje = fisica.eje_dominante(datos, fisica.ACEL)
        frecuencia = fisica.frecuencia_dominante(datos["t_s"], datos[eje])
        try:
            control = 1.0 / fisica.periodo_por_cruces(datos["t_s"], datos[eje])
            control_texto = f"{control:>15.2f}"
        except ValueError:
            control_texto = f"{'-':>15}"
        frecuencias.append(frecuencia)
        espectros.append(fisica.espectro(datos["t_s"], datos[eje]))
        print(f"{ruta:<34}{longitud:>8.3f}{eje:>9}{frecuencia:>17.2f}{control_texto}")

    n, k, incertidumbre = fisica.ajuste_potencia(args.longitudes, frecuencias)
    print(f"\nf = {k:.3f} * L^({n:.2f} +/- {incertidumbre:.2f}). Para una viga ideal el exponente es -2.")

    plt = preparar_grafico(args.mostrar)
    fig, (izq, der) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=150)
    for longitud, (f, a), pico in zip(args.longitudes, espectros, frecuencias):
        limite = min(150.0, f[-1])
        mascara = (f >= 1.0) & (f <= limite)
        izq.plot(f[mascara], a[mascara], linewidth=1.2, label=f"L = {longitud * 100:.0f} cm")
    izq.set_xlabel("Frecuencia (Hz)")
    izq.set_ylabel("Amplitud (g)")
    izq.set_title("Espectros")
    izq.grid(True, alpha=0.25)
    izq.legend(frameon=False)

    longitudes = np.asarray(args.longitudes)
    x = np.linspace(longitudes.min() * 0.9, longitudes.max() * 1.1, 50)
    der.loglog(x, k * x**n, color=COLOR_AJUSTE, linewidth=1.6, label=f"Ajuste: exponente {n:.2f} ± {incertidumbre:.2f}")
    der.loglog(longitudes, frecuencias, "o", color=COLOR_DATOS, label="Mediciones")
    der.set_xlabel("Longitud de la viga L (m)")
    der.set_ylabel("Frecuencia f (Hz)")
    der.set_title("Frecuencia en función de la longitud")
    der.grid(True, which="both", alpha=0.25)
    der.legend(frameon=False)
    finalizar(plt, fig, args.salida, args.mostrar)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    def comunes(p, con_longitudes):
        p.add_argument("--archivos", nargs="+", required=True, help="CSV de las mediciones")
        if con_longitudes:
            p.add_argument("--longitudes", nargs="+", type=float, help="Longitudes en metros (por defecto, se leen del nombre del archivo)")
            p.add_argument("--salida", help="Guardar el grafico en este archivo")
            p.add_argument("--mostrar", action="store_true", help="Abrir la ventana del grafico")
        p.add_argument("--quieto", help="CSV con el dispositivo quieto, para calibrar")

    p_resumen = sub.add_parser("resumen", help="Resumen de uno o varios registros")
    p_resumen.add_argument("archivos", nargs="+")
    p_resumen.add_argument("--quieto")
    p_resumen.set_defaults(funcion=cmd_resumen)

    p_pendulo = sub.add_parser("pendulo", help="Estimar g con un pendulo")
    comunes(p_pendulo, True)
    p_pendulo.set_defaults(funcion=cmd_pendulo)

    p_viga = sub.add_parser("vibracion", help="Frecuencia de una viga en funcion de su longitud")
    comunes(p_viga, True)
    p_viga.set_defaults(funcion=cmd_vibracion)

    args = parser.parse_args()
    try:
        args.funcion(args)
    except FileNotFoundError as error:
        sys.exit(f"No se encontro el archivo: {error.filename}")
    except ValueError as error:
        sys.exit(f"No se pudo analizar: {error}")


if __name__ == "__main__":
    main()
