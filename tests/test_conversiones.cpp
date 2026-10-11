// Pruebas de las funciones puras del firmware. Se compilan en una PC:
//   g++ -std=c++17 -o prueba_conversiones tests/test_conversiones.cpp && ./prueba_conversiones

#include <cassert>
#include <cmath>
#include <cstdio>

#include "../firmware/src/conversiones.h"

static bool casiIgual(float a, float b, float tolerancia = 1e-4f) {
  return std::fabs(a - b) <= tolerancia;
}

int main() {
  // Union de bytes con signo.
  assert(combinarBytes(0x00, 0x01) == 1);
  assert(combinarBytes(0xFF, 0xFE) == -2);
  assert(combinarBytes(0x40, 0x00) == 16384);
  assert(combinarBytes(0x80, 0x00) == -32768);

  // Registro de rango del acelerometro.
  assert(bitsRangoAcel(2) == 0x00);
  assert(bitsRangoAcel(4) == 0x08);
  assert(bitsRangoAcel(8) == 0x10);
  assert(bitsRangoAcel(16) == 0x18);

  // Sensibilidad: 16384, 8192, 4096 y 2048 cuentas por g.
  assert(casiIgual(aceleracionG(16384, 2), 1.0f));
  assert(casiIgual(aceleracionG(8192, 4), 1.0f));
  assert(casiIgual(aceleracionG(4096, 8), 1.0f));
  assert(casiIgual(aceleracionG(2048, 16), 1.0f));
  assert(casiIgual(aceleracionG(-8192, 4), -1.0f));

  // Giroscopio.
  assert(casiIgual(giroDps(131), 1.0f));
  assert(casiIgual(giroDps(-262), -2.0f));

  // Periodo de muestreo y cantidad de muestras.
  assert(periodoUs(100) == 10000);
  assert(periodoUs(500) == 2000);
  assert(muestrasObjetivo(100, 10, 6000) == 1000);
  assert(muestrasObjetivo(1000, 10, 6000) == 6000);

  assert(limitar(5, 20, 1000) == 20);
  assert(limitar(5000, 20, 1000) == 1000);
  assert(limitar(100, 20, 1000) == 100);

  std::puts("conversiones: todas las pruebas pasaron");
  return 0;
}
