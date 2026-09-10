# Referencias técnicas y origen de las hipótesis

Este documento separa tres niveles de evidencia:

1. **documentación oficial de OpenMV**;
2. **changelogs oficiales de firmware/IDE**;
3. **casos y explicaciones del foro/issues**, útiles como antecedentes pero no equivalentes a una reproducción exacta del problema actual.

## 1. Documentación oficial

### Módulo `omv` y control del framebuffer

OpenMV documenta `omv.disable_fb(True)` en versiones anteriores a 4.8.0. La función evita que la cámara comprima y transmita imágenes al OpenMV IDE. La documentación aclara que el IDE puede seguir sondeando imágenes y que este flag es distinto del control `Disable FB` del propio IDE.

Referencia:

- https://docs.openmv.io/v4.5.8/library/omv.omv.html

**Hipótesis derivada:** si una grabación funciona con framebuffer desactivado y presenta problemas con framebuffer activo, la capa de preview/debug USB pasa a ser sospechosa.

### Grabación MJPEG

La documentación actual de `mjpeg.Mjpeg` describe `add_frame()`, `count()`, `size()`, `sync()` y `close()`. `sync()` fuerza el volcado del archivo al disco sin cerrarlo y está pensado para llamarse periódicamente durante grabaciones largas.

Referencia:

- https://docs.openmv.io/dev/library/omv.mjpeg.html

**Ideas derivadas:**

- guardar `count()` y `size()` cuando la versión de firmware los expone;
- ejecutar `sync()` periódicamente si está disponible;
- no asumir que un archivo abierto debe aparecer inmediatamente como archivo final utilizable en el explorador;
- distinguir entre frames capturados por el script y frames realmente añadidos al MJPEG.

### Memoria MicroPython

`gc.mem_free()` y `gc.mem_alloc()` permiten medir el heap administrado por MicroPython. No representan toda la RAM física de la placa.

Referencias:

- https://docs.openmv.io/dev/library/gc.html
- https://docs.openmv.io/dev/develop/memorymgt.html

### Filesystem

`os.statvfs()` permite consultar estadísticas del filesystem y `os.sync()` fuerza sincronización cuando está disponible.

Referencia:

- https://docs.openmv.io/dev/library/os.html

## 2. Cambios relevantes entre firmware/IDE

### Firmware / IDE 4.7.0

El equipo observado actualmente usa firmware 4.7.0. El changelog de esa versión sirve como referencia del entorno base.

- https://docs.openmv.io/dev/changelog/ide/v4.7.0.html

### Firmware 4.8.0

La versión 4.8.0 introdujo cambios importantes en framebuffer y protocolo/debug USB. También eliminó `omv.disable_fb()`, por lo que los scripts de este repositorio detectan la API antes de usarla.

El changelog menciona, entre otras cosas:

- cambios en manejo de framebuffer;
- cambios en USB debug;
- eliminación de comandos USBDBG obsoletos;
- descarte de comandos no soportados de IDE antiguos para evitar fallos en placas TinyUSB;
- eliminación de `omv.disable_fb()`.

Referencia:

- https://docs.openmv.io/dev/changelog/firmware/v4.8.0.html

**Consecuencia práctica:** no copiar ciegamente una solución basada en `omv.disable_fb()` a firmware >=4.8.0.

### IDE 4.8.1

El IDE 4.8.1 añadió soporte para OpenMV Debug Protocol V2 y correcciones de confiabilidad relacionadas con el binding del disco.

Referencia:

- https://github.com/openmv/openmv-ide/releases

### Firmware/IDE 5.0.0

OpenMV 5.0.0 reconstruyó el enlace host/cámara como OpenMV Protocol V2. La documentación describe:

- tramas secuenciadas y con CRC;
- recuperación ante huecos de secuencia;
- canales separados para `stdio`, preview y datos de usuario;
- FPS de cámara y FPS mostrado por IDE por separado;
- logging del protocolo desde la terminal serie del IDE.

Referencias:

- https://docs.openmv.io/dev/changelog/ide/v5.0.0.html
- https://docs.openmv.io/v5.0.0/changelog/firmware/v5.0.0.html

Esto no demuestra que 4.7.0 tenga un bug concreto, pero sí demuestra que OpenMV modificó sustancialmente esta capa en releases posteriores.

## 3. Antecedentes en foros e issues

### Cómo funciona históricamente el framebuffer del IDE

Una explicación de desarrolladores de OpenMV describe que el IDE sondea frames mediante solicitudes USB y que, en la implementación histórica, una captura puede esperar a que el IDE termine de leer el frame solicitado antes de sobrescribirlo.

- https://forums.openmv.io/t/frame-buffer-sensor-snapshot/101

Este antecedente es importante porque demuestra acoplamiento entre `sensor.snapshot()` y la transferencia de preview/debug en versiones históricas. No implica que el comportamiento interno sea idéntico en todas las versiones posteriores.

### Script que continúa ejecutándose aunque se quite USB

En el foro, un desarrollador de OpenMV indica que se puede desconectar la cámara del IDE mientras el script está ejecutándose y éste puede continuar corriendo.

- https://forums.openmv.io/t/run-onboard-script-automatically-after-disconnecting-from-computer/5879

Esto apoya la separación conceptual entre:

- ejecución del script en la cámara;
- estado de la conexión con el IDE.

### Recomendación de persistir errores en archivo

Ante ejecución autónoma, desarrolladores de OpenMV recomiendan capturar excepciones y escribirlas a un archivo para poder diagnosticarlas después.

- https://forums.openmv.io/t/development-questions/1526
- https://forums.openmv.io/t/runtime-error-handling-while-running-scripts/7104

De aquí surge el uso de logs persistentes en este repositorio.

### Caso análogo: framebuffer que deja de refrescar

Existe un reporte donde el terminal seguía mostrando `print()` pero el framebuffer dejaba de actualizarse y parecía que la cámara estaba congelada. El caso no es idéntico al actual y utilizaba software antiguo, por lo que sólo se considera evidencia de que preview/terminal/ejecución pueden divergir.

- https://forums.openmv.io/t/the-ide-debug-windows-shows-the-print-data-but-the-bufferframe-doesnt-refresh/9077

## 4. Estado de la hipótesis actual

Observación del caso:

```text
IDE deja de reportar / mostrar actividad
+ MJPEG sigue creciendo
+ video final es reproducible
+ problema aparece en más de una PC
```

Interpretación de trabajo:

```text
la ejecución y escritura en la cámara probablemente continúan
mientras alguna parte de IDE / debug / USB deja de actualizarse
```

Esto sigue siendo una **hipótesis**, no una causa demostrada.

Las pruebas diseñadas para falsarla son:

1. `11_console_heartbeat.py`: prueba `stdio/debug` sin sensor ni SD.
2. `10_framebuffer_off_test.py`: en firmware compatible, elimina el streaming de framebuffer como variable.
3. `09_grabacion_telemetria.py`: persiste telemetría aunque la consola deje de verse.
4. `12_grabacion_debug_controlado.py`: combina logging persistente, sync del MJPEG y control A/B del framebuffer.
5. `windows/10_monitor_usb_openmv.ps1`: comprueba si Windows realmente pierde el dispositivo USB/COM.

Una hipótesis sólo se considera fortalecida cuando una de estas pruebas cambia el resultado manteniendo las demás variables constantes.
