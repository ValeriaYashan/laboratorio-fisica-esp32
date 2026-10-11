#pragma once

// Bus I2C del MPU-6050 (pines por defecto del ESP32 DevKit).
#define PIN_SDA 21
#define PIN_SCL 22

// Boton para empezar a grabar sin PC (entre este pin y GND) y LED de estado.
#define PIN_BOTON 4
#define PIN_LED 2

// Rango del acelerometro en g: 2, 4, 8 o 16. Menor rango = mas resolucion.
#define RANGO_ACEL_G 4

// Filtro pasa bajos interno del MPU-6050 (registro CONFIG): 1 = 184 Hz, 2 = 94 Hz, 3 = 44 Hz.
#define FILTRO_DLPF 1

// Valores por defecto de una grabacion (se cambian por serial con f<hz> y s<seg>).
#define FRECUENCIA_HZ 100
#define DURACION_S 10

// Limites. El buffer guarda las muestras en RAM: 6000 muestras de 16 bytes son 96 kB.
#define MAX_MUESTRAS 6000
#define FRECUENCIA_MIN_HZ 20
#define FRECUENCIA_MAX_HZ 1000
