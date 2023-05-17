# Vault project

# Imports
from machine import Pin, SoftI2C, PWM
import time
import ssd1306
import network
import ujson
import sys
from umqtt.simple import MQTTClient

# Pin Definitions
LED_PIN_R = 15   # Red LED pin
LED_PIN_G = 12   # Green LED pin
LED_PIN_B = 13   # Blue LED pin
BUZZER_PIN = 14  # Buzzer pin
SERVO_PIN = 5    # Servo pin

# OLED-Display Configuration
I2C_SCL_PIN = 22     # I2C SCL pin
I2C_SDA_PIN = 21     # I2C SDA pin
DISPLAY_WIDTH = 128  # OLED display width in pixels
DISPLAY_HEIGHT = 64  # OLED display height in pixels

# Servo Configuration
SERVO_FREQ = 50             # Servo motor frequency in Hz
SERVO_ANGLE_UNLOCKED = 90   # Servo angle for unlocked state
SERVO_ANGLE_LOCKED = 180    # Servo angle for locked state

# MQTT Configuration
MQTT_CLIENT_ID = "Guardify"             # MQTT client ID
MQTT_BROKER = 'test.mosquitto.org'      # MQTT broker address
MQTT_TOPIC = "alert-push"               # MQTT topic to publish the alert message

# Password configuration
PASSWORD = '1234'  # Change this to the desired password

# Global Variables
password_attempts = 0
is_locked = True
display = None
led_r = Pin(LED_PIN_R, Pin.OUT)
led_g = Pin(LED_PIN_G, Pin.OUT)
led_b = Pin(LED_PIN_B, Pin.OUT)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
servo = PWM(Pin(SERVO_PIN))
user_password = None

def setup():
    # Initialize RGB LED pins
    led_r.off()
    led_g.off()
    led_b.on()

    # Initialize buzzer pin
    buzzer.off()

    # Initialize OLED display
    i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    global display
    display = ssd1306.SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    display.text('Vault locked!', 12, 10)
    display.text('Insert pin: ', 20, 20)    
    display.show()

    # Initialize servo
    servo.freq(SERVO_FREQ)
    servo.duty(SERVO_ANGLE_LOCKED)

    return led_r, led_g, led_b, buzzer, servo

def unlock_vault():
    # Print the message for successful unlocking
    display.fill(0)  # Clear the display
    display.text('Cassaforte ', 22, 20)
    display.text('sbloccata.', 25, 30)
    display.show()

    # Turn off the blue led
    led_b.off()

    # Turn on the green led
    led_g.on()

    # Move the servo to open the door (90° degrees)
    servo.duty(SERVO_ANGLE_UNLOCKED)

    # Emit a sound
    #buzzer.tone(BUZZER_PIN, 1000, 500)  # Plays 1000Hz tone for 500ms
    buzzer.on()

def trigger_alarm():
    # Display a warning message on the OLED display
    display.fill(0)  # Clear the display
    display.text('ATTENZIONE!', 25, 10)
    display.text('Intrusione', 25, 30)
    display.text('rilevata', 30, 40)
    display.show()

    # Turn off the blue led
    led_b.off()

    # Turn on the red led
    led_r.on()

    # Emit a sound
    #buzzer.tone(BUZZER_PIN, 262, 3000) # Plays 262Hz tone for 3 seconds
    buzzer.on()

    # Publish the alert message via MQTT
    client.publish(MQTT_TOPIC, "ATTENZIONE! Cassaforte a rischio! Intrusione rilevata!")

def wrong_password():
    # Display a message of wrong PIN on the OLED display
    display.fill(0)  # Clear the display
    display.text('Pin errato!', 20, 10)
    display.show()

    # Activate the red LED
    led_r.on()

    # Delay for a certain period of time (e.g., 1 second)
    time.sleep(1)

    # Return to the blue LED
    led_r.off()
    led_b.on()

    # Emit a sound for a wrong try
    #buzzer.tone(BUZZER_PIN, 500, 500)  # Plays 500Hz tone for 500ms
    buzzer.on()

setup()

# Connect to MQTT broker
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')

while not sta_if.isconnected():
    print(".", end="")
    time.sleep(0.1)
print(" Connected!")

print("Connecting to MQTT server... ", end="")
try:
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.connect()
    print("Connected to MQTT broker!")
except Exception as ex:
    print("Failed to connect to MQTT broker:", str(ex))

while (user_password is not PASSWORD) and (password_attempts <= 3):
    user_password = input("Enter the PIN: ")    # Prompt the user to enter the PIN

    if user_password is PASSWORD:
        unlock_vault()
        password_attempts = 0
        is_locked = False
    else:
        password_attempts += 1
        
        if password_attempts >= 3:
            wrong_password()
            trigger_alarm()
            sys.exit()
        else:
            wrong_password()