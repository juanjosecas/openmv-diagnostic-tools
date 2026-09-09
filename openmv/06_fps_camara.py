# ============================================================
# 06_fps_camara.py
#
# OBJETIVO:
# Medir rendimiento del sensor durante 60 s SIN escribir video.
# ============================================================

import sensor
import time

DURACION_SEGUNDOS = 60
REPORT_EVERY_FRAMES = 100

print("\n========================================")
print(" DIAGNOSTICO OPENMV - FPS")
print("========================================\n")

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

inicio = time.ticks_ms()
frames = 0

while time.ticks_diff(time.ticks_ms(), inicio) < DURACION_SEGUNDOS * 1000:
    try:
        sensor.snapshot()
        frames += 1
    except Exception as e:
        print("ERROR capturando frame:")
        print(e)
        raise

    if frames % REPORT_EVERY_FRAMES == 0:
        transcurrido = time.ticks_diff(time.ticks_ms(), inicio) / 1000
        fps = frames / transcurrido if transcurrido > 0 else 0
        print("Tiempo: %.1f s | Frames: %d | FPS promedio: %.2f" % (transcurrido, frames, fps))

tiempo_total = time.ticks_diff(time.ticks_ms(), inicio) / 1000
fps_final = frames / tiempo_total if tiempo_total > 0 else 0

print("\nFrames totales:", frames)
print("FPS promedio: %.2f" % fps_final)
print("\n========================================")
print(" RESULTADO: TEST COMPLETADO")
print("========================================")
