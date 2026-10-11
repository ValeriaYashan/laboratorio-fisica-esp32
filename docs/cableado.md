# Cableado

El MPU-6050 (módulo GY-521) se conecta por I2C. Alimentalo con **3,3 V**.

| GY-521 | ESP32 DevKit | Nota |
|--------|--------------|------|
| VCC    | 3V3          | Los módulos GY-521 traen regulador, pero con 3,3 V alcanza y es más seguro |
| GND    | GND          | |
| SDA    | GPIO 21      | Pines I2C por defecto |
| SCL    | GPIO 22      | |
| AD0    | GND          | Fija la dirección en 0x68 |

Extras opcionales:

| Componente | Conexión |
|------------|----------|
| Pulsador   | GPIO 4 y GND (el firmware activa la resistencia interna `INPUT_PULLUP`) |
| LED        | El LED integrado en GPIO 2 se enciende mientras graba |

Los pines se cambian en `firmware/src/config.h`.

## Cómo comprobar la conexión

Abrí el monitor serie a 230400 baudios. Si al arrancar aparece `# No se encontro el MPU-6050`, revisá SDA/SCL y la soldadura de los pines. Si aparece un aviso con `WHO_AM_I` distinto de `0x68`, es probable que tu módulo traiga un chip compatible: suele funcionar igual, pero verificá los datos.

## Sentido de los ejes

Los ejes dependen de cómo quede orientada la placa dentro de la caja. Antes de medir, inclinala hacia un lado y mirá qué canal cambia. La marca "+X" de la tapa es una guía: verificala con tu montaje real.
