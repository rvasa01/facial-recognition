import os
import subprocess
import sys
import RPi.GPIO as GPIO
import time
import json

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Set pin 17 as input with pull-up resistor
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Define GPIO pins for L298N
motor_pins = {
    "3": {"ENA": 17, "IN1": 27, "IN2": 22},
    "1": {"ENA": 12, "IN1": 6, "IN2": 5},
    "2": {"ENA": 23, "IN1": 24, "IN2": 25}, 
    "0": {"ENA": 21, "IN1": 20, "IN2": 16}         
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

def run_command(command, cwd=None):
    """Execute a command and handle errors"""
    try:
        subprocess.run(command, check=True, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def dispense(medicineIndex):
    extend_actuator(str(medicineIndex), speed=100)
    time.sleep(10)
    stop_actuator(str(medicineIndex))
    retract_actuator(str(medicineIndex), speed=100)
    time.sleep(10)
    stop_actuator(str(medicineIndex))

def main():
    # Get home directory
    home = os.path.expanduser("~")
    try:
        print("Ready for command")
        while True:
            button1 = GPIO.input(18)
            button2 = GPIO.input(15)
            button3 = GPIO.input(14)
            if button1 == GPIO.LOW:
               # print("Button1 Pressed")
                # Button 1 
                if "VIRTUAL_ENV" in os.environ:
                    del os.environ["VIRTUAL_ENV"]
                    # Restore original PATH without venv
                    os.environ["PATH"] = ":".join([p for p in os.environ["PATH"].split(":")
                                                if not (p.startswith("/usr/src/Python-3.9.16/DIY_eng_CoralUSB"))])
                    if "PYTHONPATH" in os.environ:
                        del os.environ["PYTHONPATH"]
                print("1. Capturing reference images...")
                ref_cmd = f"python3 test.py"
                run_command(ref_cmd, cwd=f"{home}/facial-recognition-dispenser")
                
                # print("\n2. Activating virtual environment...")
                venv_path = "/usr/src/Python-3.9.16/DIY_eng_CoralUSB"
                # Activate virtual environment by modifying PATH and PYTHONPATH
                os.environ["PATH"] = f"{venv_path}/bin:{os.environ['PATH']}"
                os.environ["PYTHONPATH"] = f"{venv_path}/lib/python3.9/site-packages"
                os.environ["VIRTUAL_ENV"] = venv_path
                
                print("\n2. Generating embeddings and adding to database...")
                db_cmd = f"python3 generate_db.py --images {home}/facial-recognition-dispenser/detected_faces --db_dir ../pretrained_model"
                run_command(db_cmd, cwd=f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/utils")
                print("Ready for command")
            if button2 == GPIO.LOW:
               # print("Button2 Pressed")
               # delete counts.json
                counts_path = f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/inference/counts.json"
                if os.path.exists(counts_path):
                    os.remove(counts_path)
                    print("Deleted previous counts.json")
                # Button 2
                venv_path = "/usr/src/Python-3.9.16/DIY_eng_CoralUSB"
                # Activate virtual environment by modifying PATH and PYTHONPATH
                os.environ["PATH"] = f"{venv_path}/bin:{os.environ['PATH']}"
                os.environ["PYTHONPATH"] = f"{venv_path}/lib/python3.9/site-packages"
                os.environ["VIRTUAL_ENV"] = venv_path
                print("\n3. Recording footage to analyze...")   
                record_cmd = "libcamera-vid -t 5000 -o output.h264 --shutter 10000 --width 640 --height 480"
                run_command(record_cmd, cwd=f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/inference")

                print("\n4. Running face recognition...")   
                recog_cmd = "python3 inference_video.py --coral_tpu --input=output.h264"
                run_command(recog_cmd, cwd=f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/inference")
                # open counts.json and return the name with the highest count
                # counts_path = f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/inference/counts.json"
                try:
                    with open(counts_path, 'r') as f:
                        counts = json.load(f)
                    if counts:
                        # Find name with maximum count
                        winner_name = max(counts.items(), key=lambda x: x[1])[0]
                        winner_count = counts[winner_name]
                        print(f"\nMost detected person: {winner_name} (count: {winner_count})")
                        longterm_counts_path = os.path.join(os.path.dirname(__file__), "longterm_counts.json")
                        try:
                            # Load existing counts or create new dict
                            if os.path.exists(longterm_counts_path):
                                with open(longterm_counts_path, 'r') as f:
                                    longterm_counts = json.load(f)
                                
                            else:
                                longterm_counts = {}
                                # dispense(0)
                            
                            # Update count for winner
                            if winner_name in longterm_counts:
                                longterm_counts[winner_name] += 1
                                longterm_counts[winner_name] = longterm_counts[winner_name] % 4
                            else:
                                longterm_counts[winner_name] = 0
                            
                            # Save updated counts
                            with open(longterm_counts_path, 'w') as f:
                                json.dump(longterm_counts, f, indent=2)
                            dispense(longterm_counts[winner_name])
                            print(f"Updated medicine index for {winner_name}: {longterm_counts[winner_name]}")
                            
                        
                        except Exception as e:
                            print(f"Error updating longterm counts: {str(e)}")                    
                    else:
                        print("No detections found in counts.json")
                except FileNotFoundError:
                    print("counts.json not found. No detections recorded.")
                except json.JSONDecodeError:
                    print("Error reading counts.json: Invalid JSON format")
                # maintain another longterm_counts json file with the name returned here, increment count if it exists, else add it with count 1
                print("Ready for command")
            if button3 == GPIO.LOW:
                print("Button3 Pressed")
                # RESET DB and LABEL.JSON
                #print("Button3 Pressed - Resetting all databases...")
                # Define paths
                pretrained_model_dir = f"{home}/coral/pycoral/Mobilefacenet-TF2-coral_tpu/pretrained_model"
                files_to_delete = [
                    f"{pretrained_model_dir}/label.json",
                    f"{pretrained_model_dir}/db.npy",
                    f"{pretrained_model_dir}/label.npy",
                    os.path.join(os.path.dirname(__file__), "longterm_counts.json")
                ]
                
                # Delete each file if it exists
                for file_path in files_to_delete:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Deleted: {os.path.basename(file_path)}")
                        else:
                            print(f"File not found: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"Error deleting {os.path.basename(file_path)}: {str(e)}")
                
                print("Reset complete")
                print("Ready for command")

            time.sleep(0.2)
    except KeyboardInterrupt:
        GPIO.cleanup()
    
    
    
    
if __name__ == "__main__":
    main()