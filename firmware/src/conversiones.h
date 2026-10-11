#pragma once

// Funciones puras (sin dependencias de Arduino) para poder probarlas en una PC.

#include <stdint.h>

// Une dos bytes (el MPU-6050 entrega primero el byte alto) en un entero con signo.
inline int16_t combinarBytes(uint8_t alto, uint8_t bajo) {
  return (int16_t)(((uint16_t)alto << 8) | bajo);
}

// Valor del registro ACCEL_CONFIG para el rango pedido (2, 4, 8 o 16 g).
inline uint8_t bitsRangoAcel(int rangoG) {
  switch (rangoG) {
    case 4:
      return 0x08;
    case 8:
      return 0x10;
    case 16:
      return 0x18;
    default:
      return 0x00;  // +-2 g
  }
}

// El rango +-R g cubre 65536 cuentas: la sensibilidad es 32768 / R cuentas por g.
inline float aceleracionG(int16_t crudo, int rangoG) {
  return (float)crudo / (32768.0f / (float)rangoG);
}

// Giroscopio en +-250 grados por segundo: 131 cuentas por grado por segundo.
inline float giroDps(int16_t crudo) {
  return (float)crudo / 131.0f;
}

inline uint32_t periodoUs(int frecuenciaHz) {
  return 1000000UL / (uint32_t)frecuenciaHz;
}

// Cantidad de muestras de una grabacion, limitada por el tamano del buffer.
inline int muestrasObjetivo(int frecuenciaHz, int segundos, int maximo) {
  long pedido = (long)frecuenciaHz * (long)segundos;
  return pedido > maximo ? maximo : (int)pedido;
}

inline int limitar(int valor, int minimo, int maximo) {
  return valor < minimo ? minimo : (valor > maximo ? maximo : valor);
}
