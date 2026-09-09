# ============================================================
# 01_versiones.py
#
# OBJETIVO:
# Mostrar información del firmware/runtime y comprobar que los
# módulos básicos de OpenMV estén disponibles.
#
# NO modifica archivos.
# NO graba video.
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

print("\n[5] MODULOS OPENMV")
for nombre in ("sensor", "mjpeg", "pyb", "machine"):
    try:
        __import__(nombre)
        print("OK    :", nombre)
    except Exception as e:
        print("ERROR :", nombre, "-", e)

print("\n========================================")
print(" FIN DEL TEST")
print("========================================")
