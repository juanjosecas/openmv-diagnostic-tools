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

No usar expresiones vagas como «se cuelga». Registrar qué ocurre realmente:

- el IDE deja de responder;
- Windows pierde el dispositivo USB;
- cambia/desaparece el puerto COM;
- la cámara se reinicia;
- el script imprime una excepción;
- el archivo MJPEG deja de crecer;
- el archivo queda corrupto o incompleto.

## Secuencia

### 1. Runtime y firmware

Ejecutar `openmv/01_versiones.py`.

Guardar toda la salida. Si faltan módulos básicos (`sensor`, `mjpeg`, `pyb`, `machine`), no seguir con las pruebas de grabación hasta aclarar firmware/API.

### 2. Sensor sin almacenamiento

Ejecutar `openmv/02_sensor_camara.py`.

Si falla aquí, la SD no es la causa primaria porque todavía no se está grabando ningún archivo.

### 3. Memoria

Ejecutar `openmv/03_memoria.py`.

La cifra reportada corresponde al heap de MicroPython y no a toda la memoria física de la placa. Se usa para comparar ejecuciones y detectar degradación o falta de heap.

### 4. Filesystem y espacio libre

Ejecutar `openmv/04_sd_info.py`.

Registrar capacidad, espacio usado y libre. Verificar además que el filesystem mostrado sea el esperado para la microSD.

### 5. Escritura sin cámara

Ejecutar `openmv/05_sd_escritura.py`.

Esta prueba crea un archivo temporal, escribe datos de forma sostenida y luego lo elimina.

Si `02_sensor_camara.py` pasa y `05_sd_escritura.py` falla, la sospecha principal pasa a almacenamiento/filesystem.

### 6. Rendimiento del sensor

Ejecutar `openmv/06_fps_camara.py`.

Registrar FPS promedio. Esta es la referencia de rendimiento sin escritura.

### 7. Grabación MJPEG instrumentada

Ejecutar `openmv/07_grabacion_mjpeg.py`.

Comparar:

- FPS promedio;
- tiempo promedio de captura;
- tiempo promedio de escritura;
- máximos de escritura si aparecen.

Si la captura se mantiene estable pero la escritura aumenta mucho, el cuello de botella está en almacenamiento.

### 8. Estabilidad prolongada

Ejecutar `openmv/08_estabilidad.py` durante varios minutos.

Si las pruebas cortas pasan pero esta falla, considerar alimentación, temperatura, firmware, memoria o hardware intermitente.

### 9. Diagnóstico de Windows

Ejecutar una vez con cámara desconectada, una con cámara funcionando y otra después del fallo:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\09_diagnostico_windows_openmv.ps1 *> diagnostico.txt
```

Comparar USB, COM, drivers y eventos Kernel-PnP.

### 10. Monitor USB durante el experimento

Ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\10_monitor_usb_openmv.ps1
```

Dejarlo abierto mientras se reproduce el fallo. El script registra cambios de dispositivos USB/COM con timestamp.

## Pruebas A/B útiles

Cambiar una sola variable por vez:

1. mismo equipo + otro cable USB;
2. mismo equipo + otro puerto USB;
3. mismo equipo + otra microSD;
4. misma cámara + otra PC;
5. mismo hardware + IDE cerrado durante grabación;
6. mismo hardware + IDE conectado durante grabación.

## Evidencia mínima a conservar

Para cada fallo guardar:

- script utilizado;
- parámetros;
- salida completa de consola;
- minuto/segundo aproximado del fallo;
- tamaño final del archivo MJPEG;
- si el archivo puede reproducirse;
- log de Windows si se sospecha desconexión USB.

No actualizar firmware, reinstalar drivers ni reformatear la SD antes de guardar esta evidencia, porque elimina información diagnóstica.