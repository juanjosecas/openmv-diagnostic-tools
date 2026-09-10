# OpenMV Diagnostic Tools

Toolkit de diagnóstico para cámaras OpenMV y su interacción con Windows.

El objetivo es aislar fallas por capas: firmware/runtime, sensor, memoria, almacenamiento, rendimiento de captura, escritura MJPEG, `stdio`, framebuffer, protocolo de debug, USB y OpenMV IDE.

## Descargar este repositorio sin usar Git

No hace falta instalar `git`, `gh`, GitHub Desktop ni ninguna otra herramienta.

### Opción recomendada: descargar todo como ZIP

1. Abrir en el navegador:

   `https://github.com/juanjosecas/openmv-diagnostic-tools`

2. Presionar el botón verde **Code**.
3. Elegir **Download ZIP**.
4. Esperar a que termine la descarga.
5. Abrir la carpeta de Descargas de Windows.
6. Buscar:

   ```text
   openmv-diagnostic-tools-main.zip
   ```

7. Clic derecho → **Extraer todo...**.
8. Abrir:

   ```text
   openmv-diagnostic-tools-main
   ```

Los scripts para la cámara están en `openmv`, las herramientas Windows en `windows`, el analizador para PC en `pc` y la documentación en `docs`.

### Descargar sólo un archivo

1. Abrir el repositorio.
2. Entrar en la carpeta correspondiente.
3. Abrir el archivo.
4. Presionar **Raw** o **Download raw file**.
5. Guardarlo conservando la extensión (`.py`, `.ps1`, `.md`).

Para alguien que no usa GitHub habitualmente, descargar el ZIP completo es más simple y evita dejar documentación o herramientas afuera.

## Estructura

```text
openmv-diagnostic-tools/
├── README.md
├── openmv/
│   ├── 01_versiones.py
│   ├── 02_sensor_camara.py
│   ├── 03_memoria.py
│   ├── 04_sd_info.py
│   ├── 05_sd_escritura.py
│   ├── 06_fps_camara.py
│   ├── 07_grabacion_mjpeg.py
│   ├── 08_estabilidad.py
│   ├── 09_grabacion_telemetria.py
│   ├── 10_framebuffer_off_test.py
│   ├── 11_console_heartbeat.py
│   ├── 12_grabacion_debug_controlado.py
│   └── grabacion_robusta.py
├── windows/
│   ├── 09_diagnostico_windows_openmv.ps1
│   └── 10_monitor_usb_openmv.ps1
├── pc/
│   └── analizar_telemetria.py
├── docs/
│   ├── protocolo_diagnostico.md
│   ├── interpretacion_resultados.md
│   ├── arbol_decision.md
│   └── referencias.md
└── original/
    └── script_esteban_original.py
```

## Caso que motivó la ampliación del diagnóstico

Se observó un patrón particularmente informativo:

```text
OpenMV IDE deja de reportar actividad aproximadamente durante la grabación
pero la cámara continúa escribiendo el MJPEG
el archivo final aparece y es reproducible
el problema se observó en más de una PC
```

Eso obliga a separar dos preguntas:

1. ¿la cámara dejó de ejecutar el script?
2. ¿o solamente dejó de funcionar correctamente alguna parte de la comunicación IDE/debug/preview?

Las herramientas nuevas están diseñadas para distinguir esos casos.

## Orden recomendado

Primero las pruebas que aíslan componentes:

1. `01_versiones.py` — firmware, placa y APIs disponibles.
2. `02_sensor_camara.py` — sensor sin SD.
3. `03_memoria.py` — heap MicroPython.
4. `04_sd_info.py` — filesystem y espacio libre.
5. `05_sd_escritura.py` — escritura sin cámara.
6. `06_fps_camara.py` — FPS del sensor sin MJPEG.
7. `11_console_heartbeat.py` — sólo terminal/debug, sin cámara ni SD.
8. `07_grabacion_mjpeg.py` — captura + MJPEG instrumentado.
9. `08_estabilidad.py` — captura prolongada.

Si el problema sigue siendo intermitente:

10. ejecutar `09_grabacion_telemetria.py`;
11. simultáneamente ejecutar `windows/10_monitor_usb_openmv.ps1`;
12. si el IDE falla pero la cámara sigue trabajando, probar `10_framebuffer_off_test.py` en firmware compatible;
13. ejecutar `12_grabacion_debug_controlado.py` como ensayo A/B con framebuffer activo/inactivo cuando la API lo permita.

No ejecutar todo junto desde el principio. Cada prueba está pensada para eliminar hipótesis.

## Qué prueba cada herramienta

| Herramienta | Qué prueba | Si falla o cambia el resultado |
|---|---|---|
| `01_versiones.py` | firmware, placa, runtime y APIs | incompatibilidad/versionado |
| `02_sensor_camara.py` | captura sin SD | sensor/firmware/hardware |
| `03_memoria.py` | heap MicroPython | presión/fragmentación de memoria |
| `04_sd_info.py` | filesystem/espacio | SD/montaje/filesystem |
| `05_sd_escritura.py` | escritura sin sensor | SD/almacenamiento |
| `06_fps_camara.py` | rendimiento base del sensor | sensor/firmware/configuración |
| `11_console_heartbeat.py` | `stdio`/debug sin sensor ni SD | IDE/debug/comunicación |
| `07_grabacion_mjpeg.py` | captura + escritura MJPEG | interacción sensor/SD/MJPEG |
| `08_estabilidad.py` | captura prolongada | fallos intermitentes |
| `09_grabacion_telemetria.py` | grabación + CSV persistente | reconstrucción posterior al cuelgue del IDE |
| `10_framebuffer_off_test.py` | elimina preview/framebuffer como variable | framebuffer/debug |
| `12_grabacion_debug_controlado.py` | grabación con log persistente y controles de debug | comparación A/B reproducible |
| `09_diagnostico_windows_openmv.ps1` | USB, COM, drivers, eventos | Windows/USB/driver/energía |
| `10_monitor_usb_openmv.ps1` | desconexiones durante el experimento | USB físico/lógico |
| `pc/analizar_telemetria.py` | análisis automático del CSV | gaps, caída de FPS, escritura lenta |

