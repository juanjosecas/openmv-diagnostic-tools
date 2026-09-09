# MJPEG Video Recording Example
#
import sys
import sensor
import time
import mjpeg
import pyb
import machine
import gc

RED_LED_PIN = 1
BLUE_LED_PIN = 3
MAX_FILE_SIZE_MB = 4096  # Tamaño máximo por archivo en MB, debido a la microSD

# ------------------------------------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------------------------------------
print("Starting camera...")
sensor.reset()  # Initialize the camera sensor.
sensor.set_pixformat(sensor.GRAYSCALE)  # sensor.RGB565 or sensor.GRAYSCALE
RESOLUCION = sensor.QVGA
sensor.set_framesize(RESOLUCION)  # or sensor.QQVGA (or others)
print("please wait...")

sensor.skip_frames(time=2000)  # Let new settings take effect.
clock = time.clock()  # Tracks FPS.
sensor.skip_frames(time=0)  # Give the user time to get ready.

print("Configuring LEDs...")
pyb.LED(RED_LED_PIN).on()
sensor.skip_frames(time=0)     # time for the user to get ready
pyb.LED(RED_LED_PIN).off()
pyb.LED(BLUE_LED_PIN).on()
print("Camera ready")

# ------------------------------------------------------------------------------------------------
# COMPLETE ONLY THESE VARIABLES
# ------------------------------------------------------------------------------------------------
filename = "_ESTEBAN"
DESIRED_FPS = 15
DURATION_MINUTES = 1

# ------------------------------------------------------------------------------------------------
# CALCULATING FILE SIZE AND VIDEO INFORMATION
# ------------------------------------------------------------------------------------------------
frame_dummy = sensor.snapshot()
buffer = frame_dummy.compress()           # imagen tipo JPEG comprimida por defecto
tamano_bytes = len(buffer)

DURACION_SEG = DURATION_MINUTES * 60
DURATION_MILLISECONDS = (DURATION_MINUTES * 60 * 1000)  # in milliseconds
TIME_BETWEEN_FRAMES = (1000 // DESIRED_FPS)  # calculate time between frames, discard the rest

frames_totales = DESIRED_FPS * DURACION_SEG
tamano_estimado_bytes = frames_totales * tamano_bytes
tamano_estimado_mb = tamano_estimado_bytes / (1024*1024)

print("Configuración:")
print(" - FPS:", DESIRED_FPS)
print(" - Duración (min):", DURATION_MINUTES)
print(" - Frames totales:", frames_totales)
print(" - Tamaño estimado del video (MB): %.2f" % tamano_estimado_mb)

if tamano_estimado_mb > MAX_FILE_SIZE_MB:
    print("¡ATENCIÓN! El video final excedería los %.0f MB." % MAX_FILE_SIZE_MB)
    print("Disminuya el tiempo de grabacion o frames deseados")
    pyb.LED(BLUE_LED_PIN).off()
    print("  Ending script early")
    sys.exit()

# ------------------------------------------------------------------------------------------------
# CREATING FILE
# ------------------------------------------------------------------------------------------------
print("")
print("Creating file...")
m = None
try:
    m = mjpeg.Mjpeg(filename + ".mjpeg")
except Exception as e:
    print("  ERROR: {} not created: {}".format(filename, e))
    m = None

# chequeo que se haya creado el archivo, sino termino el script
if m is None:
    print("  Ending script early")
    pyb.LED(BLUE_LED_PIN).off()
    sys.exit()

# ------------------------------------------------------------------------------------------------
# RECORDING VIDEO
# ------------------------------------------------------------------------------------------------
print("")
print("RECORDING...")
saved_frames = 0
start_time = time.ticks_ms()

try:
    while time.ticks_diff(time.ticks_ms(), start_time) <= DURATION_MILLISECONDS:
        start_frame = time.ticks_ms()           # start of cycle
        frame = sensor.snapshot()  # May fail if sensor disconnects
        m.add_frame(frame)  # May fail if SD is full
        saved_frames += 1

        # properly limit FPS
        cycle_time = time.ticks_diff(time.ticks_ms(), start_frame)
        if cycle_time < TIME_BETWEEN_FRAMES:
            time.sleep_ms(TIME_BETWEEN_FRAMES - cycle_time)

        # show info every 128 frames
        if saved_frames % 128 == 0:
            time.sleep_ms(1)
            elapsed_s = time.ticks_diff(time.ticks_ms(), start_time) / 1000
            minutes = int(elapsed_s // 60)
            seconds = int(elapsed_s % 60)
            avg_fps = saved_frames / elapsed_s
            print("Time: {:02d}:{:02d} min Frames: {} Average FPS: {:.1f}".format(
                minutes, seconds, saved_frames, avg_fps))

        # blink LED
        if saved_frames % 16 == 0:
            pyb.LED(BLUE_LED_PIN).toggle()

except Exception as e:
    print("ERROR DURING RECORDING: {}".format(e))
    print("  Ending script early")
    pyb.LED(BLUE_LED_PIN).off()
    sys.exit()

# ------------------------------------------------------------------------------------------------
# FINALIZING RECORDING
# ------------------------------------------------------------------------------------------------
finally:
    # Try to close the file
    print("")
    print("Finalizing recording...")
    try:
        # Intenta cerrar sin usar FPS
        m.close()
        print("  File closed successfully")
    except TypeError:
        # Intenta cerrar usando FPS (para H7 original o bibliotecas antiguas)
        m.close(DESIRED_FPS)
        print("  File closed successfully")
    except Exception as e:
        print("WARNING: Error closing file: {}".format(e))
        sys.exit()
    finally:
        pyb.LED(BLUE_LED_PIN).off()
        gc.collect()  # Libera los bloques no referenciados

    # END
    time.sleep_ms(1000)
    machine.reset()
