import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "software"))

import fisica  # noqa: E402

EJEMPLO = Path(__file__).resolve().parent.parent / "datos" / "ejemplo"


def senal(frecuencia, fs=200.0, duracion=5.0, amplitud=1.0, ruido=0.0, desfase=0.0, semilla=1):
    azar = np.random.default_rng(semilla)
    t = np.arange(int(fs * duracion)) / fs
    return t, amplitud * np.sin(2 * np.pi * frecuencia * t + desfase) + azar.normal(0, ruido, len(t))


def test_periodo_por_cruces_senal_limpia():
    t, y = senal(2.0)
    assert fisica.periodo_por_cruces(t, y) == pytest.approx(0.5, rel=1e-3)


def test_periodo_por_cruces_con_ruido_y_compensacion_de_continua():
    t, y = senal(1.25, amplitud=0.5, ruido=0.03)
    assert fisica.periodo_por_cruces(t, y + 3.0) == pytest.approx(0.8, rel=0.01)


def test_periodo_por_cruces_falla_sin_oscilaciones():
    t = np.arange(0, 1, 0.01)
    with pytest.raises(ValueError):
        fisica.periodo_por_cruces(t, 0.001 * t)


def test_frecuencia_dominante():
    t, y = senal(12.3, fs=400.0, duracion=3.0, ruido=0.05)
    assert fisica.frecuencia_dominante(t, y) == pytest.approx(12.3, abs=0.1)


def test_g_desde_pendulo_recupera_g_conocido():
    longitudes = np.array([0.3, 0.45, 0.6, 0.8, 1.0])
    periodos = 2 * np.pi * np.sqrt(longitudes / 9.81)
    g, incertidumbre = fisica.g_desde_pendulo(longitudes, periodos)
    assert g == pytest.approx(9.81, rel=1e-6)
    assert incertidumbre >= 0


def test_ajuste_potencia_recupera_exponente():
    x = np.array([0.08, 0.10, 0.12, 0.15, 0.18])
    n, k, _ = fisica.ajuste_potencia(x, 0.3 / x**2)
    assert n == pytest.approx(-2.0, abs=1e-9)
    assert k == pytest.approx(0.3, rel=1e-9)


def test_calibracion_normaliza_modulo_y_quita_sesgo():
    n = 100
    quieto = {
        "t_s": np.arange(n) / 100.0,
        "ax_g": np.zeros(n),
        "ay_g": np.zeros(n),
        "az_g": np.full(n, 1.02),
        "gx_dps": np.full(n, 0.8),
        "gy_dps": np.full(n, -0.5),
        "gz_dps": np.full(n, 0.3),
    }
    parametros = fisica.parametros_calibracion(quieto)
    corregido = fisica.aplicar_calibracion(quieto, parametros)
    assert float(np.mean(fisica.modulo_aceleracion(corregido))) == pytest.approx(1.0)
    assert float(np.mean(corregido["gx_dps"])) == pytest.approx(0.0, abs=1e-9)
    assert float(np.mean(corregido["gy_dps"])) == pytest.approx(0.0, abs=1e-9)


def test_eje_dominante():
    datos = {c: np.zeros(50) for c in fisica.COLUMNAS}
    datos["gy_dps"] = np.sin(np.linspace(0, 10, 50))
    assert fisica.eje_dominante(datos, fisica.GIRO) == "gy_dps"


def test_ejemplo_pendulo_recupera_g():
    quieto = fisica.leer_csv(EJEMPLO / "quieto.csv")
    parametros = fisica.parametros_calibracion(quieto)
    longitudes, periodos = [], []
    for cm in (30, 45, 60, 80, 100):
        datos = fisica.aplicar_calibracion(fisica.leer_csv(EJEMPLO / f"pendulo_{cm}cm.csv"), parametros)
        eje = fisica.eje_dominante(datos, fisica.GIRO)
        assert eje == "gy_dps"
        longitudes.append(cm / 100.0)
        periodos.append(fisica.periodo_por_cruces(datos["t_s"], datos[eje]))
    g, incertidumbre = fisica.g_desde_pendulo(longitudes, periodos)
    assert g == pytest.approx(9.81, abs=0.15)
    assert incertidumbre < 0.3


def test_ejemplo_viga_recupera_exponente_menos_dos():
    longitudes, frecuencias = [], []
    for cm in (8, 10, 12, 15, 18):
        datos = fisica.leer_csv(EJEMPLO / f"vibracion_{cm}cm.csv")
        eje = fisica.eje_dominante(datos, fisica.ACEL)
        assert eje == "az_g"
        longitudes.append(cm / 100.0)
        frecuencias.append(fisica.frecuencia_dominante(datos["t_s"], datos[eje]))
    n, _, _ = fisica.ajuste_potencia(longitudes, frecuencias)
    assert n == pytest.approx(-2.0, abs=0.1)


def test_leer_csv_ignora_comentarios_y_filas_danadas(tmp_path):
    ruta = tmp_path / "x.csv"
    ruta.write_text(
        "# frecuencia_hz=100\n"
        "t_s,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps\n"
        "0.0,0,0,1,0,0,0\n"
        "0.01,abc,0,1,0,0,0\n"
        "0.02,0,0,1,0,0,0\n",
        encoding="utf-8",
    )
    datos = fisica.leer_csv(ruta)
    assert len(datos["t_s"]) == 2
