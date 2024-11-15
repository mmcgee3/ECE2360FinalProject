import time
import serial

arduino = serial.Serial(port='/dev/cu.usbserial-120', baudrate=9600, timeout=.1)
time.sleep(2)

def sendData(x): 
    arduino.write(bytes(x, 'utf-8')) 
    time.sleep(0.05)

while True:
    ledState = input("Enter led state(on/off): ")
    ledState.capitalize
    rgb = '0, 0, 0'
    while True:
        color = input("Enter a color: ")
        if color == 'Red':
            rgb = '128, 0, 0'
            break
        elif color == 'Green':
            rgb = '0, 128, 0'
            break
        elif color == 'Blue':
            rgb = '0, 0, 128'
            break
        else :
            print("Invalid color")
    string = '<' + ledState + ', ' + rgb + '>'
    sendData(string)