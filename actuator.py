import RPi.GPIO as GPIO
import time

# Define GPIO pins for L298N
motor_pins = {
    #"act1": {"ENA": 17, "IN1": 27, "IN2": 22},
    #"act2": {"ENA": 12, "IN1": 6, "IN2": 5},
    "act3": {"ENA": 23, "IN1": 24, "IN2": 25}, 
   # "act4": {"ENA": 21, "IN1": 20, "IN2": 16}         
}

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Dictionary to store PWM objects
pwm_objects = {}

# Set up pins and create PWM objects for each actuator
for actuator, pins in motor_pins.items():
    GPIO.setup(pins["ENA"], GPIO.OUT)
    GPIO.setup(pins["IN1"], GPIO.OUT)
    GPIO.setup(pins["IN2"], GPIO.OUT)
    pwm_objects[actuator] = GPIO.PWM(pins["ENA"], 100)  # 100 Hz frequency
    pwm_objects[actuator].start(0)  # Start with 0% duty cycle

def extend_actuator(actuator_id, speed=100):
    """Extend the specified linear actuator"""
    pins = motor_pins[actuator_id]
    pwm_objects[actuator_id].ChangeDutyCycle(speed)
    GPIO.output(pins["IN1"], GPIO.HIGH)
    GPIO.output(pins["IN2"], GPIO.LOW)

def retract_actuator(actuator_id, speed=100):
    """Retract the specified linear actuator"""
    pins = motor_pins[actuator_id]
    pwm_objects[actuator_id].ChangeDutyCycle(speed)
    GPIO.output(pins["IN1"], GPIO.LOW)
    GPIO.output(pins["IN2"], GPIO.HIGH)

def stop_actuator(actuator_id):
    """Stop the specified linear actuator"""
    pins = motor_pins[actuator_id]
    GPIO.output(pins["IN1"], GPIO.LOW)
    GPIO.output(pins["IN2"], GPIO.LOW)
    pwm_objects[actuator_id].ChangeDutyCycle(0)

try:
        # Example usage for all actuators
    for actuator_id in motor_pins.keys():
        print(f"Extending {actuator_id}...")
        extend_actuator(actuator_id, speed=100)
    time.sleep(10)  # Run for 5 seconds
    
    print("Stopping all actuators...")
    for actuator_id in motor_pins.keys():
        stop_actuator(actuator_id)
    time.sleep(1)  # Wait for 1 second
    
    print("Retracting all actuators...")
    for actuator_id in motor_pins.keys():
        retract_actuator(actuator_id, speed=100)
    time.sleep(10)  # Run for 5 seconds
    
    print("Stopping all actuators...")
    for actuator_id in motor_pins.keys():
        stop_actuator(actuator_id)

except KeyboardInterrupt:
    print("\nProgram stopped by user")
    GPIO.cleanup()  # Clean up GPIO on CTRL+C exit

finally:
    for pwm in pwm_objects.values():
        pwm.stop()  # Stop all PWM objects
    GPIO.cleanup()  # Clean up GPIO on normal exit