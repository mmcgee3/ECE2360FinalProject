import serial
import time
import spacy

# Load the English language model from spaCy
nlp = spacy.load("en_core_web_sm")

arduino = serial.Serial(port='/dev/cu.usbserial-120', baudrate=9600, timeout=.1)
time.sleep(2)

def sendData(x): 
    arduino.write(bytes(x, 'utf-8')) 
    time.sleep(0.05)

def parse_command(command):
    # Process the user input using spaCy
    doc = nlp(command.lower())
    
    # Extract tokens for action and color
    action = None
    color = None
    
    for token in doc:
        if token.text in {"on", "off"}:
            action = token.text.lower()
        elif token.text in {"red", "green", "blue"}:
            if token.text == "red":
                color = "255, 0, 0"
            elif token.text == "green":
                color = "0, 255, 0"
            elif token.text == "blue":
                color = "0, 0, 255"
    
    # Format the command for the Arduino
    if action == "OFF":
        return "<Off, 0, 0, 0>"
    elif action == "ON" and color:
        return f"<ON, {color}>"
    else:
        return None
    
while True:
    user_input = input("Enter a command for the LED (e.g., 'turn on red', 'turn off'): ")
    command = parse_command(user_input)
    
    if command:
        print(f"Sending command to Arduino: {command}")
        sendData(command)
    else:
        print("Invalid command.")
