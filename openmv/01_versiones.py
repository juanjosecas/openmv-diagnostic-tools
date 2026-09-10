# ============================================================
# 01_versiones.py
#
# OBJETIVO:
# Mostrar información del firmware/runtime, modelo de placa y
# disponibilidad de APIs relevantes para diagnóstico.
# ============================================================

import sys
import os

print("\n========================================")
print(" DIAGNOSTICO OPENMV - VERSIONES")
print("========================================\n")

print("[1] VERSION / RUNTIME")
try:
    print("sys.version:")
    print(sys.version)
except Exception as e:
    print("ERROR leyendo sys.version:", e)

print("\n[2] IMPLEMENTACION")
try:
    print(sys.implementation)
except Exception as e:
    print("No disponible:", e)

print("\n[3] PLATAFORMA")
try:
    print("sys.platform:", sys.platform)
except Exception as e:
    print("No disponible:", e)

print("\n[4] INFORMACION DEL SISTEMA")
try:
    print(os.uname())
except Exception as e:
    print("os.uname() no disponible:", e)

print("\n[5] INFORMACION OPENMV")
try:
    import omv

    for nombre in ("version_string", "board_type", "board_id", "arch"):
        try:
            valor = getattr(omv, nombre)()
            print("%-16s: %s" % (nombre, valor))
        except Exception as e:
            print("%-16s: no disponible (%s)" % (nombre, e))

    try:
        print("disable_fb API  :", hasattr(omv, "disable_fb"))
    except Exception:
        pass

except Exception as e:
    print("Modulo omv no disponible:", e)

print("\n[6] MODULOS OPENMV")
for nombre in ("sensor", "mjpeg", "pyb", "machine", "omv"):
    try:
        __import__(nombre)
        print("OK    :", nombre)
    except Exception as e:
        print("ERROR :", nombre, "-", e)

print("\n[7] CAPACIDADES MJPEG")
try:
    import mjpeg
    print("Modulo mjpeg cargado correctamente")
    print("NOTA: count(), size() y sync() dependen de la version del firmware.")
except Exception as e:
    print("ERROR cargando mjpeg:", e)

print("\n========================================")
print(" FIN DEL TEST")
print("========================================")
