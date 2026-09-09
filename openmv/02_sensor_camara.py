# ============================================================
# 02_sensor_camara.py
#
# OBJETIVO:
# Comprobar el sensor SIN escribir en la microSD.
#
# Si falla aquí, la SD no es la causa primaria.
# ============================================================

import sensor
import time
import gc

NUMERO_DE_FOTOS = 100

print("\n========================================")
print(" DIAGNOSTICO OPENMV - SENSOR")
print("========================================\n")

print("[1] Inicializando sensor...")
try:
    sensor.reset()
    sensor.set_pixformat(sensor.GRAYSCALE)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)
    print("OK: sensor inicializado")
except Exception as e:
    print("ERROR inicializando sensor:", e)
    raise

print("\n[2] Capturando", NUMERO_DE_FOTOS, "imagenes...")
inicio = time.ticks_ms()

for i in range(NUMERO_DE_FOTOS):
    try:
        sensor.snapshot()
    except Exception as e:
        print("ERROR EN CAPTURA NUMERO:", i + 1)
        print(e)
        raise

    if (i + 1) % 10 == 0:
        print("Capturas correctas:", i + 1)

fin = time.ticks_ms()
tiempo_s = time.ticks_diff(fin, inicio) / 1000
fps = NUMERO_DE_FOTOS / tiempo_s if tiempo_s > 0 else 0

gc.collect()

print("\nTiempo total: %.2f s" % tiempo_s)
print("FPS aproximados: %.2f" % fps)
print("\n========================================")
print(" RESULTADO: SENSOR OK")
print("========================================")
