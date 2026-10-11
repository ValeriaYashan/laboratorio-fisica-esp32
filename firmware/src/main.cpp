#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "conversiones.h"

// Registros del MPU-6050 (hoja de datos de InvenSense).
static const uint8_t DIR_MPU = 0x68;
static const uint8_t REG_SMPLRT_DIV = 0x19;
static const uint8_t REG_CONFIG = 0x1A;
static const uint8_t REG_GYRO_CONFIG = 0x1B;
static const uint8_t REG_ACCEL_CONFIG = 0x1C;
static const uint8_t REG_ACCEL_XOUT_H = 0x3B;
static const uint8_t REG_PWR_MGMT_1 = 0x6B;
static const uint8_t REG_WHO_AM_I = 0x75;

// Una muestra ocupa 16 bytes: tiempo en microsegundos y seis enteros del sensor.
struct Muestra {
  uint32_t t_us;
  int16_t ax, ay, az, gx, gy, gz;
};

enum Estado { ESPERA, GRABANDO, LISTO };

static Muestra buffer[MAX_MUESTRAS];
static int cantidad = 0;
static int objetivo = 0;
static Estado estado = ESPERA;

static int frecuenciaHz = FRECUENCIA_HZ;
static int duracionS = DURACION_S;
static uint32_t periodo = 0;
static uint32_t inicioUs = 0;
static uint32_t proximaUs = 0;

static bool escribirRegistro(uint8_t registro, uint8_t valor) {
  Wire.beginTransmission(DIR_MPU);
  Wire.write(registro);
  Wire.write(valor);
  return Wire.endTransmission() == 0;
}

static bool leerRegistros(uint8_t registro, uint8_t *destino, int cantidadBytes) {
  Wire.beginTransmission(DIR_MPU);
  Wire.write(registro);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)DIR_MPU, cantidadBytes) != cantidadBytes) return false;
  for (int i = 0; i < cantidadBytes; i++) {
    destino[i] = Wire.read();
  }
  return true;
}

static bool leerSensor(Muestra &m) {
  uint8_t b[14];
  if (!leerRegistros(REG_ACCEL_XOUT_H, b, 14)) return false;
  m.ax = combinarBytes(b[0], b[1]);
  m.ay = combinarBytes(b[2], b[3]);
  m.az = combinarBytes(b[4], b[5]);
  // b[6] y b[7] son la temperatura, que aca no se usa.
  m.gx = combinarBytes(b[8], b[9]);
  m.gy = combinarBytes(b[10], b[11]);
  m.gz = combinarBytes(b[12], b[13]);
  return true;
}

static void iniciarSensor() {
  escribirRegistro(REG_PWR_MGMT_1, 0x01);  // sale del modo de bajo consumo, reloj del giroscopio
  delay(100);
  escribirRegistro(REG_CONFIG, FILTRO_DLPF);
  escribirRegistro(REG_SMPLRT_DIV, 0);
  escribirRegistro(REG_GYRO_CONFIG, 0x00);  // +-250 dps
  escribirRegistro(REG_ACCEL_CONFIG, bitsRangoAcel(RANGO_ACEL_G));

  uint8_t quien = 0;
  if (!leerRegistros(REG_WHO_AM_I, &quien, 1)) {
    Serial.println("# No se encontro el MPU-6050. Revisa el cableado I2C.");
  } else if (quien != 0x68) {
    // Algunos modulos baratos traen un chip compatible que responde otro valor.
    Serial.printf("# Aviso: WHO_AM_I = 0x%02X (se esperaba 0x68). Puede ser un chip compatible.\n", quien);
  }
}

static void empezarGrabacion() {
  frecuenciaHz = limitar(frecuenciaHz, FRECUENCIA_MIN_HZ, FRECUENCIA_MAX_HZ);
  duracionS = limitar(duracionS, 1, 60);
  periodo = periodoUs(frecuenciaHz);
  objetivo = muestrasObjetivo(frecuenciaHz, duracionS, MAX_MUESTRAS);
  cantidad = 0;
  inicioUs = micros();
  proximaUs = inicioUs;
  estado = GRABANDO;
  digitalWrite(PIN_LED, HIGH);
}

static void terminarGrabacion() {
  estado = LISTO;
  digitalWrite(PIN_LED, LOW);
  Serial.printf("# grabacion lista: %d muestras\n", cantidad);
}

static void volcar() {
  if (cantidad == 0) {
    Serial.println("# no hay datos grabados");
    return;
  }
  Serial.printf("# frecuencia_hz=%d rango_g=%d\n", frecuenciaHz, RANGO_ACEL_G);
  Serial.println("t_s,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps");
  for (int i = 0; i < cantidad; i++) {
    const Muestra &m = buffer[i];
    Serial.printf("%.6f,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f\n", (double)m.t_us / 1e6,
                  aceleracionG(m.ax, RANGO_ACEL_G), aceleracionG(m.ay, RANGO_ACEL_G),
                  aceleracionG(m.az, RANGO_ACEL_G), giroDps(m.gx), giroDps(m.gy), giroDps(m.gz));
  }
  Serial.println("# fin");
}

// Comandos por serial, una linea cada uno:
//   g = grabar, x = detener, v = volcar el CSV, f<hz> = frecuencia, s<seg> = duracion.
static void ejecutarComando(const char *linea) {
  switch (linea[0]) {
    case 'g':
      empezarGrabacion();
      break;
    case 'x':
      if (estado == GRABANDO) terminarGrabacion();
      break;
    case 'v':
      volcar();
      break;
    case 'f':
      frecuenciaHz = limitar(atoi(linea + 1), FRECUENCIA_MIN_HZ, FRECUENCIA_MAX_HZ);
      Serial.printf("# frecuencia = %d Hz\n", frecuenciaHz);
      break;
    case 's':
      duracionS = limitar(atoi(linea + 1), 1, 60);
      Serial.printf("# duracion = %d s\n", duracionS);
      break;
    default:
      break;
  }
}

static void atenderSerial() {
  static char linea[16];
  static int largo = 0;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (largo > 0) {
        linea[largo] = '\0';
        ejecutarComando(linea);
        largo = 0;
      }
    } else if (largo < (int)sizeof(linea) - 1) {
      linea[largo++] = c;
    }
  }
}

static void atenderBoton() {
  static bool anterior = true;
  static unsigned long ultimoCambio = 0;
  bool actual = digitalRead(PIN_BOTON);
  if (actual != anterior && millis() - ultimoCambio > 50) {
    ultimoCambio = millis();
    anterior = actual;
    if (!actual && estado != GRABANDO) {  // se apreto el boton
      empezarGrabacion();
    }
  }
}

void setup() {
  Serial.begin(230400);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  iniciarSensor();
  Serial.println("# listo: g grabar, x detener, v volcar, f<hz>, s<seg>");
}

void loop() {
  atenderSerial();
  atenderBoton();

  if (estado != GRABANDO) {
    return;
  }

  uint32_t ahora = micros();
  if ((int32_t)(ahora - proximaUs) < 0) {
    return;
  }

  Muestra m;
  if (leerSensor(m)) {
    m.t_us = ahora - inicioUs;
    buffer[cantidad++] = m;
  }
  proximaUs += periodo;
  if ((int32_t)(ahora - proximaUs) > (int32_t)periodo) {
    proximaUs = ahora + periodo;  // se atraso demasiado: no intentar recuperar de golpe
  }
  if (cantidad >= objetivo) {
    terminarGrabacion();
  }
}
