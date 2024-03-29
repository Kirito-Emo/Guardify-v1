# Vault project

# Imports
from machine import Pin, SoftI2C, PWM
import time
import ssd1306
import network
import ujson
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
SERVO_ANGLE_UNLOCKED = 246  # Servo angle for unlocked state
SERVO_ANGLE_LOCKED = 84     # Servo angle for locked state

# MQTT Configuration
MQTT_CLIENT_ID = "Guardify"             # MQTT client ID
MQTT_BROKER = 'test.mosquitto.org'      # MQTT broker address
MQTT_TOPIC = b'alert-push'              # MQTT topic to publish the alert message

# Password configuration
PASSWORD = b'1234'  # Change this to the desired password

# Buzzer Configuration
BUZZER_FREQ_WRONG = 100    # Frequency for wrong password
BUZZER_FREQ_ALARM = 1000   # Frequency for alarm
BUZZER_FREQ_SUCCESS = 500  # Frequency for successful unlock

# Global Variables
password_attempts = 0
is_locked = True
display = None
led_r = Pin(LED_PIN_R, Pin.OUT)
led_g = Pin(LED_PIN_G, Pin.OUT)
led_b = Pin(LED_PIN_B, Pin.OUT)
buzzer = PWM(Pin(BUZZER_PIN), freq=BUZZER_FREQ_WRONG, duty=0)
servo = PWM(Pin(SERVO_PIN))
user_password = None

def setup():
    # Initialize RGB LED pins
    led_r.off()
    led_g.off()
    led_b.on()

    # Initialize buzzer pin
    buzzer.duty(0)

    # Initialize OLED display
    i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    global display
    display = ssd1306.SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    display.text('Vault locked!', 20, 10)
    display.show()

    # Initialize servo
    servo.freq(SERVO_FREQ)
    servo.duty(SERVO_ANGLE_LOCKED)

    return led_r, led_g, led_b, buzzer, servo

def buzz(freq, duration):
    buzzer.freq(freq)  # Change the frequency
    buzzer.duty(512)  # Start the buzzer
    time.sleep(duration)
    buzzer.duty(0)  # Stop the buzzer

def unlock_vault():
    # Print the message for successful unlocking
    display.fill(0)
    display.text('Vault', 25, 10)
    display.text('Unlocked.', 25, 30)
    display.show()

    # Turn off the blue led
    led_b.off()

    # Turn on the green led and buzz at the same time
    led_g.on()
    buzz(BUZZER_FREQ_SUCCESS, 1)  # Moved this up to sound with the green light

    # Move the servo to open the door gradually
    for angle in range(SERVO_ANGLE_LOCKED, SERVO_ANGLE_UNLOCKED):
        servo.duty(angle)
        time.sleep(0.1)  # Pause briefly to allow the servo to move
    
    # Lock the vault automatically
    lock_vault()
    
def lock_vault():
    # Move the servo to close the door gradually
    for angle in range(SERVO_ANGLE_UNLOCKED, SERVO_ANGLE_LOCKED, -1):
        servo.duty(angle)
        time.sleep(0.1)  # Pause briefly to allow the servo to move

    # Display message and LEDs after door closure
    # Print the message for locking
    display.fill(0)
    display.text('Vault locked!', 20, 10)
    display.show()

    # Turn off the green led
    led_g.off()

    # Turn on the blue led
    led_b.on()

    # Emit a sound (optional, or use another frequency to indicate lock)
    buzz(BUZZER_FREQ_WRONG, 1)

    global is_locked
    is_locked = True

def trigger_alarm():
    global MQTT_TOPIC

    # Display a warning message on the OLED display
    display.fill(0)
    display.text('WARNING!', 20, 10)
    display.text('Intrusion', 25, 30)
    display.text('detected', 30, 40)
    display.show()

    # Turn on the red led
    led_r.on()

    # Turn off the blue led
    led_b.off()

    # Emit a sound
    buzz(BUZZER_FREQ_ALARM, 3)

    # Delay for a certain period of time (e.g., 2 seconds)
    time.sleep(2)

    # Return to the blue LED
    led_r.off()
    led_b.on()

    # Publish the alert message via MQTT
    client.publish(MQTT_TOPIC, "WARNING! Intrusion detected!")

def wrong_password():
    # Display a message of wrong PIN on the OLED display
    display.fill(0)
    display.text('Wrong PIN!', 20, 10)
    display.show()

    # Activate the red LED
    led_r.on()

    # Turn off the blue LED
    led_b.off()

    # Emit a sound for a wrong try
    buzz(BUZZER_FREQ_WRONG, 0.5)

    # Delay for a certain period of time (e.g., 1 second)
    time.sleep(2)

    # Return to the blue LED
    led_r.off()
    buzzer.duty(0)  # Stop the buzzer
    led_b.on()

    if password_attempts < 3:
        # Prompt for password input
        display.fill(0)
        display.text('Insert PIN:', 20, 20)
        display.show()

setup()

# Callback function to use when a msg is received from the broker
def subCallback(topic, msg):
    global user_password, password_attempts

    print(topic, msg)
    
    if(topic == MQTT_TOPIC):
        user_password = msg
        print(user_password)

        if(user_password == PASSWORD):
            unlock_vault()
            password_attempts = 0
            is_locked = False
        else:
            password_attempts += 1
            if password_attempts >= 3:
                wrong_password()
                trigger_alarm()
            else:
                wrong_password()

# Connect to MQTT broker
display.fill(0)
display.text('Connecting to', 0, 0)
display.text('WiFi...', 0, 10)
display.show()
time.sleep(1)
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')

while not sta_if.isconnected():
    display.fill(0)
    display.text('Connecting.', 0, 0)
    display.show()
    time.sleep(1)
    print(".", end="")
    time.sleep(1)

display.fill(0)
display.text('WiFi Connected!', 0, 0)
display.show()
time.sleep(1)
print(" Connected!")

print("Connecting to MQTT server... ", end="")
display.fill(0)
display.text('Connecting to', 0, 0)
display.text('MQTT server...', 0, 10)
display.show()
time.sleep(1)

try:
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(subCallback)
    client.connect()
    client.subscribe(MQTT_TOPIC)

    display.fill(0)
    display.text('MQTT Connected!', 0, 0)
    display.show()
    time.sleep(1)
    print("Connected to MQTT broker!")
except Exception as ex:
    display.fill(0)
    display.text('Failed to', 0, 0)
    display.text('connect to MQTT', 0, 10)
    display.text('broker:', 0, 20)
    display.text(str(ex), 0, 30)
    display.show()
    time.sleep(1)
    print("Failed to connect to MQTT broker:", str(ex))

# Prompt for password input
display.fill(0)
display.text('Insert PIN:', 20, 20)
display.show()

while password_attempts < 3:
    client.check_msg()