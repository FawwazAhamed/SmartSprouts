# USING MICROPYTHON

import ioty.monitor
from ioty import pin
import time
from machine import Pin, time_pulse_us
import machine
import ssd1306
import scaled_text
import network
import usocket as socket
from neopixel import NeoPixel
import uasyncio as asyncio
import _thread

pin.digital_write(12, 0)
# Initialise OLED display
scl_pin = machine.Pin(22)
sda_pin = machine.Pin(21)
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=100000)
ssd1306_i2c = ssd1306.SSD1306_I2C(128, 64, i2c, 60)
ssd1306_i2c.fill(0)
ssd1306_i2c.show()
text_scaler = scaled_text.ScaledText(ssd1306_i2c)

# Set up WiFi connection
wifi_ssid = "LAPTOP-DUSAORGU 0578"
wifi_password = "12345678"
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(wifi_ssid, wifi_password)
ssd1306_i2c.fill(0)
text_scaler.text("Waiting for WiFi", 0, 20, 1, scale=1)
ssd1306_i2c.show()
while not wifi.isconnected():
    print("Connecting to WiFi...")
    time.sleep(1)
print("Connected to WiFi")
ssd1306_i2c.fill(0)
text_scaler.text("WiFi Connected!", 0, 20, 1, scale=1)
ssd1306_i2c.show()
time.sleep(1)

# Set up TCP server
server_port = 8895  # Choose a port number
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', server_port))
server_socket.listen(1) 
print("TCP server listening on port", server_port)

# Pumping function
def pump():
    pin.digital_write(4, 1)
    time.sleep(2)  # Time that motor runs
    pin.digital_write(4, 0)

# Interpolating function
def math_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

ssd1306_i2c.fill(0)
text_scaler.text("Awaiting Phone", 0, 20, 1, scale=1)
ssd1306_i2c.show()
# Accept a connection outside the loop
client_socket, client_address = server_socket.accept()

ssd1306_i2c.fill(0)
text_scaler.text("Phone Connected!", 0, 20, 1, scale=1)
ssd1306_i2c.show()

time.sleep(1)

SOUND_SPEED=340 # Vitesse du son dans l'air
TRIG_PULSE_DURATION_US=10

trig_pin = Pin(5, Pin.OUT)
echo_pin = Pin(18, Pin.IN)

