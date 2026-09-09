# ============================================================
# 08_estabilidad.py
#
# OBJETIVO:
# Mantener el sensor trabajando durante varios minutos para
# detectar fallas intermitentes SIN escribir video.
# ============================================================

import sensor
import time
import gc

DURACION_MINUTOS = 10
REPORTE_CADA_SEGUNDOS = 30

print("\n========================================")
print(" DIAGNOSTICO OPENMV - ESTABILIDAD")
print("========================================\n")

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

inicio = time.ticks_ms()
frames = 0
ultimo_reporte = 0

while time.ticks_diff(time.ticks_ms(), inicio) < DURACION_MINUTOS * 60 * 1000:
    try:
        sensor.snapshot()
        frames += 1
    except Exception as e:
        print("\nERROR EN FRAME:", frames + 1)
        print(e)
        raise

    transcurrido_s = time.ticks_diff(time.ticks_ms(), inicio) / 1000

    if transcurrido_s - ultimo_reporte >= REPORTE_CADA_SEGUNDOS:
        ultimo_reporte = transcurrido_s
        fps = frames / transcurrido_s if transcurrido_s > 0 else 0
        gc.collect()

        print("\nTiempo: %d s" % int(transcurrido_s))
        print("Frames:", frames)
        print("FPS promedio: %.2f" % fps)

        try:
            print("Heap libre:", gc.mem_free(), "bytes")
        except Exception:
            pass

print("\n========================================")
print(" TEST DE ESTABILIDAD COMPLETADO")
print("========================================")
