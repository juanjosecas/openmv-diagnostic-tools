# ============================================================
# grabacion_robusta.py
#
# VERSION ROBUSTA DEL GRABADOR MJPEG ORIGINAL
#
# Objetivo: grabar normalmente, pero dejar suficiente evidencia
# para diagnosticar fallos aunque el IDE deje de reportar.
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

# ------------------------------------------------------------
# CONFIGURACION USUAL
# ------------------------------------------------------------
filename = "_ESTEBAN"
DESIRED_FPS = 15
DURATION_MINUTES = 10
RESOLUCION = sensor.QVGA
PIXFORMAT = sensor.GRAYSCALE

# ------------------------------------------------------------
# CONFIGURACION DIAGNOSTICA
# ------------------------------------------------------------
MIN_FREE_SPACE_MB = 100
LOG_FILE = filename + "_diagnostico.log"
LOG_EVERY_SECONDS = 10
PRINT_EVERY_SECONDS = 30
SYNC_EVERY_SECONDS = 30
SLOW_WRITE_WARNING_MS = 100

# Para firmware 4.7.x puede probarse True como ensayo A/B.
# Desde 4.8.0 omv.disable_fb() fue eliminado, por lo que se
# detecta la API antes de usarla.
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


def mjpeg_size(m):
    try:
        if hasattr(m, "size"):
            return m.size()
    except Exception:
        pass
    return -1


def mjpeg_count(m, fallback):
    try:
        if hasattr(m, "count"):
            return m.count()
    except Exception:
        pass
    return fallback


def log_event(log, start_ms, level, text):
    elapsed = time.ticks_diff(time.ticks_ms(), start_ms) / 1000
    log.write("%.3f | %s | %s\n" % (elapsed, level, text))
    safe_flush(log)


def close_mjpeg(m):
    if m is None:
        return
    try:
        m.close()
    except TypeError:
        # Compatibilidad con APIs/ejemplos antiguos.
        m.close(DESIRED_FPS)


print("\n==================================================")
print(" OPENMV - GRABADOR MJPEG ROBUSTO")
print("==================================================\n")
print("Runtime:", sys.version)

if DESIRED_FPS <= 0:
    raise ValueError("DESIRED_FPS debe ser > 0")
if DURATION_MINUTES <= 0:
    raise ValueError("DURATION_MINUTES debe ser > 0")

DURATION_MS = DURATION_MINUTES * 60 * 1000
FRAME_INTERVAL_MS = 1000 // DESIRED_FPS

# ------------------------------------------------------------
# Información de firmware y control opcional del framebuffer
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
            print("Framebuffer del IDE desactivado para esta prueba.")
        else:
            print("WARNING: este firmware no expone omv.disable_fb().")
except Exception as e:
    print("WARNING: no se pudo consultar modulo omv:", e)

# ------------------------------------------------------------
# Chequeos previos
# ------------------------------------------------------------
space0 = free_mb()
print("Espacio libre inicial: %.2f MB" % space0)
if space0 >= 0 and space0 < MIN_FREE_SPACE_MB:
    raise RuntimeError("Espacio libre insuficiente")

print("Inicializando sensor...")
sensor.reset()
sensor.set_pixformat(PIXFORMAT)
sensor.set_framesize(RESOLUCION)
sensor.skip_frames(time=2000)

# Captura de prueba antes de crear el archivo.
try:
    probe = sensor.snapshot()
    print("Captura de prueba: OK")
except Exception as e:
    pyb.LED(RED_LED_PIN).on()
    print("ERROR inicializando/capturando sensor:", e)
    raise

# Estimación orientativa, no se usa como sustituto del espacio real.
try:
    probe_jpeg = probe.compress()
    estimated_frame_bytes = len(probe_jpeg)
    expected_frames = DESIRED_FPS * DURATION_MINUTES * 60
    estimated_mb = expected_frames * estimated_frame_bytes / (1024 * 1024)
    print("Tamaño estimado orientativo: %.2f MB" % estimated_mb)
except Exception:
    estimated_mb = -1

probe = None
try:
    probe_jpeg = None
except Exception:
    pass
gc.collect()

