# ============================================================
# grabacion_robusta.py
#
# VERSION DIAGNOSTICA DEL GRABADOR MJPEG ORIGINAL
#
# OBJETIVO:
# Grabar video MJPEG y reportar de forma clara posibles fallas
# de sensor, almacenamiento, rendimiento y memoria.
# ============================================================

import sys
import sensor
import time
import mjpeg
import pyb
import gc
import os

RED_LED_PIN = 1
BLUE_LED_PIN = 3

filename = "_ESTEBAN"
DESIRED_FPS = 15
DURATION_MINUTES = 1
RESOLUCION = sensor.QVGA
PIXFORMAT = sensor.GRAYSCALE
MIN_FREE_SPACE_MB = 100
REPORT_EVERY_FRAMES = 128
SLOW_WRITE_WARNING_MS = 100


def separator():
    print("\n--------------------------------------------------\n")


def mostrar_memoria():
    try:
        gc.collect()
        print("Memoria libre:", gc.mem_free(), "bytes")
    except Exception:
        pass


def espacio_libre_mb():
    try:
        fs = os.statvfs("/")
        block_size = fs[0]
        free_blocks = fs[3]
        return block_size * free_blocks / (1024 * 1024)
    except Exception as e:
        print("WARNING: no se pudo determinar espacio libre.")
        print("Detalle:", e)
        return None


def cerrar_mjpeg(m):
    if m is None:
        return

    print("Cerrando archivo MJPEG...")
    try:
        m.close()
        print("Archivo cerrado correctamente.")
    except TypeError:
        try:
            m.close(DESIRED_FPS)
            print("Archivo cerrado correctamente usando FPS.")
        except Exception as e:
            print("ERROR cerrando archivo MJPEG:", e)
    except Exception as e:
        print("ERROR cerrando archivo MJPEG:", e)


print("\n==================================================")
print(" OPENMV - GRABADOR MJPEG ROBUSTO")
print("==================================================\n")

try:
    print("Runtime:", sys.version)
    print("Plataforma:", sys.platform)
except Exception:
    pass

mostrar_memoria()
separator()

print("Validando configuracion...")
if DESIRED_FPS <= 0:
    print("ERROR: DESIRED_FPS debe ser mayor que cero.")
    sys.exit()
if DURATION_MINUTES <= 0:
    print("ERROR: DURATION_MINUTES debe ser mayor que cero.")
    sys.exit()

DURATION_SECONDS = DURATION_MINUTES * 60
DURATION_MILLISECONDS = DURATION_SECONDS * 1000
TIME_BETWEEN_FRAMES = 1000 // DESIRED_FPS
EXPECTED_FRAMES = DESIRED_FPS * DURATION_SECONDS

print("Archivo:", filename + ".mjpeg")
print("FPS objetivo:", DESIRED_FPS)
print("Duracion:", DURATION_MINUTES, "min")
print("Frames teoricos:", EXPECTED_FRAMES)

separator()
print("Revisando almacenamiento...")
free_space_mb = espacio_libre_mb()
if free_space_mb is not None:
    print("Espacio libre: %.2f MB" % free_space_mb)
    if free_space_mb < MIN_FREE_SPACE_MB:
        print("ERROR: queda muy poco espacio libre.")
        sys.exit()
else:
    print("WARNING: se continuara sin conocer el espacio libre.")

separator()
print("Inicializando camara...")
try:
    sensor.reset()
    sensor.set_pixformat(PIXFORMAT)
    sensor.set_framesize(RESOLUCION)
    sensor.skip_frames(time=2000)
    print("Sensor inicializado correctamente.")
except Exception as e:
    print("ERROR INICIALIZANDO LA CAMARA")
    print("Detalle:", e)
    pyb.LED(RED_LED_PIN).on()
    sys.exit()

print("\nRealizando captura de prueba...")
try:
    frame_dummy = sensor.snapshot()
    print("Captura de prueba correcta.")
except Exception as e:
    print("ERROR CAPTURANDO IMAGEN DE PRUEBA")
    print("Detalle:", e)
    pyb.LED(RED_LED_PIN).on()
    sys.exit()

print("\nEstimando tamaño del video...")
try:
    buffer = frame_dummy.compress()
    frame_size_bytes = len(buffer)
    estimated_mb = EXPECTED_FRAMES * frame_size_bytes / (1024 * 1024)
    print("Tamaño JPEG del frame de prueba:", frame_size_bytes, "bytes")
    print("Tamaño aproximado del video: %.2f MB" % estimated_mb)

    if free_space_mb is not None:
        if estimated_mb + MIN_FREE_SPACE_MB > free_space_mb:
            print("ERROR: posiblemente no haya espacio suficiente.")
            print("Video estimado: %.2f MB" % estimated_mb)
            print("Espacio libre: %.2f MB" % free_space_mb)
            sys.exit()
except Exception as e:
    print("WARNING: no se pudo estimar tamaño del archivo.")
    print("Detalle:", e)

