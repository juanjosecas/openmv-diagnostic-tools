# ============================================================
# 03_memoria.py
#
# OBJETIVO:
# Revisar memoria del heap de MicroPython.
#
# NO usa cámara.
# NO escribe en la microSD.
# ============================================================

import gc

print("\n========================================")
print(" DIAGNOSTICO OPENMV - MEMORIA")
print("========================================\n")

gc.collect()

try:
    libre = gc.mem_free()
    usada = gc.mem_alloc()
    total = libre + usada

    print("Memoria total aproximada :", total, "bytes")
    print("Memoria usada            :", usada, "bytes")
    print("Memoria libre            :", libre, "bytes")

    if total > 0:
        print("Memoria libre            : %.1f %%" % (libre * 100 / total))

except Exception as e:
    print("ERROR obteniendo informacion de memoria:")
    print(e)

print("\nNOTA: esto corresponde al heap de MicroPython,")
print("no a toda la RAM fisica de la placa.")
print("\n========================================")
print(" FIN DEL TEST")
print("========================================")
