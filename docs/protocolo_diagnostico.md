# Protocolo de diagnóstico

## Objetivo

Separar el problema por capas y evitar cambiar varias variables a la vez.

## Antes de empezar

Registrar:

- modelo exacto de OpenMV;
- versión de OpenMV IDE;
- versión de firmware/runtime reportada por `01_versiones.py`;
- versión/build de Windows;
- marca y capacidad de la microSD;
- cable y puerto USB usados;
- descripción exacta del fallo.

No usar sólo «se cuelga». Registrar qué ocurre realmente:

- el IDE deja de responder;
- el terminal deja de imprimir;
- el framebuffer deja de actualizarse;
- Windows pierde el dispositivo USB;
- cambia/desaparece el puerto COM;
- la cámara se reinicia;
- el script imprime una excepción;
- el MJPEG deja de crecer;
- el log persistente deja de crecer;
- el archivo queda corrupto o incompleto.

## Secuencia recomendada

### 1. Runtime, firmware y APIs

Ejecutar `openmv/01_versiones.py`.

Guardar toda la salida. El script también informa, cuando es posible, versión OpenMV, modelo de placa y disponibilidad de APIs como `omv.disable_fb()`.

### 2. Sensor sin almacenamiento

Ejecutar `openmv/02_sensor_camara.py`.

Si falla aquí, la SD no es la causa primaria.

### 3. Memoria

Ejecutar `openmv/03_memoria.py`.

La cifra corresponde al heap de MicroPython, no a toda la RAM física. Usarla sobre todo para comparar ejecuciones.

### 4. Filesystem y espacio libre

Ejecutar `openmv/04_sd_info.py`.

Registrar capacidad, espacio usado y libre. Verificar que el filesystem consultado sea efectivamente el usado por el MJPEG.

### 5. Escritura sin cámara

Ejecutar `openmv/05_sd_escritura.py`.

Si `02_sensor_camara.py` pasa y `05_sd_escritura.py` falla, priorizar almacenamiento/filesystem.

### 6. Rendimiento del sensor

Ejecutar `openmv/06_fps_camara.py`.

Este valor sirve como referencia sin escritura MJPEG.

### 7. Consola/debug sin cámara ni SD

Ejecutar `openmv/11_console_heartbeat.py` durante 20 minutos.

Debe aparecer un mensaje por segundo. Si el terminal deja de mostrar mensajes en una prueba que no usa sensor ni SD, la hipótesis de `stdio`/debug/IDE gana fuerza.

### 8. Grabación MJPEG instrumentada

Ejecutar `openmv/07_grabacion_mjpeg.py`.

Comparar FPS, captura media y escritura media. Si `write_ms` crece mientras `capture_ms` permanece estable, priorizar almacenamiento.

### 9. Telemetría persistente + monitor USB

Ejecutar simultáneamente:

```text
openmv/09_grabacion_telemetria.py
windows/10_monitor_usb_openmv.ps1
```

La telemetría se escribe en la propia cámara y no depende de que el IDE siga mostrando la consola.

Si el IDE deja de reportar, no detener inmediatamente. Esperar algunos minutos y comprobar después si el CSV y el MJPEG siguieron creciendo.

### 10. Prueba de framebuffer

En firmware que todavía exponga `omv.disable_fb()` —incluido el entorno 4.7.x observado— ejecutar:

```text
openmv/10_framebuffer_off_test.py
```

El IDE puede dejar de mostrar imagen durante esta prueba: eso es esperado.

Desde firmware 4.8.0 `omv.disable_fb()` fue eliminado; el script detecta esto y termina sin modificar nada.

### 11. Grabación con debug controlado

Ejecutar `openmv/12_grabacion_debug_controlado.py`.

Para un ensayo A/B en firmware compatible:

```python
DISABLE_IDE_FRAMEBUFFER = False
```

y luego repetir con:

```python
DISABLE_IDE_FRAMEBUFFER = True
```

No cambiar ninguna otra variable entre ambas pruebas.

Este script:

- deja un log persistente;
- hace flush del log;
- usa `Mjpeg.sync()` si la API existe;
- consulta `Mjpeg.size()` y `Mjpeg.count()` si existen;
- imprime por consola con baja frecuencia;
- separa error de captura, escritura y cierre.

### 12. Analizar la telemetría en PC

Con Python 3.10+ y sin dependencias externas:

```bash
python pc/analizar_telemetria.py diagnostico_telemetria.csv
```

El script resume FPS, tiempos de captura/escritura, tamaño reportado del MJPEG y gaps grandes en el log.

## Pruebas A/B útiles

Cambiar una sola variable por vez:

1. mismo equipo + otro cable USB;
2. mismo equipo + otro puerto USB;
3. mismo equipo + otra microSD;
4. misma cámara + otra PC;
5. mismo hardware + IDE cerrado durante grabación;
6. mismo hardware + IDE conectado durante grabación;
7. mismo hardware + framebuffer activo/inactivo, si la versión lo permite;
8. sólo después de guardar evidencia: mismo hardware + otra versión de firmware/IDE.

## Evidencia mínima a conservar

Para cada fallo guardar:

- script utilizado;
- parámetros;
- versión de firmware e IDE;
- salida completa de consola;
- minuto/segundo aproximado del fallo;
- log persistente;
- tamaño final del MJPEG;
- si el archivo puede reproducirse;
- log USB/COM de Windows.

## Sobre actualizaciones de firmware

No actualizar firmware, reinstalar drivers ni reformatear la SD antes de guardar evidencia. Una actualización puede arreglar el problema, pero también elimina la posibilidad de saber qué variable lo causaba.

Después de documentar el comportamiento base, una actualización puede usarse como experimento A/B controlado.

Ver también:

- `docs/arbol_decision.md`
- `docs/interpretacion_resultados.md`
- `docs/referencias.md`
