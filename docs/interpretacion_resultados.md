# Interpretación de resultados

## Tabla rápida

| Resultado | Interpretación principal |
|---|---|
| `01` falla | firmware/runtime/API incompatible o instalación dañada |
| `02` falla | sensor, firmware o hardware; la SD todavía no participa |
| `02` OK + `05` falla | almacenamiento/filesystem/microSD |
| `02` OK + `05` OK + `07` falla | interacción captura + compresión + escritura |
| `06` estable + `07` lento | la escritura/SD introduce el cuello de botella |
| todo OpenMV funciona pero IDE pierde conexión | USB/Windows/IDE |
| cámara reinicia espontáneamente | alimentación, firmware, excepción severa o hardware |
| sólo fallan pruebas largas | problema intermitente, memoria, temperatura, alimentación o SD degradada |

## FPS

No interpretar `DESIRED_FPS` como garantía. El script puede pedir 15 FPS, pero si captura + escritura tardan más de ~66 ms por frame, el FPS efectivo necesariamente cae.

Para 15 FPS:

```text
presupuesto temporal por frame ~= 1000 / 15 ~= 66.7 ms
```

Ejemplo sano:

```text
captura media:   20 ms
escritura media: 10 ms
ciclo:           30 ms
```

Hay margen para esperar hasta el siguiente frame.

Ejemplo con cuello de botella:

```text
captura media:   20 ms
escritura media: 90 ms
ciclo:          110 ms
```

No es físicamente posible sostener 15 FPS en ese caso.

## Espacio libre

El script original estimaba el tamaño del video a partir de un frame JPEG y lo comparaba con un límite fijo de 4096 MB. Eso no demuestra que existan 4096 MB libres.

Las herramientas nuevas consultan el filesystem real y reservan un margen de seguridad.

## Memoria

`gc.mem_free()` reporta memoria libre del heap administrado por MicroPython. No equivale a toda la RAM física ni incluye necesariamente buffers especiales de imagen. Su utilidad principal aquí es comparar estados y detectar degradación durante una prueba.

## USB/Windows

Un cuelgue del IDE y una detención de la grabación son eventos distintos.

- IDE pierde conexión pero MJPEG continúa creciendo: sospechar USB/Windows/IDE.
- MJPEG también se detiene: sospechar cámara/firmware/SD/alimentación/script.
- dispositivo desaparece de PnP/COM: sospechar desconexión o reinicio físico/lógico.
- dispositivo permanece estable pero IDE se congela: sospechar software del IDE o comunicación de depuración.

## Qué comparar entre ejecuciones

Para una misma configuración, registrar:

- FPS promedio;
- captura media en ms;
- escritura media en ms;
- peor escritura en ms;
- heap libre;
- espacio libre;
- timestamp de desconexiones USB;
- tamaño final del MJPEG.

No comparar pruebas realizadas con distinta resolución, formato, FPS o tarjeta SD como si fueran equivalentes.