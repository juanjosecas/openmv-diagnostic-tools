# ============================================================
# 05_sd_escritura.py
#
# OBJETIVO:
# Probar escritura sostenida en almacenamiento SIN usar cámara.
#
# Crea un archivo temporal de ~5 MB y luego lo elimina.
# ============================================================

import os
import time
import gc

ARCHIVO = "test_escritura.bin"
TAMANO_BLOQUE = 1024
NUMERO_BLOQUES = 5000

print("\n========================================")
print(" DIAGNOSTICO OPENMV - ESCRITURA SD")
print("========================================\n")

bloque = bytearray(TAMANO_BLOQUE)
for i in range(TAMANO_BLOQUE):
    bloque[i] = i % 256

mb = NUMERO_BLOQUES * TAMANO_BLOQUE / 1024 / 1024
print("Archivo temporal :", ARCHIVO)
print("Tamaño aproximado: %.2f MB" % mb)
print("")

inicio = time.ticks_ms()

try:
    with open(ARCHIVO, "wb") as f:
        for i in range(NUMERO_BLOQUES):
            f.write(bloque)
            if (i + 1) % 500 == 0:
                print("Bloques escritos:", i + 1)
except Exception as e:
    print("\nERROR DURANTE ESCRITURA:")
    print(e)
    raise

fin = time.ticks_ms()
tiempo_s = time.ticks_diff(fin, inicio) / 1000
velocidad = mb / tiempo_s if tiempo_s > 0 else 0

print("\nTiempo: %.2f s" % tiempo_s)
print("Velocidad aproximada: %.2f MB/s" % velocidad)

try:
    os.remove(ARCHIVO)
    print("Archivo temporal eliminado correctamente.")
except Exception as e:
    print("WARNING: no se pudo eliminar el archivo temporal:")
    print(e)

gc.collect()

print("\n========================================")
print(" RESULTADO: ESCRITURA COMPLETADA")
print("========================================")
