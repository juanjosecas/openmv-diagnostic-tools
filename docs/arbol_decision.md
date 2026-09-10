# Árbol de decisión de diagnóstico

Objetivo: decidir qué probar después sin cambiar varias variables a la vez.

```mermaid
flowchart TD
    A[Inicio: OpenMV H7 Plus + OV5640] --> B{01_versiones.py OK?}
    B -- No --> B1[Firmware/runtime/API sospechoso]
    B1 --> B2[Guardar versión exacta y evidencia antes de actualizar]

    B -- Sí --> C{02_sensor_camara.py completa?}
    C -- No --> C1[Sensor / firmware / alimentación / hardware]
    C -- Sí --> D{04_sd_info.py coherente?}

    D -- No --> D1[Filesystem / SD / montaje]
    D -- Sí --> E{05_sd_escritura.py completa?}
    E -- No --> E1[SD / filesystem / escritura]
    E -- Sí --> F{06_fps_camara.py estable?}

    F -- No --> F1[Sensor / firmware / rendimiento base]
    F -- Sí --> G{11_console_heartbeat.py mantiene salida?}

    G -- No --> G1[Problema de stdio/debug/IDE aun sin cámara ni SD]
    G -- Sí --> H{07_grabacion_mjpeg.py falla o cae FPS?}

    H -- Sí --> H1{write_ms sube y capture_ms queda estable?}
    H1 -- Sí --> H2[Cuello de botella SD/escritura]
    H1 -- No --> H3[Interacción sensor + MJPEG + firmware]

    H -- No --> I[09_grabacion_telemetria.py + monitor USB Windows]
    I --> J{IDE deja de reportar?}
    J -- No --> J1[Extender duración y repetir]

    J -- Sí --> K{CSV/MJPEG siguen creciendo?}
    K -- No --> K1[Cámara/script/SD/alimentación también se detuvieron]
    K -- Sí --> L{Windows registra desconexión USB?}

    L -- Sí --> L1[USB / cable / puerto / energía / driver / firmware]
    L -- No --> M[IDE/debug/framebuffer sospechoso]

    M --> N{Firmware expone omv.disable_fb?}
    N -- Sí --> N1[Ejecutar 10_framebuffer_off_test.py]
    N -- No --> N2[No usar disable_fb; seguir con controles del IDE/protocolo]

    N1 --> O{Sin framebuffer desaparece el problema?}
    O -- Sí --> O1[Hipótesis framebuffer/debug fortalecida]
    O -- No --> O2[Framebuffer no explica por sí solo el fallo]

    O1 --> P[Comparar 12_grabacion_debug_controlado.py con framebuffer False vs True]
    O2 --> P

    P --> Q{Archivo enorme?}
    Q -- Sí --> Q1[Analizar telemetría: duración real, frames, size(), FPS]
    Q -- No --> R[Revisar firmware/IDE como siguiente variable A/B]

    Q1 --> S{Grabó mucho más tiempo de lo previsto?}
    S -- Sí --> S1[Terminación/temporizador/script ejecutado]
    S -- No --> S2[Bytes/frame altos: compresión, resolución, escena o API]
```

## Secuencia corta para el caso actual

```text
1. 01_versiones.py
2. 11_console_heartbeat.py
3. 09_grabacion_telemetria.py + windows/10_monitor_usb_openmv.ps1
4. Si IDE deja de reportar pero el CSV/MJPEG siguen:
   4a. mirar si Windows registró desconexión USB
   4b. si NO hubo desconexión: probar 10_framebuffer_off_test.py
5. Ejecutar 12_grabacion_debug_controlado.py dos veces:
   A) DISABLE_IDE_FRAMEBUFFER = False
   B) DISABLE_IDE_FRAMEBUFFER = True  (sólo firmware que soporte la API)
6. Comparar resultados manteniendo mismo cable, PC, SD, FPS y duración.
```

## Interpretación crítica

Si ocurre:

```text
IDE: deja de mostrar actividad
CSV persistente: sigue agregando registros
MJPEG: sigue creciendo
video final: reproducible
Windows: dispositivo USB sigue presente
```

la cámara sigue ejecutando el trabajo principal y el fallo queda concentrado en la capa IDE/debug/framebuffer/stdio. Eso no identifica todavía cuál de esas piezas es la causa.

Si `11_console_heartbeat.py` también deja de reportar sin usar sensor ni SD, la hipótesis de SD/cámara pierde fuerza y sube mucho la de `stdio`/debug/IDE.

Si `10_framebuffer_off_test.py` cambia el comportamiento en firmware 4.7.x, el framebuffer pasa a ser una variable causal plausible. Si no cambia nada, esa hipótesis queda debilitada.

## Firmware

No usar `omv.disable_fb()` sin detectar primero la API. OpenMV la documenta en versiones antiguas, pero fue eliminada en firmware 4.8.0. El script `10_framebuffer_off_test.py` hace esta comprobación automáticamente.

## Antes de actualizar firmware

No actualizar sólo porque exista una versión nueva. Primero conservar:

- versión exacta;
- logs;
- telemetría;
- comportamiento con framebuffer activo/inactivo;
- monitor USB de Windows.

Después sí puede hacerse un A/B de firmware manteniendo el resto constante.
