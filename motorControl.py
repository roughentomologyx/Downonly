import RPi.GPIO as GPIO
import time
import os
import signal
import sys

# Configuration
GPIO_PIN = 21
STATE_FILE = './motorTimeRemaining.txt'

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# Load state
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

# Save state
def save_state(time_remaining):
    with open(STATE_FILE, 'w') as f:
        f.write(str(time_remaining))

# Control motor
def control_motor():
    while True:
        time_remaining = load_state()
        if time_remaining > 0:
            GPIO.output(GPIO_PIN, GPIO.HIGH)
            time.sleep(1)
            time_remaining -= 1
            save_state(time_remaining)
        else:
            GPIO.output(GPIO_PIN, GPIO.LOW)
            time.sleep(1)

# Signal handler for graceful termination
def signal_handler(sig, frame):
    print('Exiting gracefully')
    GPIO.output(GPIO_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start the motor control loop
        control_motor()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the motor is turned off and GPIO is cleaned up
        GPIO.output(GPIO_PIN, GPIO.LOW)
        GPIO.cleanup()