## `grabacion_robusta.py`

Es la versión corregida para uso práctico del script original. Mantiene una configuración simple de grabación pero agrega:

- espacio libre real;
- captura y escritura medidas por separado;
- log persistente independiente de la consola del IDE;
- `flush()` del log;
- `os.sync()` cuando existe;
- `Mjpeg.sync()` cuando la API lo soporta;
- `Mjpeg.size()` y `Mjpeg.count()` cuando están disponibles;
- heartbeat de consola deliberadamente poco frecuente;
- separación entre errores de captura, escritura y cierre;
- opción A/B para desactivar framebuffer en firmware que todavía exponga `omv.disable_fb()`;
- sin reinicio automático al terminar, para no destruir evidencia.

## Prueba específica de consola/debug

`openmv/11_console_heartbeat.py` no usa sensor ni SD. Sólo imprime un contador una vez por segundo durante 20 minutos.

Si deja de reportar aproximadamente al mismo tiempo que el script de video, ya no tiene sentido culpar a la microSD o a `mjpeg.add_frame()` como explicación única.

## Prueba específica del framebuffer

`openmv/10_framebuffer_off_test.py` intenta ejecutar una prueba con el streaming del framebuffer desactivado desde la cámara.

Esto es especialmente útil para firmware 4.7.x, donde OpenMV documentaba `omv.disable_fb()`.

**Importante:** OpenMV eliminó `omv.disable_fb()` en firmware 4.8.0. El script comprueba primero si la función existe y no intenta usarla si no está disponible.

Por eso no hay que copiar esta prueba ciegamente después de actualizar firmware.

## Telemetría persistente

`openmv/09_grabacion_telemetria.py` genera:

```text
diagnostico_video.mjpeg
diagnostico_telemetria.csv
```

Registra periódicamente, cuando las APIs están disponibles:

```text
time_s
frames
mjpeg_count
fps
capture_ms_avg
capture_ms_max
write_ms_avg
write_ms_max
mjpeg_size_bytes
heap_free
free_mb
mjpeg_sync
status
```

El CSV se fuerza al almacenamiento periódicamente. La idea es poder responder después del experimento:

- ¿cuánto tiempo siguió vivo el script?
- ¿cuántos frames añadió?
- ¿cayó el FPS?
- ¿aumentó el tiempo de escritura?
- ¿el MJPEG siguió creciendo después de que desaparecieron los mensajes del IDE?

## Analizar el CSV en la PC

Requiere Python 3.10+ y sólo usa biblioteca estándar:

```bash
python pc/analizar_telemetria.py diagnostico_telemetria.csv
```

Busca, entre otras cosas, gaps grandes entre registros, caída de FPS y predominio del tiempo de escritura sobre captura.

## Windows

Diagnóstico puntual:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\09_diagnostico_windows_openmv.ps1 *> diagnostico_openmv_windows.txt
```

Monitor durante la grabación:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\10_monitor_usb_openmv.ps1
```

Conviene comparar tres estados:

- cámara desconectada;
- cámara conectada y funcionando;
- inmediatamente después del fallo.

## Cómo interpretar el síntoma actual

Si ocurre:

```text
IDE: deja de reportar
MJPEG: sigue creciendo
telemetría: sigue creciendo
video final: reproducible
```

entonces la ausencia de actividad en la pantalla no demuestra que la cámara haya dejado de ejecutar.

Si además Windows mantiene el dispositivo USB presente, la hipótesis de IDE/debug/framebuffer/stdio gana fuerza.

Si Windows registra desconexión/reconexión al mismo tiempo, priorizar cable, puerto, power management, driver, firmware USB/debug o hardware USB de la placa.

## Firmware e IDE

El entorno observado inicialmente utiliza firmware OpenMV 4.7.0. Releases posteriores modificaron de forma sustancial framebuffer y protocolo USB/debug.

Eso **no demuestra** que 4.7.0 sea la causa. Primero conviene registrar el comportamiento con la versión actual y recién después usar una actualización como ensayo A/B.

Además, desde firmware 4.8.0 hubo cambios de API: entre ellos se eliminó `omv.disable_fb()`. En 5.0.0 OpenMV introdujo un protocolo host/cámara nuevo con canales separados para `stdio`, preview y datos, CRC y recuperación de secuencia; el IDE 5.0.0 también incorpora logging del protocolo de debug.

## Documentación y antecedentes

Las hipótesis y pruebas no salen sólo de inferencia. `docs/referencias.md` reúne:

- documentación oficial de `omv`, `mjpeg`, `gc` y filesystem;
- changelogs de firmware e IDE;
- explicación histórica de cómo el IDE sondea el framebuffer por USB;
- antecedentes del foro donde ejecución del script, terminal y framebuffer muestran comportamientos distintos.

Los casos de foro se presentan como antecedentes análogos, no como prueba de que exista exactamente el mismo bug.

## Árbol de decisión

Ver [`docs/arbol_decision.md`](docs/arbol_decision.md).

## Documentación adicional

- [`docs/protocolo_diagnostico.md`](docs/protocolo_diagnostico.md)
- [`docs/interpretacion_resultados.md`](docs/interpretacion_resultados.md)
- [`docs/arbol_decision.md`](docs/arbol_decision.md)
- [`docs/referencias.md`](docs/referencias.md)
