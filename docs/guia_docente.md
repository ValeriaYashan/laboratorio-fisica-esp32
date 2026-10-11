# Guía docente (propuesta)

Secuencia de unas 10 clases, pensada para trabajo en grupos de 3 o 4. Los tiempos son orientativos y la vinculación con el diseño curricular de Física depende del año y de la jurisdicción: conviene ajustarla con el profesor o la profesora de Física.

| Clase | Foco | Producto |
|-------|------|----------|
| 1 | Pregunta y modelo: ¿de qué depende el período de un péndulo? ¿Y la frecuencia de una viga? | Hipótesis escritas |
| 2 | Electrónica: cableado del sensor y lectura de prueba | Sensor respondiendo |
| 3 | Firmware: grabar y volcar datos por serie | Primer CSV propio |
| 4 | Calibración y ruido: registro en reposo | Parámetros de calibración |
| 5 | Péndulo: medir períodos con distintos largos y estimar g | Gráfico T² vs L |
| 6 | Diseño 3D: caja y soporte | Piezas impresas |
| 7 | Viga: espectros y ley de potencia | Exponente medido |
| 8 | UX: mejorar el panel de visualización con ayuda de IA | Panel ajustado |
| 9 | Informe con incertidumbre, resumen en inglés | Borrador |
| 10 | Cierre: presentación y coevaluación | Rúbrica completada |

## Seguridad

- No hagas pruebas de caída con el equipo sin protección.
- Péndulo: ángulos pequeños, menos de unos 15°, y masas fijas con nudos seguros.
- Las vigas impresas pueden quebrarse: usar protección ocular en las pruebas de flexión.
- La impresora 3D se usa con supervisión de un adulto.
- Alimentar por USB; no manipular baterías de litio sueltas.

## Límites que conviene hablar con el curso

- El MPU-6050 es un sensor modesto: necesita calibración y tiene ruido y deriva.
- La incertidumbre del ajuste no incluye los errores sistemáticos (largo mal medido, ángulo grande, masa del sensor en la viga). Que los estudiantes los busquen es parte del aprendizaje.
- Pegar el sensor en la punta de la viga cambia la masa y por lo tanto la frecuencia.
- Los datos de `datos/ejemplo/` son simulados: sirven para probar el análisis antes de medir y no son resultados experimentales.

## Competencias que se trabajan

Creatividad, comunicación, pensamiento crítico, carácter, colaboración y ciudadanía (uso responsable de la IA y de los datos).
