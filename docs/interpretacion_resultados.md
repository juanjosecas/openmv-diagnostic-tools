# Interpretación de resultados

## Tabla rápida

| Resultado | Interpretación principal |
|---|---|
| `01` falla | firmware/runtime/API incompatible o instalación dañada |
| `02` falla | sensor, firmware o hardware; la SD todavía no participa |
| `02` OK + `05` falla | almacenamiento/filesystem/microSD |
| `06` inestable sin grabación | sensor/firmware/rendimiento base |
| `11_console_heartbeat.py` deja de reportar | `stdio`/debug/IDE aun sin cámara ni SD |
| `06` estable + `07` lento | la escritura/SD introduce el cuello de botella |
| IDE deja de reportar pero CSV/MJPEG siguen creciendo | ejecución de cámara sigue viva; concentrarse en IDE/debug/USB/framebuffer |
| Windows registra desconexión USB | cable/puerto/energía/driver/USB firmware/hardware |
| Windows no registra desconexión y el trabajo sigue | IDE/debug/framebuffer/stdio gana peso |
| `10_framebuffer_off_test.py` elimina el problema | framebuffer/debug se vuelve variable causal plausible |
| cámara reinicia espontáneamente | alimentación, firmware, excepción severa o hardware |

## FPS

No interpretar `DESIRED_FPS` como garantía. Para 15 FPS el presupuesto temporal es aproximadamente:

```text
1000 / 15 ~= 66.7 ms por frame
```

Si captura + escritura supera ese tiempo, el FPS real necesariamente cae.

## Tamaño del MJPEG

Un archivo de varios GB no demuestra corrupción. Hay que mirar simultáneamente:

- duración real;
- frames escritos;
- FPS efectivo;
- `Mjpeg.size()` si la versión lo soporta;
- tiempo medio y máximo de escritura.

Dos grabaciones de igual duración no tienen por qué ocupar exactamente lo mismo: MJPEG comprime cada frame de forma independiente y el tamaño depende del contenido de imagen y de la compresión.

## `Mjpeg.sync()`

En versiones recientes OpenMV expone `Mjpeg.sync()` para forzar el volcado al disco sin cerrar el archivo. Las herramientas del repositorio lo usan sólo mediante detección de capacidad, para no romper firmware que no lo implemente.

## Framebuffer y consola

Framebuffer, terminal y ejecución del script son capas distintas.

Casos útiles:

```text
terminal deja de imprimir
+ log persistente sigue creciendo
+ MJPEG sigue creciendo
```

=> la ausencia de mensajes en pantalla no implica que el script haya parado.

```text
framebuffer deja de actualizarse
+ terminal sigue imprimiendo
```

=> problema concentrado en preview/framebuffer.

```text
terminal + framebuffer paran
+ Windows mantiene el dispositivo
+ log persistente sigue creciendo
```

=> sospecha fuerte sobre IDE/protocolo debug/stdio, no sobre la adquisición.

## Firmware 4.7.x y `omv.disable_fb()`

En ramas antiguas OpenMV documentaba `omv.disable_fb(True)` para impedir que la cámara enviara imágenes al IDE. Desde firmware 4.8.0 esa API fue eliminada.

Por eso nunca hay que asumir que existe: los scripts la detectan antes de usarla.

## Memoria

`gc.mem_free()` reporta heap MicroPython, no toda la RAM física ni necesariamente buffers especiales de imagen. Se usa principalmente para comparar estados y detectar degradación.

## USB/Windows

- IDE pierde conexión y Windows también pierde el dispositivo: priorizar USB físico/driver/energía/firmware.
- IDE falla pero Windows mantiene USB y la cámara sigue escribiendo: priorizar IDE/debug/framebuffer/stdio.
- ocurre en dos PCs distintas: reduce la probabilidad de un problema específico de una sola instalación de Windows, aunque no elimina cable, driver genérico o comportamiento del firmware.

## Evidencia y causalidad

Una mejora observada después de cambiar firmware, cable o configuración no prueba automáticamente la causa. Para atribuir causalidad, repetir un A/B cambiando una sola variable.

Ver `docs/referencias.md` para el origen documental de estas hipótesis.