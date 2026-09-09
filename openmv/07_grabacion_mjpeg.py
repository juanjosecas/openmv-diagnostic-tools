# ============================================================
# 07_grabacion_mjpeg.py
#
# OBJETIVO:
# Probar grabación MJPEG midiendo por separado captura y escritura.
# ============================================================

import sensor
import mjpeg
import time
import gc

ARCHIVO = "diagnostico.mjpeg"
FPS_OBJETIVO = 15
DURACION_SEGUNDOS = 60
REPORT_EVERY_FRAMES = 100

print("\n========================================")
print(" DIAGNOSTICO OPENMV - MJPEG")
print("========================================\n")

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

print("Creando archivo:", ARCHIVO)
m = mjpeg.Mjpeg(ARCHIVO)

inicio = time.ticks_ms()
frames = 0
captura_total_ms = 0
escritura_total_ms = 0
max_escritura_ms = 0
intervalo_ms = 1000 // FPS_OBJETIVO

try:
    while time.ticks_diff(time.ticks_ms(), inicio) < DURACION_SEGUNDOS * 1000:
        ciclo_inicio = time.ticks_ms()

        t0 = time.ticks_ms()
        img = sensor.snapshot()
        t1 = time.ticks_ms()

        m.add_frame(img)
        t2 = time.ticks_ms()

        captura_ms = time.ticks_diff(t1, t0)
        escritura_ms = time.ticks_diff(t2, t1)
        captura_total_ms += captura_ms
        escritura_total_ms += escritura_ms
        if escritura_ms > max_escritura_ms:
            max_escritura_ms = escritura_ms
        frames += 1

        ciclo_ms = time.ticks_diff(time.ticks_ms(), ciclo_inicio)
        if ciclo_ms < intervalo_ms:
            time.sleep_ms(intervalo_ms - ciclo_ms)

        if frames % REPORT_EVERY_FRAMES == 0:
            transcurrido = time.ticks_diff(time.ticks_ms(), inicio) / 1000
            fps_real = frames / transcurrido if transcurrido > 0 else 0
            print("")
            print("Frames:", frames)
            print("FPS promedio: %.2f" % fps_real)
            print("Captura media: %.2f ms" % (captura_total_ms / frames))
            print("Escritura media: %.2f ms" % (escritura_total_ms / frames))
            print("Peor escritura: %d ms" % max_escritura_ms)

except Exception as e:
    print("\nERROR DURANTE LA GRABACION:")
    print(e)
    raise

finally:
    print("\nCerrando archivo...")
    try:
        m.close()
    except TypeError:
        m.close(FPS_OBJETIVO)
    gc.collect()

print("\n========================================")
print(" GRABACION TERMINADA")
print("========================================")
