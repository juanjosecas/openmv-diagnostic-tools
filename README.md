# OpenMV Diagnostic Tools

Toolkit de diagnóstico para cámaras OpenMV y su interacción con Windows.

El objetivo es aislar fallas por capas: firmware/runtime, sensor, memoria, almacenamiento, rendimiento de captura, escritura MJPEG, estabilidad prolongada y comunicación USB con Windows.

## Descargar este repositorio sin usar Git

No hace falta instalar `git`, `gh`, GitHub Desktop ni ninguna otra herramienta.

### Opción recomendada: descargar todo como ZIP

1. Abrir en el navegador:

   `https://github.com/juanjosecas/openmv-diagnostic-tools`

2. Presionar el botón verde **Code**.
3. Elegir **Download ZIP**.
4. Esperar a que termine la descarga.
5. Abrir la carpeta de Descargas de Windows.
6. Buscar un archivo similar a:

   ```text
   openmv-diagnostic-tools-main.zip
   ```

7. Hacer clic derecho sobre el ZIP y elegir **Extraer todo...**.
8. Abrir la carpeta extraída:

   ```text
   openmv-diagnostic-tools-main
   ```

Dentro estarán las carpetas `openmv`, `windows`, `docs` y `original`.

### Qué archivo usar después de descargar

Los scripts que se ejecutan dentro de la cámara están en:

```text
openmv-diagnostic-tools-main\openmv\
```

Los scripts de diagnóstico de Windows están en:

```text
openmv-diagnostic-tools-main\windows\
```

La documentación está en:

```text
openmv-diagnostic-tools-main\docs\
```

### Descargar sólo un archivo

Si sólo se necesita un script:

1. Abrir el repositorio en el navegador.
2. Entrar en la carpeta correspondiente, por ejemplo `openmv`.
3. Hacer clic sobre el archivo deseado, por ejemplo `01_versiones.py`.
4. Presionar **Raw** o **Download raw file**.
5. Guardar el archivo manteniendo su extensión original (`.py`, `.ps1`, `.md`, etc.).

Para alguien que no usa GitHub habitualmente, es preferible descargar el ZIP completo. Así se conservan todas las herramientas y la documentación juntas.

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
│   └── grabacion_robusta.py
├── windows/
│   ├── 09_diagnostico_windows_openmv.ps1
│   └── 10_monitor_usb_openmv.ps1
├── docs/
│   ├── protocolo_diagnostico.md
│   ├── interpretacion_resultados.md
│   └── arbol_decision.md
└── original/
    └── script_esteban_original.py
