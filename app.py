from flask import Flask, render_template, request, jsonify
from pynq import Overlay
from pynq.lib import AxiGPIO
import psutil

# Cargar el diseño base de la placa
base = Overlay("base.bit")

# Definir el pin que simula GPIO 24 en Raspberry Pi (adaptado para PYNQ-Z2)
from pynq.gpio import GPIO
SENSOR_PIN = GPIO(GPIO.get_gpio_pin(24), 'in')  # Configurar como entrada

# Configuración de los LEDs
leds = base.ip_dict['leds_gpio']
led_gpio = AxiGPIO(leds).channel1

# Crear la aplicación Flask
app = Flask(__name__)

# Página principal con los botones para controlar los LEDs
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para alternar el estado de los LEDs mediante AJAX
@app.route('/toggle_led', methods=['POST'])
def toggle_led():
    data = request.get_json()  # Obtener los datos enviados por AJAX
    led_id = data['led_id']

    # Leer el estado actual del LED
    current_state = led_gpio.read()

    # Alternar el estado del LED
    new_state = current_state ^ (1 << led_id)  # Cambiar el estado solo de ese LED

    # Escribir el nuevo estado
    led_gpio.write(new_state, 0b1111)

    # Devolver una respuesta con el ID y estado del LED
    led_state = "On" if (new_state >> led_id) & 1 else "Off"
    return jsonify({'ledId': f'led{led_id}', 'ledState': led_state})

# Ruta para obtener la información del sensor de proximidad

@app.route('/proximity', methods=['GET'])
def get_proximity_info():
    try:
        sensor_value = SENSOR_PIN.read()  # Leer el valor del sensor
        print(f"Valor del sensor: {sensor_value}")  # Imprime el valor en consola para depuración
        if SENSOR_PIN == 1:  # No hay obstáculo (valor bajo)
            sensor_state = "No obstacle"
        else:  # Hay un obstáculo (valor alto)
            sensor_state = "Obstacle detected"
    except Exception as e:
        print(f"Error leyendo el sensor: {e}")
        sensor_state = "Error leyendo el sensor"

    # Devolver el estado del sensor
    return jsonify({'sensorState': sensor_state})


# Ruta para obtener la información de monitorización
@app.route('/monitor', methods=['GET'])
def get_monitor_info():
    # Obtener uso de memoria
    mem = psutil.virtual_memory()
    total_mem = mem.total / (1024 * 1024)  # Convertir a MB
    used_mem = mem.used / (1024 * 1024)  # Convertir a MB

    # Obtener el uso de la CPU
    cpu_usage = psutil.cpu_percent(interval=1)  # Uso de la CPU en porcentaje

    # Obtener el uso del disco
    disk_usage = psutil.disk_usage('/')
    total_disk = disk_usage.total / (1024 * 1024 * 1024)  # Convertir a GB
    used_disk = disk_usage.used / (1024 * 1024 * 1024)  # Convertir a GB
    disk_percent = disk_usage.percent

    # Obtener estadísticas de red
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent / (1024 * 1024)  # Convertir a MB
    bytes_recv = net_io.bytes_recv / (1024 * 1024)  # Convertir a MB

    # Estado de LEDs (binario convertido a string)
    led_state = format(led_gpio.read(), '04b')  # Estado de los LEDs en binario

    # Construir la respuesta
    monitor_info = (
        f"  Memoria: {used_mem:.2f} MB / {total_mem:.2f} MB\n\r"
        f"  CPU Usage: {cpu_usage}%\n\r"
        f"  Disk: {used_disk:.2f} GB / {total_disk:.2f} GB ({disk_percent}%)\n\r"
        f"  Red: Enviado: {bytes_sent:.2f} MB, Recibido: {bytes_recv:.2f} MB\n\r"
        f"  Estado de los LEDs: {led_state} (binario)\n\r"
    )
    return monitor_info

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

