# ============================================================
# 11_console_heartbeat.py
#
# OBJETIVO:
# Probar SOLO la salida de consola/debug durante varios minutos.
#
# NO usa sensor.
# NO usa microSD.
# NO crea archivos.
#
# Si la consola deja de mostrar mensajes pero el script sigue
# ejecutándose, el problema está en la capa de comunicación/IDE.
# ============================================================

import time

DURACION_MINUTOS = 20
INTERVALO_MS = 1000

print("\n========================================")
print(" TEST DE CONSOLA / DEBUG")
print("========================================\n")
print("Debe aparecer un heartbeat por segundo.")
print("Duracion:", DURACION_MINUTOS, "min")
print("")

start = time.ticks_ms()
counter = 0
max_ms = DURACION_MINUTOS * 60 * 1000

while time.ticks_diff(time.ticks_ms(), start) < max_ms:
    counter += 1
    elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
    print("HEARTBEAT %d | t=%.1f s" % (counter, elapsed))
    time.sleep_ms(INTERVALO_MS)

print("\nRESULTADO: HEARTBEAT COMPLETADO")
print("Mensajes enviados:", counter)
