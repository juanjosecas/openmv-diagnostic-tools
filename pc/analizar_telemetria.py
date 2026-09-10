# Python 3.10+ | solo biblioteca estándar
# ============================================================
# analizar_telemetria.py
#
# OBJETIVO:
# Leer diagnostico_telemetria.csv generado por la OpenMV y
# resumir automáticamente duración, FPS, tiempos de captura,
# escritura, tamaño del MJPEG y posibles gaps en el log.
#
# USO:
#   python analizar_telemetria.py diagnostico_telemetria.csv
# ============================================================

import csv
import sys
from pathlib import Path


def to_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def to_int(value, default=None):
    try:
        return int(float(value))
    except Exception:
        return default


def main():
    if len(sys.argv) != 2:
        print("Uso: python analizar_telemetria.py diagnostico_telemetria.csv")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print("ERROR: no existe:", path)
        raise SystemExit(1)

    rows = []
    comments = []

    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        raw_lines = f.readlines()

    data_lines = []
    for line in raw_lines:
        if line.startswith("#"):
            comments.append(line.strip())
        elif line.strip():
            data_lines.append(line)

    if not data_lines:
        print("ERROR: no hay filas de telemetría.")
        raise SystemExit(1)

    reader = csv.DictReader(data_lines)
    rows = list(reader)

    if not rows:
        print("ERROR: no hay datos válidos.")
        raise SystemExit(1)

    times = [to_float(r.get("time_s")) for r in rows]
    times = [x for x in times if x is not None]

    fps_values = [to_float(r.get("fps")) for r in rows]
    fps_values = [x for x in fps_values if x is not None]

    write_avg = [to_float(r.get("write_ms_avg")) for r in rows]
    write_avg = [x for x in write_avg if x is not None]

    capture_avg = [to_float(r.get("capture_ms_avg")) for r in rows]
    capture_avg = [x for x in capture_avg if x is not None]

    last = rows[-1]

    print("========================================")
    print(" RESUMEN DE TELEMETRIA OPENMV")
    print("========================================")
    print("Archivo:", path)
    print("Filas:", len(rows))

    if times:
        print("Duración registrada: %.1f s" % times[-1])

    print("Frames finales:", last.get("frames", "?"))
    print("Estado final:", last.get("status", "?"))

    if fps_values:
        print("FPS inicial/final: %.2f / %.2f" % (fps_values[0], fps_values[-1]))
        print("FPS min/max: %.2f / %.2f" % (min(fps_values), max(fps_values)))

    if capture_avg:
        print("Captura media final: %.2f ms" % capture_avg[-1])

    if write_avg:
        print("Escritura media final: %.2f ms" % write_avg[-1])

    if last.get("write_ms_max"):
        print("Peor escritura: %s ms" % last.get("write_ms_max"))

    if last.get("mjpeg_size_bytes"):
        size = to_int(last.get("mjpeg_size_bytes"), -1)
        if size is not None and size >= 0:
            print("Tamaño MJPEG registrado: %.2f MB" % (size / 1024 / 1024))
        else:
            print("Tamaño MJPEG registrado: API no disponible")

    if last.get("free_mb"):
        print("Espacio libre final: %s MB" % last.get("free_mb"))

    print("\nGAPS EN TELEMETRIA")
    gaps = []
    if len(times) >= 2:
        intervals = [b - a for a, b in zip(times, times[1:])]
        typical = sorted(intervals)[len(intervals) // 2]
        threshold = max(typical * 2.5, typical + 5)
        for i, dt in enumerate(intervals, start=1):
            if dt > threshold:
                gaps.append((i, dt))

    if gaps:
        for idx, dt in gaps:
            print("WARNING: gap antes de fila %d: %.1f s" % (idx + 1, dt))
    else:
        print("No se detectaron gaps grandes en el CSV.")

    print("\nHEURISTICAS")
    if fps_values and len(fps_values) >= 2:
        if fps_values[-1] < fps_values[0] * 0.75:
            print("WARNING: caída de FPS >25% entre inicio y final.")
        else:
            print("FPS sin caída >25% entre inicio y final.")

    if write_avg and capture_avg:
        if write_avg[-1] > capture_avg[-1] * 2 and write_avg[-1] > 20:
            print("WARNING: escritura domina claramente el costo por frame.")
        else:
            print("La escritura no domina claramente el costo por frame según esta heurística.")

    if comments:
        print("\nCOMENTARIOS / ERRORES DEL LOG")
        for line in comments:
            print(line)


if __name__ == "__main__":
    main()
