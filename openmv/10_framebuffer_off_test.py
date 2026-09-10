# ============================================================
# 10_framebuffer_off_test.py
#
# OBJETIVO:
# Probar si la comunicación/preview del IDE está interfiriendo
# con la ejecución del script.
#
# IMPORTANTE:
# - En firmware 4.7.x puede existir omv.disable_fb().
# - Desde firmware 4.8.0 esa API fue eliminada.
# - Este script detecta la capacidad antes de usarla.
# ============================================================

import sensor
import time

DURACION_SEGUNDOS = 180
REPORT_EVERY_SECONDS = 10

print("\n========================================")
print(" TEST FRAMEBUFFER / DEBUG IDE")
print("========================================\n")

try:
    import omv
except Exception as e:
    print("ERROR: no se pudo importar omv:", e)
    raise

if not hasattr(omv, "disable_fb"):
    print("RESULTADO: este firmware no expone omv.disable_fb().")
    print("No se modifica el framebuffer.")
    print("En firmware >= 4.8.0 esta API fue eliminada.")
    raise SystemExit

try:
    estado_anterior = omv.disable_fb()
except Exception:
    estado_anterior = None

print("Estado previo disable_fb:", estado_anterior)

try:
    omv.disable_fb(True)
    print("Framebuffer hacia IDE desactivado desde la camara.")
except Exception as e:
    print("ERROR desactivando framebuffer:", e)
    raise

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

start = time.ticks_ms()
last_report = start
frames = 0

print("\nCapturando durante", DURACION_SEGUNDOS, "s.")
print("El IDE puede dejar de mostrar imagen: ESO ES ESPERADO en esta prueba.")

try:
    while time.ticks_diff(time.ticks_ms(), start) < DURACION_SEGUNDOS * 1000:
        sensor.snapshot()
        frames += 1

        now = time.ticks_ms()
        if time.ticks_diff(now, last_report) >= REPORT_EVERY_SECONDS * 1000:
            last_report = now
            elapsed = time.ticks_diff(now, start) / 1000
            fps = frames / elapsed if elapsed > 0 else 0
            print("heartbeat t=%.1f s | frames=%d | fps=%.2f" % (elapsed, frames, fps))

finally:
    try:
        if estado_anterior is False:
            omv.disable_fb(False)
            print("Framebuffer restaurado al estado previo.")
    except Exception as e:
        print("WARNING: no se pudo restaurar framebuffer:", e)

elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
print("\nRESULTADO: prueba completada")
print("Tiempo: %.2f s" % elapsed)
print("Frames:", frames)
print("FPS promedio: %.2f" % (frames / elapsed if elapsed > 0 else 0))
