# ============================================================
# 04_sd_info.py
#
# OBJETIVO:
# Revisar filesystem y espacio disponible.
#
# NO escribe archivos grandes.
# ============================================================

import os

print("\n========================================")
print(" DIAGNOSTICO OPENMV - MICROSD / FS")
print("========================================\n")

print("[1] Archivos visibles en /:")
try:
    for archivo in os.listdir("/"):
        print(" -", archivo)
except Exception as e:
    print("ERROR ejecutando os.listdir('/'):", e)

print("\n[2] Espacio del filesystem /:")
try:
    info = os.statvfs("/")
    block_size = info[0]
    total_blocks = info[2]
    free_blocks = info[3]

    total_bytes = block_size * total_blocks
    free_bytes = block_size * free_blocks
    used_bytes = total_bytes - free_bytes

    total_mb = total_bytes / (1024 * 1024)
    free_mb = free_bytes / (1024 * 1024)
    used_mb = used_bytes / (1024 * 1024)

    print("Capacidad total : %.2f MB" % total_mb)
    print("Espacio usado   : %.2f MB" % used_mb)
    print("Espacio libre   : %.2f MB" % free_mb)

    if total_mb > 0:
        libre_pct = free_mb * 100 / total_mb
        print("Espacio libre   : %.1f %%" % libre_pct)
        if libre_pct < 10:
            print("WARNING: queda menos del 10 % del almacenamiento libre.")

except Exception as e:
    print("ERROR leyendo el filesystem:")
    print(e)

print("\nIMPORTANTE: verificar que '/' corresponda al almacenamiento")
print("donde realmente se escribe el MJPEG en este modelo/firmware.")
print("\n========================================")
print(" FIN DEL TEST")
print("========================================")