# ------------------------------------------------------------
# Apertura de video y log persistente
# ------------------------------------------------------------
m = None
log = None
status = "INIT"
error_text = ""
start = time.ticks_ms()

frames = 0
capture_total = 0
write_total = 0
capture_max = 0
write_max = 0

try:
    log = open(LOG_FILE, "w")
    log.write("# OpenMV robust recorder diagnostic log\n")
    safe_flush(log)

    log_event(log, start, "INFO", "START")
    log_event(log, start, "INFO", "fps=%d duration_min=%d free_mb=%.2f fb_disabled=%s" % (
        DESIRED_FPS, DURATION_MINUTES, space0, DISABLE_IDE_FRAMEBUFFER
    ))

    m = mjpeg.Mjpeg(filename + ".mjpeg")
    log_event(log, start, "INFO", "MJPEG_CREATED")

    pyb.LED(RED_LED_PIN).off()
    pyb.LED(BLUE_LED_PIN).on()
    status = "RUNNING"

    last_log = start
    last_print = start
    last_sync = start

    while time.ticks_diff(time.ticks_ms(), start) < DURATION_MS:
        cycle_start = time.ticks_ms()

        # Captura y escritura se miden por separado.
        t0 = time.ticks_ms()
        try:
            frame = sensor.snapshot()
        except Exception as e:
            status = "CAPTURE_ERROR"
            error_text = str(e)
            log_event(log, start, "ERROR", "CAPTURE_ERROR: " + error_text)
            break
        t1 = time.ticks_ms()

        try:
            m.add_frame(frame)
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

        if write_ms > SLOW_WRITE_WARNING_MS and log is not None:
            log_event(log, start, "WARN", "SLOW_WRITE frame=%d write_ms=%d" % (frames, write_ms))

        cycle_ms = time.ticks_diff(time.ticks_ms(), cycle_start)
        if cycle_ms < FRAME_INTERVAL_MS:
            time.sleep_ms(FRAME_INTERVAL_MS - cycle_ms)

        now = time.ticks_ms()

        # Log frecuente en SD. No depende de que la consola/IDE funcione.
        if time.ticks_diff(now, last_log) >= LOG_EVERY_SECONDS * 1000:
            last_log = now
            elapsed = time.ticks_diff(now, start) / 1000
            fps = frames / elapsed if elapsed > 0 else 0
            log_event(log, start, "INFO", (
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
            ))

            space = free_mb()
            if space >= 0 and space < MIN_FREE_SPACE_MB:
                status = "LOW_SPACE"
                error_text = "Espacio libre por debajo del margen"
                log_event(log, start, "ERROR", error_text)
                break

        # La documentación reciente de OpenMV expone Mjpeg.sync().
        # Se usa sólo si la versión actual realmente lo implementa.
        if time.ticks_diff(now, last_sync) >= SYNC_EVERY_SECONDS * 1000:
            last_sync = now
            synced = safe_mjpeg_sync(m)
            log_event(log, start, "INFO", "MJPEG_SYNC supported=%s" % synced)

        # Consola poco verbosa: si esto desaparece pero el log sigue,
        # el script está vivo y el problema está más arriba en debug/IDE.
        if time.ticks_diff(now, last_print) >= PRINT_EVERY_SECONDS * 1000:
            last_print = now
            elapsed = time.ticks_diff(now, start) / 1000
            print("ALIVE t=%.0fs frames=%d fps=%.2f size=%d" % (
                elapsed,
                frames,
                frames / elapsed if elapsed > 0 else 0,
                mjpeg_size(m),
            ))

        if frames % 16 == 0:
            try:
                pyb.LED(BLUE_LED_PIN).toggle()
            except Exception:
                pass

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
            status = "CLOSE_ERROR"
            error_text = str(e)
            if log is not None:
                try:
                    log_event(log, start, "ERROR", "CLOSE_ERROR: " + error_text)
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

    pyb.LED(BLUE_LED_PIN).off()

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
print("Video:", filename + ".mjpeg")
print("Log:", LOG_FILE)
if error_text:
    print("Detalle:", error_text)

# NO reiniciar automáticamente durante diagnóstico.