piny = Pin(13, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(piny, 5)   # create NeoPixel driver on GPIO0 for 8 pixels

water_level = None
water_percent = None
buzzer_on = None

# Define the pin connected to the buzzer
buzzer_pin = machine.Pin(12, machine.Pin.OUT)

# Create a PWM object with a frequency of 1000 Hz
buzzer_pwm = machine.PWM(buzzer_pin, freq=1000)

def runner():
    global water_level
    global water_percent
    global buzzer_on
    buzzer_on = False
    while True:
        # Prepare le signal
        trig_pin.value(0)
        time.sleep_us(5)
        # Créer une impulsion de 10 µs
        trig_pin.value(1)
        time.sleep_us(TRIG_PULSE_DURATION_US)
        trig_pin.value(0)
    
        ultrason_duration = time_pulse_us(echo_pin, 1, 30000) # Renvoie le temps de propagation de l'onde (en µs)
        distance_cm = SOUND_SPEED * ultrason_duration / 20000
        if distance_cm < 4:
            water_level = 6
            water_percent = "100%"
            buzzer_on = False
        if 4 < distance_cm < 6.4:
            water_level = 5
            water_percent = "~80%"
            buzzer_on = False
        if 6.4 < distance_cm < 9.6:
            water_level = 4
            water_percent = "~60%"
            buzzer_on = False
        if 9.6 < distance_cm < 12.8:
            water_level = 3
            water_percent = "~20%"
            buzzer_on = False
        if 12.8 < distance_cm:
            water_level = 2
            water_percent = "~5%"
            buzzer_on = True
            message4 = "Low Water Level!\n"
            client_socket.send(message4.encode("utf-8"))
            #Buzzer()
        print(f"Distance : {distance_cm} cm")
        
        
        
        message1 = f"Water Left in Tank : {water_percent}\n"
        oled1 = "Tank: " + str(water_percent)
        
        # Get data
        reading = pin.analog_read(32)
        percent = min(max(math_map(reading, 36000, 14000, 0, 100), 0), 100)
        percentage = round(percent, 1)
        print(f"{percentage}%")
        oled2 = '{}%'.format(percentage)
        
        oled3 = "H20: " + oled2
        
        # Display on LED
        ssd1306_i2c.fill(0)
        text_scaler.text(oled3, 0, 10, 1, scale=1)
        text_scaler.text(oled1, 0, 30, 1, scale=1)
        ssd1306_i2c.show()
        
        message2 = f"Moisture Level: {percentage}%\n\n"
        #client_socket.send(message1.encode("utf-8"))
        #client_socket.send(message2.encode("utf-8"))
        print("Sent data")
        
        # Pump check
        if percentage < 10:  # Add function to change this threshold
            pump()
            message3 = "Pump is activated\n" + message2
            client_socket.send(message3.encode("utf-8"))
        
        time.sleep(0.1)
        
def LED():
    while not wifi.isconnected():
        np[0] = (0, 0, 0) # set the first pixel to white
        np[1] = (0, 0, 0) # set the first pixel to white
        np[2] = (0, 0, 0) # set the first pixel to white
        np[3] = (0, 0, 0) # set the first pixel to white
        np[4] = (0, 0, 0) # set the first pixel to white
        np.write()
        time.sleep(2)
    while True:
        if water_level == 6:
            np[0] = (0, 200, 0) # set the first pixel to white
            np[1] = (0, 200, 0) # set the first pixel to white
            np[2] = (0, 200, 0) # set the first pixel to white
            np[3] = (0, 200, 0) # set the first pixel to white
            np[4] = (0, 200, 0) # set the first pixel to 
            buzzer_pwm.duty(0)

        if water_level == 5:
            np[0] = (0, 0, 0) # set the first pixel to white
            np[1] = (40, 160, 0) # set the first pixel to white
            np[2] = (40, 160, 0) # set the first pixel to white
            np[3] = (40, 160, 0) # set the first pixel to white
            np[4] = (40, 160, 0) # set the first pixel to 
            buzzer_pwm.duty(0)
        
        if water_level == 4:
            np[0] = (0, 0, 0) # set the first pixel to white
            np[1] = (0, 0, 0) # set the first pixel to white
            np[2] = (40, 120, 0) # set the first pixel to white
            np[3] = (40, 120, 0) # set the first pixel to white
            np[4] = (40, 120, 0) # set the first pixel to 
            buzzer_pwm.duty(0)
            
        if water_level == 3:
            np[0] = (0, 0, 0) # set the first pixel to white
            np[1] = (0, 0, 0) # set the first pixel to white
            np[2] = (0, 0, 0) # set the first pixel to white
            np[3] = (120, 40, 0) # set the first pixel to white
            np[4] = (120, 40, 0) # set the first pixel to
            buzzer_pwm.duty(0)
            
        if water_level == 2:
            np[0] = (0, 0, 0) # set the first pixel to white
            np[1] = (0, 0, 0) # set the first pixel to white
            np[2] = (0, 0, 0) # set the first pixel to white
            np[3] = (0, 0, 0) # set the first pixel to white
            np[4] = (200, 0, 0) # set the first pixel to 
            buzzer_pwm.freq(2000)
            buzzer_pwm.duty(10)  # 50frequency% duty cycle (adjust as needed)
            
        np.write()              # write data to all pixels
        time.sleep(0.1)

        
        
        

# Start both tasks concurrently using threads
_thread.start_new_thread(runner, ())
_thread.start_new_thread(LED, ())

# Keep the main thread running
while True:
    pass
