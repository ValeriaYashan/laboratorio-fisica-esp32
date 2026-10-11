#!/usr/bin/env python3
"""Controla el dispositivo por serial: graba un experimento y descarga el CSV.

Uso con el dispositivo conectado a la PC:
    python software/registrar.py --puerto COM3 --frecuencia 100 --segundos 10 --salida datos/pendulo_60cm.csv

Si grabaste con el boton y ahora conectaste el dispositivo, solo descargar:
    python software/registrar.py --puerto COM3 --solo-descargar --salida datos/pendulo_60cm.csv
"""

import argparse
import sys
import time
from pathlib import Path

CABECERA = ["t_s", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"]


def parsear_linea(linea):
    """Convierte una linea del volcado en 7 numeros. Devuelve None si no es una muestra."""
    linea = linea.strip()
    if not linea or linea.startswith("#") or linea.startswith("t_s"):
        return None
    partes = linea.split(",")
    if len(partes) != 7:
        return None
    try:
        valores = [float(p) for p in partes]
    except ValueError:
        return None
    # El MPU-6050 llega como maximo a +-16 g y +-2000 dps.
    if not all(abs(v) <= 17 for v in valores[1:4]) or not all(abs(v) <= 2100 for v in valores[4:]):
        return None
    return valores


def enviar(puerto, texto):
    puerto.write((texto + "\n").encode("ascii"))
    puerto.flush()
    time.sleep(0.1)


def descargar(puerto, espera_inactividad=3.0, limite_total=120.0):
    """Pide el volcado y lee hasta que el dispositivo deja de enviar datos."""
    puerto.reset_input_buffer()
    enviar(puerto, "v")
    muestras, ultimo = [], time.time()
    inicio = ultimo
    while time.time() - inicio < limite_total:
        linea = puerto.readline().decode("utf-8", errors="ignore")
        muestra = parsear_linea(linea)
        if muestra is not None:
            muestras.append(muestra)
            ultimo = time.time()
        elif time.time() - ultimo > espera_inactividad and muestras:
            break
        elif time.time() - ultimo > espera_inactividad * 3:
            break
    return muestras


def guardar(muestras, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        archivo.write(",".join(CABECERA) + "\n")
        for fila in muestras:
            archivo.write(f"{fila[0]:.4f}," + ",".join(f"{v:.4f}" for v in fila[1:4]) + "," + ",".join(f"{v:.3f}" for v in fila[4:]) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--puerto", required=True)
    parser.add_argument("--baudios", type=int, default=230400)
    parser.add_argument("--frecuencia", type=int, default=100, help="Frecuencia de muestreo en Hz (20 a 1000)")
    parser.add_argument("--segundos", type=float, default=10.0, help="Duracion de la grabacion")
    parser.add_argument("--salida", required=True, help="CSV de salida")
    parser.add_argument("--solo-descargar", action="store_true", help="No grabar: solo bajar lo ya grabado")
    args = parser.parse_args()

    try:
        import serial
    except ImportError:
        sys.exit("Falta pyserial: pip install -r software/requirements.txt")

    try:
        with serial.Serial(args.puerto, args.baudios, timeout=1) as puerto:
            time.sleep(2.0)  # el ESP32 se reinicia al abrir el puerto
            puerto.reset_input_buffer()
            if not args.solo_descargar:
                enviar(puerto, f"f{args.frecuencia}")
                enviar(puerto, f"s{int(round(args.segundos))}")
                print(f"Grabando {args.segundos:.0f} s a {args.frecuencia} Hz. Hacé el experimento ahora.")
                enviar(puerto, "g")
                time.sleep(args.segundos + 1.0)
            muestras = descargar(puerto)
    except serial.SerialException as error:
        sys.exit(f"Error de puerto serie: {error}")

    if not muestras:
        sys.exit("No llegaron muestras. Revisá el cableado del sensor y el puerto.")
    guardar(muestras, args.salida)
    duracion = muestras[-1][0] - muestras[0][0]
    print(f"{len(muestras)} muestras ({duracion:.2f} s) guardadas en {args.salida}")


if __name__ == "__main__":
    main()