buffer = None
frame_dummy = None
gc.collect()
mostrar_memoria()

separator()
print("Creando archivo MJPEG...")
m = None
try:
    m = mjpeg.Mjpeg(filename + ".mjpeg")
    print("Archivo creado correctamente.")
except Exception as e:
    print("ERROR CREANDO EL ARCHIVO MJPEG")
    print("Detalle:", e)
    pyb.LED(RED_LED_PIN).on()
    sys.exit()

separator()
print("GRABANDO...")
pyb.LED(RED_LED_PIN).off()
pyb.LED(BLUE_LED_PIN).on()

saved_frames = 0
start_time = time.ticks_ms()
capture_time_total = 0
write_time_total = 0
max_write_time = 0
recording_error = None

try:
    while time.ticks_diff(time.ticks_ms(), start_time) <= DURATION_MILLISECONDS:
        frame_start = time.ticks_ms()

        capture_start = time.ticks_ms()
        try:
            frame = sensor.snapshot()
        except Exception as e:
            print("\nERROR CAPTURANDO FRAME")
            print("Frame:", saved_frames + 1)
            print("Detalle:", e)
            recording_error = e
            break
        capture_end = time.ticks_ms()
        capture_ms = time.ticks_diff(capture_end, capture_start)

        write_start = time.ticks_ms()
        try:
            m.add_frame(frame)
        except Exception as e:
            print("\nERROR ESCRIBIENDO FRAME")
            print("Frame:", saved_frames + 1)
            print("Detalle:", e)
            free_now = espacio_libre_mb()
            if free_now is not None:
                print("Espacio libre actual: %.2f MB" % free_now)
            recording_error = e
            break
        write_end = time.ticks_ms()
        write_ms = time.ticks_diff(write_end, write_start)

        saved_frames += 1
        capture_time_total += capture_ms
        write_time_total += write_ms
        if write_ms > max_write_time:
            max_write_time = write_ms

        if write_ms > SLOW_WRITE_WARNING_MS:
            print("WARNING: escritura lenta:", write_ms, "ms | frame:", saved_frames)

        cycle_time = time.ticks_diff(time.ticks_ms(), frame_start)
        if cycle_time < TIME_BETWEEN_FRAMES:
            time.sleep_ms(TIME_BETWEEN_FRAMES - cycle_time)

        if saved_frames % REPORT_EVERY_FRAMES == 0:
            elapsed_s = time.ticks_diff(time.ticks_ms(), start_time) / 1000
            avg_fps = saved_frames / elapsed_s if elapsed_s > 0 else 0

            print("\nTiempo: %02d:%02d" % (int(elapsed_s // 60), int(elapsed_s % 60)))
            print("Frames:", saved_frames)
            print("FPS promedio: %.2f" % avg_fps)
            print("Captura promedio: %.2f ms" % (capture_time_total / saved_frames))
            print("Escritura promedio: %.2f ms" % (write_time_total / saved_frames))
            print("Peor escritura:", max_write_time, "ms")
            mostrar_memoria()

            free_now = espacio_libre_mb()
            if free_now is not None:
                print("Espacio libre: %.2f MB" % free_now)
                if free_now < MIN_FREE_SPACE_MB:
                    print("ERROR: almacenamiento casi lleno.")
                    recording_error = "Espacio insuficiente"
                    break

        if saved_frames % 16 == 0:
            try:
                pyb.LED(BLUE_LED_PIN).toggle()
            except Exception:
                pass

except Exception as e:
    print("\nERROR GENERAL DURANTE LA GRABACION")
    print("Detalle:", e)
    recording_error = e

finally:
    separator()
    print("Finalizando grabacion...")
    cerrar_mjpeg(m)
    pyb.LED(BLUE_LED_PIN).off()
    gc.collect()

separator()
elapsed_s = time.ticks_diff(time.ticks_ms(), start_time) / 1000
print("RESULTADO FINAL")
print("Frames guardados:", saved_frames)
print("Tiempo grabado: %.2f segundos" % elapsed_s)

if elapsed_s > 0:
    print("FPS promedio final: %.2f" % (saved_frames / elapsed_s))
if saved_frames > 0:
    print("Captura promedio: %.2f ms" % (capture_time_total / saved_frames))
    print("Escritura promedio: %.2f ms" % (write_time_total / saved_frames))
    print("Mayor tiempo de escritura:", max_write_time, "ms")

mostrar_memoria()
free_final = espacio_libre_mb()
if free_final is not None:
    print("Espacio libre final: %.2f MB" % free_final)

if recording_error is None:
    print("\nRESULTADO: GRABACION COMPLETADA CORRECTAMENTE")
else:
    print("\nRESULTADO: LA GRABACION TERMINO CON ERROR")
    print("ERROR:", recording_error)

print("\n==================================================")
print(" FIN")
print("==================================================")

# Durante diagnóstico NO se reinicia automáticamente la placa.
# Para recuperar el comportamiento del script original:
# import machine
# time.sleep_ms(1000)
# machine.reset()