```

## Orden recomendado

Ejecutar los scripts OpenMV en este orden:

1. `01_versiones.py`
2. `02_sensor_camara.py`
3. `03_memoria.py`
4. `04_sd_info.py`
5. `05_sd_escritura.py`
6. `06_fps_camara.py`
7. `07_grabacion_mjpeg.py`
8. `08_estabilidad.py`

Si todo lo anterior funciona y el problema sigue siendo intermitente:

9. ejecutar `openmv/09_grabacion_telemetria.py`;
10. al mismo tiempo ejecutar `windows/10_monitor_usb_openmv.ps1`.

No conviene ejecutar todas las pruebas juntas desde el principio. Cada script está pensado para aislar una capa concreta.

## Qué prueba cada capa

| Script | Qué prueba | Si falla, sospechar |
|---|---|---|
| `01_versiones.py` | runtime y módulos básicos | firmware / instalación OpenMV |
| `02_sensor_camara.py` | captura repetida sin SD | sensor / firmware / hardware |
| `03_memoria.py` | heap MicroPython | presión o fragmentación de memoria |
| `04_sd_info.py` | filesystem y espacio libre | SD / montaje / filesystem |
| `05_sd_escritura.py` | escritura sostenida sin cámara | SD / almacenamiento |
| `06_fps_camara.py` | rendimiento de captura sin SD | sensor / configuración / firmware |
| `07_grabacion_mjpeg.py` | captura + escritura MJPEG | interacción sensor + SD |
| `08_estabilidad.py` | funcionamiento prolongado | fallas intermitentes / alimentación / temperatura |
| `09_grabacion_telemetria.py` | grabación real + CSV persistente | reconstrucción del fallo aunque el IDE muera |
| `09_diagnostico_windows_openmv.ps1` | inventario USB, drivers y eventos | Windows / USB / drivers |
| `10_monitor_usb_openmv.ps1` | cambios USB durante el experimento | desconexiones o reinicios intermitentes |

## Grabación robusta

`openmv/grabacion_robusta.py` es una versión instrumentada del script original. Mantiene la lógica general de grabación MJPEG y agrega comprobación de espacio libre real, separación de errores de captura y escritura, métricas de rendimiento, control de memoria, cierre compatible de MJPEG y mensajes diagnósticos.

Durante diagnóstico se evita reiniciar automáticamente la cámara para que la consola conserve el error.

## Grabación con telemetría persistente

`openmv/09_grabacion_telemetria.py` está pensada para el caso en el que OpenMV IDE deja de responder pero no sabemos si la cámara siguió ejecutando el script.

Genera dos archivos:

```text
diagnostico_video.mjpeg
diagnostico_telemetria.csv
```

El CSV registra periódicamente:

```text
time_s
frames
fps
capture_ms_avg
write_ms_avg
write_ms_max
heap_free
free_mb
status
```

Si el IDE queda congelado pero el CSV y el MJPEG siguen creciendo, la cámara sigue ejecutando. En ese caso la sospecha pasa hacia USB, debug framebuffer, OpenMV IDE o firmware de comunicación.

## Uso en Windows

Abrir PowerShell en la carpeta `windows/`.

Diagnóstico puntual:

```powershell
powershell -ExecutionPolicy Bypass -File .\09_diagnostico_windows_openmv.ps1 *> diagnostico_openmv_windows.txt
```

Monitor de conexión durante un experimento:

```powershell
powershell -ExecutionPolicy Bypass -File .\10_monitor_usb_openmv.ps1
```

Para comparar estados, conviene guardar tres diagnósticos:

- cámara desconectada;
- cámara conectada y funcionando;
- inmediatamente después del fallo.

## Caso de uso crítico: IDE congelado pero video grabado

Si ocurre:

```text
OpenMV IDE: sin imagen / FPS 0
MJPEG: continúa creciendo
CSV de telemetría: continúa creciendo
VLC: reproduce el archivo final
```

no corresponde concluir que la cámara se colgó. El proceso de adquisición y escritura sigue funcionando y el fallo está más probablemente en la capa de comunicación/debug/IDE.

Si, además, el monitor de Windows registra una desconexión USB, priorizar cable, puerto, administración de energía, firmware USB/debug y hardware USB de la placa.

## Archivos MJPEG muy grandes

Un archivo de varios GB no demuestra por sí mismo corrupción. Primero verificar en el CSV:

- cuánto tiempo grabó realmente;
- cuántos frames acumuló;
- FPS efectivo;
- si el tiempo de escritura aumentó;
- si la grabación siguió mucho después de que el IDE dejó de mostrar imagen.

## Árbol de decisión

Ver [`docs/arbol_decision.md`](docs/arbol_decision.md). Incluye un diagrama Mermaid y una versión textual para decidir qué prueba ejecutar según el resultado anterior.

## Regla principal

No asumir que un cuelgue de OpenMV IDE implica que la cámara dejó de grabar. Si el archivo de la microSD continúa creciendo mientras el IDE pierde conexión, el problema está probablemente en USB/Windows/IDE. Si la grabación también se detiene, el problema está más cerca de sensor, firmware, almacenamiento, alimentación o script.

Ver también:

- [`docs/protocolo_diagnostico.md`](docs/protocolo_diagnostico.md)
- [`docs/interpretacion_resultados.md`](docs/interpretacion_resultados.md)
- [`docs/arbol_decision.md`](docs/arbol_decision.md)
