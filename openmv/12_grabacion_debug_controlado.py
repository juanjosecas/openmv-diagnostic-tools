# ============================================================
# 12_grabacion_debug_controlado.py
#
# OBJETIVO:
# Grabación MJPEG con control explícito de debug y telemetría.
# Diseñado para reproducir el caso:
#   - el IDE deja de reportar
#   - la cámara sigue grabando
#
# SALIDAS:
#   debug_video.mjpeg
#   debug_eventos.log
#
# CARACTERISTICAS:
# - logs persistentes con flush
# - heartbeat por consola poco frecuente
# - sync periódico del MJPEG si la API lo soporta
# - tamaño y cantidad de frames del MJPEG si la API lo soporta
# - opción de desactivar framebuffer en firmware que todavía
#   expone omv.disable_fb() (p.ej. 4.7.x)
# ============================================================

import sys
import sensor
import mjpeg
import time
import gc
import os

VIDEO_FILE = "debug_video.mjpeg"
LOG_FILE = "debug_eventos.log"

FPS_OBJETIVO = 15
DURACION_MINUTOS = 30
LOG_CADA_SEGUNDOS = 5
PRINT_CADA_SEGUNDOS = 30
SYNC_CADA_SEGUNDOS = 30
MIN_FREE_SPACE_MB = 100

# Para el caso actual con firmware 4.7.0 conviene probar primero
# False y luego True como ensayo A/B.
DISABLE_IDE_FRAMEBUFFER = False


def free_mb():
    try:
        fs = os.statvfs("/")
        return fs[0] * fs[3] / (1024 * 1024)
    except Exception:
        return -1


def heap_free():
    try:
        return gc.mem_free()
    except Exception:
        return -1


def safe_flush(f):
    try:
        f.flush()
    except Exception:
        pass
    try:
        if hasattr(os, "sync"):
            os.sync()
    except Exception:
        pass


def safe_mjpeg_sync(m):
    try:
        if hasattr(m, "sync"):
            m.sync()
            return True
    except Exception:
        return False
    return False


def mjpeg_count(m, fallback):
    try:
        if hasattr(m, "count"):
            return m.count()
    except Exception:
        pass
    return fallback


def mjpeg_size(m):
    try:
        if hasattr(m, "size"):
            return m.size()
    except Exception:
        pass
    return -1


def log_event(f, start_ms, level, message):
    elapsed = time.ticks_diff(time.ticks_ms(), start_ms) / 1000
    line = "%.3f | %s | %s\n" % (elapsed, level, message)
    f.write(line)
    safe_flush(f)


def close_mjpeg(m):
    try:
        m.close()
    except TypeError:
        # Compatibilidad con variantes antiguas del ejemplo/API.
        m.close(FPS_OBJETIVO)


print("\n==================================================")
print(" OPENMV - GRABACION CON DEBUG CONTROLADO")
print("==================================================\n")
print("Runtime:", sys.version)

# ------------------------------------------------------------
# Información OpenMV y control opcional del framebuffer
# ------------------------------------------------------------
fb_changed = False
fb_previous = None
try:
    import omv
    try:
        print("OpenMV firmware:", omv.version_string())
    except Exception:
        pass
    try:
        print("Board:", omv.board_type())
    except Exception:
        pass

    if DISABLE_IDE_FRAMEBUFFER:
        if hasattr(omv, "disable_fb"):
            try:
                fb_previous = omv.disable_fb()
            except Exception:
                fb_previous = None
            omv.disable_fb(True)
            fb_changed = True
            print("Framebuffer IDE desactivado desde la cámara.")
        else:
            print("WARNING: este firmware no expone omv.disable_fb().")
except Exception as e:
    print("WARNING: modulo omv no disponible:", e)

# ------------------------------------------------------------
# Prechecks
# ------------------------------------------------------------
if FPS_OBJETIVO <= 0:
    raise ValueError("FPS_OBJETIVO debe ser > 0")
if DURACION_MINUTOS <= 0:
    raise ValueError("DURACION_MINUTOS debe ser > 0")

space0 = free_mb()
print("Espacio libre inicial: %.2f MB" % space0)
if space0 >= 0 and space0 < MIN_FREE_SPACE_MB:
    raise RuntimeError("Espacio libre insuficiente")

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

m = None
log = None
start = time.ticks_ms()
status = "INIT"
error_text = ""

frames = 0
capture_total = 0
write_total = 0
capture_max = 0
write_max = 0

