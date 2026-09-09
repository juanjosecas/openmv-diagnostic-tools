# Árbol de decisión de diagnóstico

Objetivo: decidir qué probar después sin cambiar varias cosas a la vez.

```mermaid
flowchart TD
    A[Inicio: OpenMV H7 Plus + OV5640] --> B{¿01_versiones.py corre bien?}
    B -- No --> B1[Firmware/runtime/API sospechoso\nRegistrar versión exacta y módulos faltantes]
    B1 --> Z1[No actualizar todavía: guardar evidencia]

    B -- Sí --> C{¿02_sensor_camara.py completa 100 capturas?}
    C -- No --> C1[Problema antes de la SD\nSensor / firmware / alimentación / hardware]
    C1 --> C2[Probar otro cable/puerto/alimentación y repetir]

    C -- Sí --> D{¿04_sd_info.py ve espacio y filesystem coherentes?}
    D -- No --> D1[Filesystem/SD/montaje sospechoso]
    D1 --> D2[Probar otra microSD conocida y repetir]

    D -- Sí --> E{¿05_sd_escritura.py completa sin error?}
    E -- No --> E1[SD/filesystem/escritura sospechosa]
    E1 --> E2[Otra SD / revisar formato / repetir]

    E -- Sí --> F{¿06_fps_camara.py es estable?}
    F -- No --> F1[Sensor/firmware/rendimiento base inestable]
    F1 --> F2[Comparar con otra resolución/FPS sin tocar SD]

    F -- Sí --> G{¿07_grabacion_mjpeg.py falla o cae mucho el FPS?}
    G -- Sí --> G1{¿Sube write_ms y capture_ms sigue estable?}
    G1 -- Sí --> G2[Cuello de botella en escritura/SD]
    G1 -- No --> G3[Interacción sensor + MJPEG + firmware]

    G -- No --> H[Ejecutar 09_grabacion_telemetria.py + monitor USB Windows]

    H --> I{¿OpenMV IDE se congela?}
    I -- No --> I1[No se reprodujo el problema\nExtender duración y repetir]

    I -- Sí --> J{¿El CSV de telemetría sigue agregando filas?}
    J -- Sí --> K{¿El monitor USB registra desconexión?}
    K -- Sí --> K1[Problema USB / driver / cable / power management / firmware debug]
    K -- No --> K2[IDE/debug framebuffer sospechoso\nLa cámara sigue ejecutando]

    J -- No --> L{¿El MJPEG también deja de crecer?}
    L -- Sí --> L1[Cámara/script/SD/alimentación también se detuvieron]
    L -- No --> L2[Telemetría falló pero grabación siguió\nRevisar escritura del log]

    K1 --> M{¿Ocurre en dos PCs?}
    M -- Sí --> M1[PC específica poco probable\nPriorizar cámara/cable/firmware/USB de la placa]
    M -- No --> M2[Comparar drivers, energía USB y puerto físico]

    K2 --> N{¿El video final se reproduce en VLC?}
    N -- Sí --> N1[Grabación funcional; fallo concentrado en IDE/debug]
    N -- No --> N2[Revisar cierre MJPEG y corrupción del archivo]

    N1 --> O{¿El archivo es mucho más grande de lo esperado?}
    O -- Sí --> O1[Ver duración real en telemetría y frames registrados]
    O1 --> O2{¿Grabó mucho más tiempo de lo previsto?}
    O2 -- Sí --> O3[Problema de terminación/tiempo o versión de script ejecutada]
    O2 -- No --> O4[Tamaño/frame anormal: revisar compresión, resolución y contenido]

    O -- No --> P[Problema principal probablemente USB/IDE]
```

## Versión operativa corta

```text
¿El sensor solo funciona?
│
├─ NO -> sensor / firmware / alimentación / hardware
│
└─ SÍ
   │
   ¿La SD escribe bien sin cámara?
   │
   ├─ NO -> SD / filesystem
   │
   └─ SÍ
      │
      ¿La cámara mantiene FPS sin grabar?
      │
      ├─ NO -> sensor / firmware / rendimiento base
      │
      └─ SÍ
         │
         ¿MJPEG se vuelve lento o falla?
         │
         ├─ SÍ -> comparar tiempo de captura vs escritura
         │          ├─ escritura alta -> SD
         │          └─ ambos raros -> firmware / interacción MJPEG
         │
         └─ NO
            │
            Ejecutar telemetría + monitor USB
            │
            ¿IDE se congela pero CSV/MJPEG siguen?
            │
            ├─ SÍ -> USB / IDE / debug; cámara sigue viva
            │
            └─ NO -> si CSV y MJPEG paran, el problema también está en la cámara
```

## Caso actualmente más interesante

Si ocurre simultáneamente:

```text
OpenMV IDE: sin imagen / FPS 0
MJPEG: sigue creciendo
CSV de telemetría: sigue creciendo
VLC: reproduce el archivo después
```

la interpretación principal es que el proceso de adquisición/grabación dentro de la OpenMV sigue vivo y el fallo está en la capa de comunicación/debug/IDE.

Si además el monitor de Windows muestra una desconexión/reconexión, priorizar:

1. cable USB;
2. puerto/hub USB;
3. administración de energía de Windows;
4. firmware OpenMV/USB debug;
5. hardware USB de la placa.

Si el monitor no muestra ninguna desconexión pero el IDE deja de actualizar el framebuffer, la sospecha sube hacia OpenMV IDE/debug framebuffer.

## Archivos enormes

No usar sólo el tamaño del MJPEG para concluir que algo está corrupto. Primero mirar la telemetría:

- duración real;
- frames realmente guardados;
- FPS efectivo;
- tiempo medio de escritura.

Un archivo de varios GB puede ser simplemente una grabación que continuó durante horas mientras el usuario creyó que el IDE estaba colgado.
