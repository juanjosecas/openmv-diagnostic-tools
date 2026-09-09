# OpenMV Diagnostic Tools

Toolkit de diagnóstico para cámaras OpenMV y su interacción con Windows.

El objetivo es aislar fallas por capas: firmware/runtime, sensor, memoria, almacenamiento, rendimiento de captura, escritura MJPEG, estabilidad prolongada y comunicación USB con Windows.

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
│   └── grabacion_robusta.py
├── windows/
│   ├── 09_diagnostico_windows_openmv.ps1
│   └── 10_monitor_usb_openmv.ps1
├── docs/
│   ├── protocolo_diagnostico.md
│   └── interpretacion_resultados.md
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

Después ejecutar las herramientas de Windows:

9. `09_diagnostico_windows_openmv.ps1`
10. `10_monitor_usb_openmv.ps1`

No conviene ejecutar todo junto. Si una prueba falla, registrar el mensaje completo antes de cambiar firmware, drivers o hardware.

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
| `09_diagnostico_windows_openmv.ps1` | inventario USB, drivers y eventos | Windows / USB / drivers |
| `10_monitor_usb_openmv.ps1` | cambios USB durante el experimento | desconexiones o reinicios intermitentes |

## Grabación robusta

`openmv/grabacion_robusta.py` es una versión instrumentada del script original. Mantiene la lógica general de grabación MJPEG y agrega comprobación de espacio libre real, separación de errores de captura y escritura, métricas de rendimiento, control de memoria, cierre compatible de MJPEG y mensajes diagnósticos.

Durante diagnóstico se evita reiniciar automáticamente la cámara para que la consola conserve el error.

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

## Regla principal

No asumir que un cuelgue de OpenMV IDE implica que la cámara dejó de grabar. Si el archivo de la microSD continúa creciendo mientras el IDE pierde conexión, el problema está probablemente en USB/Windows/IDE. Si la grabación también se detiene, el problema está más cerca de sensor, firmware, almacenamiento, alimentación o script.

Ver `docs/protocolo_diagnostico.md` para el procedimiento completo.