try:
    log = open(LOG_FILE, "w")
    log.write("# OpenMV diagnostic event log\n")
    safe_flush(log)
    log_event(log, start, "INFO", "START")
    log_event(log, start, "INFO", "fps_target=%d duration_min=%d fb_disabled=%s" % (
        FPS_OBJETIVO, DURACION_MINUTOS, DISABLE_IDE_FRAMEBUFFER
    ))

    m = mjpeg.Mjpeg(VIDEO_FILE)
    log_event(log, start, "INFO", "MJPEG_CREATED")

    status = "RUNNING"
    interval_ms = 1000 // FPS_OBJETIVO
    max_ms = DURACION_MINUTOS * 60 * 1000
    last_log = start
    last_print = start
    last_sync = start

    while time.ticks_diff(time.ticks_ms(), start) < max_ms:
        cycle_start = time.ticks_ms()

        t0 = time.ticks_ms()
        try:
            img = sensor.snapshot()
        except Exception as e:
            status = "CAPTURE_ERROR"
            error_text = str(e)
            log_event(log, start, "ERROR", "CAPTURE_ERROR: " + error_text)
            break
        t1 = time.ticks_ms()

        try:
            m.add_frame(img)
        except Exception as e:
            status = "WRITE_ERROR"
            error_text = str(e)
            log_event(log, start, "ERROR", "WRITE_ERROR: " + error_text)
            break
        t2 = time.ticks_ms()

        cap_ms = time.ticks_diff(t1, t0)
        write_ms = time.ticks_diff(t2, t1)
        frames += 1
        capture_total += cap_ms
        write_total += write_ms
        if cap_ms > capture_max:
            capture_max = cap_ms
        if write_ms > write_max:
            write_max = write_ms

        cycle_ms = time.ticks_diff(time.ticks_ms(), cycle_start)
        if cycle_ms < interval_ms:
            time.sleep_ms(interval_ms - cycle_ms)

        now = time.ticks_ms()

        if time.ticks_diff(now, last_log) >= LOG_CADA_SEGUNDOS * 1000:
            last_log = now
            elapsed = time.ticks_diff(now, start) / 1000
            fps = frames / elapsed if elapsed > 0 else 0
            msg = (
                "HEARTBEAT frames=%d mcount=%d fps=%.2f cap_avg=%.2f cap_max=%d "
                "write_avg=%.2f write_max=%d msize=%d heap=%d free_mb=%.2f"
                % (
                    frames,
                    mjpeg_count(m, frames),
                    fps,
                    capture_total / frames,
                    capture_max,
                    write_total / frames,
                    write_max,
                    mjpeg_size(m),
                    heap_free(),
                    free_mb(),
                )
            )
            log_event(log, start, "INFO", msg)

            if free_mb() >= 0 and free_mb() < MIN_FREE_SPACE_MB:
                status = "LOW_SPACE"
                error_text = "Espacio libre por debajo del margen"
                log_event(log, start, "ERROR", error_text)
                break

        if time.ticks_diff(now, last_sync) >= SYNC_CADA_SEGUNDOS * 1000:
            last_sync = now
            synced = safe_mjpeg_sync(m)
            log_event(log, start, "INFO", "MJPEG_SYNC supported=%s" % synced)

        if time.ticks_diff(now, last_print) >= PRINT_CADA_SEGUNDOS * 1000:
            last_print = now
            elapsed = time.ticks_diff(now, start) / 1000
            print("ALIVE t=%.0fs frames=%d fps=%.2f msize=%d" % (
                elapsed,
                frames,
                frames / elapsed if elapsed > 0 else 0,
                mjpeg_size(m),
            ))

    if status == "RUNNING":
        status = "COMPLETED"

except Exception as e:
    status = "UNEXPECTED_ERROR"
    error_text = str(e)
    if log is not None:
        try:
            log_event(log, start, "ERROR", "UNEXPECTED_ERROR: " + error_text)
        except Exception:
            pass

finally:
    if m is not None:
        try:
            safe_mjpeg_sync(m)
            close_mjpeg(m)
            if log is not None:
                log_event(log, start, "INFO", "MJPEG_CLOSED")
        except Exception as e:
            if status == "COMPLETED":
                status = "CLOSE_ERROR"
                error_text = str(e)
            if log is not None:
                try:
                    log_event(log, start, "ERROR", "CLOSE_ERROR: " + str(e))
                except Exception:
                    pass

    if log is not None:
        try:
            log_event(log, start, "FINAL", "status=%s frames=%d error=%s" % (
                status, frames, error_text.replace("\n", " ")
            ))
            log.close()
        except Exception:
            pass

    if fb_changed:
        try:
            if fb_previous is False:
                omv.disable_fb(False)
        except Exception:
            pass

    gc.collect()

elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
print("\nRESULTADO:", status)
print("Tiempo: %.2f s" % elapsed)
print("Frames:", frames)
print("FPS promedio: %.2f" % (frames / elapsed if elapsed > 0 else 0))
print("Log persistente:", LOG_FILE)
print("Video:", VIDEO_FILE)
if error_text:
    print("Detalle:", error_text)
