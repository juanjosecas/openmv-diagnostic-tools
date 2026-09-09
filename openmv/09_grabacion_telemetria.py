# ============================================================
# 09_grabacion_telemetria.py
#
# OBJETIVO:
# Grabar MJPEG y, en paralelo, guardar telemetría en CSV para
# reconstruir qué ocurrió incluso si OpenMV IDE deja de responder.
#
# SALIDAS:
#   diagnostico_video.mjpeg
#   diagnostico_telemetria.csv
#
# El CSV se actualiza cada pocos segundos y registra:
# tiempo, frames, FPS, tiempos de captura/escritura, heap y
# espacio libre.
# ============================================================

import sensor
import mjpeg
import time
import gc
import os

VIDEO_FILE = "diagnostico_video.mjpeg"
LOG_FILE = "diagnostico_telemetria.csv"

FPS_OBJETIVO = 15
DURACION_MINUTOS = 30
REPORTE_CADA_SEGUNDOS = 10
MIN_FREE_SPACE_MB = 100


def free_mb():
    try:
        fs = os.statvfs("/")
        return fs[0] * fs[3] / (1024 * 1024)
    except Exception:
        return -1


def heap_free():
    try:
        gc.collect()
        return gc.mem_free()
    except Exception:
        return -1


def safe_flush(f):
    try:
        f.flush()
    except Exception:
        pass


def close_mjpeg(m):
    try:
        m.close()
    except TypeError:
        m.close(FPS_OBJETIVO)


print("\n========================================")
print(" OPENMV - GRABACION CON TELEMETRIA")
print("========================================\n")

if FPS_OBJETIVO <= 0:
    raise ValueError("FPS_OBJETIVO debe ser > 0")

espacio_inicial = free_mb()
print("Espacio libre inicial: %.2f MB" % espacio_inicial)

if espacio_inicial >= 0 and espacio_inicial < MIN_FREE_SPACE_MB:
    raise RuntimeError("Espacio libre insuficiente")

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

print("Sensor listo")
print("Video:", VIDEO_FILE)
print("Telemetria:", LOG_FILE)

m = mjpeg.Mjpeg(VIDEO_FILE)
log = open(LOG_FILE, "w")

log.write("time_s,frames,fps,capture_ms_avg,write_ms_avg,write_ms_max,heap_free,free_mb,status\n")
safe_flush(log)

start = time.ticks_ms()
last_report_ms = start
intervalo_ms = 1000 // FPS_OBJETIVO
max_duration_ms = DURACION_MINUTOS * 60 * 1000

frames = 0
capture_total = 0
write_total = 0
write_max = 0
status = "RUNNING"
error_text = ""

try:
    while time.ticks_diff(time.ticks_ms(), start) <= max_duration_ms:
        frame_start = time.ticks_ms()

        t0 = time.ticks_ms()
        try:
            img = sensor.snapshot()
        except Exception as e:
            status = "CAPTURE_ERROR"
            error_text = str(e)
            break
        t1 = time.ticks_ms()

        try:
            m.add_frame(img)
        except Exception as e:
            status = "WRITE_ERROR"
            error_text = str(e)
            break
        t2 = time.ticks_ms()

        capture_ms = time.ticks_diff(t1, t0)
        write_ms = time.ticks_diff(t2, t1)

        frames += 1
        capture_total += capture_ms
        write_total += write_ms
        if write_ms > write_max:
            write_max = write_ms

        cycle_ms = time.ticks_diff(time.ticks_ms(), frame_start)
        if cycle_ms < intervalo_ms:
            time.sleep_ms(intervalo_ms - cycle_ms)

        now = time.ticks_ms()
        if time.ticks_diff(now, last_report_ms) >= REPORTE_CADA_SEGUNDOS * 1000:
            last_report_ms = now
            elapsed_s = time.ticks_diff(now, start) / 1000
            fps = frames / elapsed_s if elapsed_s > 0 else 0
            capture_avg = capture_total / frames if frames > 0 else 0
            write_avg = write_total / frames if frames > 0 else 0
            heap = heap_free()
            space = free_mb()

            line = "%.1f,%d,%.2f,%.2f,%.2f,%d,%d,%.2f,%s\n" % (
                elapsed_s,
                frames,
                fps,
                capture_avg,
                write_avg,
                write_max,
                heap,
                space,
                status,
            )

            log.write(line)
            safe_flush(log)

            print("t=%.1fs | frames=%d | fps=%.2f | cap=%.2f ms | write=%.2f ms | free=%.2f MB" % (
                elapsed_s, frames, fps, capture_avg, write_avg, space
            ))

            if space >= 0 and space < MIN_FREE_SPACE_MB:
                status = "LOW_SPACE"
                error_text = "Espacio libre por debajo del margen de seguridad"
                break

except Exception as e:
    status = "UNEXPECTED_ERROR"
    error_text = str(e)

finally:
    elapsed_s = time.ticks_diff(time.ticks_ms(), start) / 1000
    fps = frames / elapsed_s if elapsed_s > 0 else 0
    capture_avg = capture_total / frames if frames > 0 else 0
    write_avg = write_total / frames if frames > 0 else 0

    try:
        close_mjpeg(m)
    except Exception as e:
        if status == "RUNNING":
            status = "CLOSE_ERROR"
            error_text = str(e)

    if status == "RUNNING":
        status = "COMPLETED"

    try:
        log.write("%.1f,%d,%.2f,%.2f,%.2f,%d,%d,%.2f,%s\n" % (
            elapsed_s,
            frames,
            fps,
            capture_avg,
            write_avg,
            write_max,
            heap_free(),
            free_mb(),
            status,
        ))
        if error_text:
            log.write("# ERROR,%s\n" % error_text.replace("\n", " "))
        safe_flush(log)
        log.close()
    except Exception:
        pass

print("\nRESULTADO:", status)
if error_text:
    print("Detalle:", error_text)
print("Frames:", frames)
print("Tiempo: %.2f s" % elapsed_s)
print("FPS promedio: %.2f" % fps)
print("Telemetria guardada en:", LOG_FILE)
