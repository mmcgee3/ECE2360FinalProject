import speech_recognition as sr
import serial
import time
import spacy
import webcolors
from gtts import gTTS
from playsound import playsound
import os
import requests

# Weather API
WEATHER_API_KEY = "3a04d1af9ceb64f266dbe905ff214cf7"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Load the English language model from spaCy
nlp = spacy.load("en_core_web_sm")

listening = False
user_color = "0, 150, 255"  # Default color is a bright blue

HTML4_NAMES = {
    'black': '#000000',
    'silver': '#c0c0c0',
    'gray': '#808080',
    'white': '#ffffff',
    'maroon': '#800000',
    'red': '#ff0000',
    'purple': '#800080',
    'fuchsia': '#ff00ff',
    'green': '#008000',
    'lime': '#00ff00',
    'olive': '#808000',
    'yellow': '#ffff00',
    'navy': '#000080',
    'blue': '#0000ff',
    'teal': '#008080',
    'aqua': '#00ffff',
}

# Initialize Arduino communication
arduino = serial.Serial(port='/dev/cu.usbserial-130', baudrate=9600, timeout=.1)
time.sleep(2)

def get_weather(location="Columbus"):
    """Fetches the current weather for a given location."""
    params = {
        "q": location,
        "appid": WEATHER_API_KEY,
        "units": "imperial"  # Use "metric" for Celsius
    }
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        temp = weather_data["main"]["temp"]
        return location, f"{temp:.1f}°F"
    except requests.RequestException as e:
        return "Error", "Unable to fetch data"

def sendData(message, state, r, g, b):
    """Send formatted data to the Arduino."""
    arduino.write(bytes(f"<{message}, {state}, {r}, {g}, {b}>", 'utf-8'))
    time.sleep(0.05)

def getColor(color):
    try:
        rgb = webcolors.name_to_rgb(color)
        return f"{rgb.red}, {rgb.green}, {rgb.blue}"
    except ValueError:
        return None

def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from microphone and return a response dictionary."""
    if not isinstance(recognizer, sr.Recognizer) or not isinstance(microphone, sr.Microphone):
        raise TypeError("`recognizer` must be `Recognizer` instance and `microphone` must be `Microphone` instance")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    response = {"success": True, "error": None, "transcription": None}

    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    return response

def speak_text(text):
    """Converts text to speech and plays it through the speakers."""
    tts = gTTS(text)
    filename = "temp_audio.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

while True:
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Wait for wake word
    if not listening:
        print("Waiting for wake word or motion detection.")
        voice_command = recognize_speech_from_mic(recognizer, microphone)

        if voice_command["error"]:
            continue

        if voice_command["transcription"] and "computer" in voice_command["transcription"].lower():
            listening = True
            sendData("Welcome sir.", "wake", 0, 150, 255)
            speak_text("Welcome sir.")
        # Check for "WAKE" signal from Arduino
        if arduino.in_waiting > 0:
            data = arduino.readline().decode('utf-8').strip()
            if data == "WAKE":
                listening = True
                wake_message = "Motion detected. Welcome sir."
                sendData(f"<wake, {user_color}>")
                print(wake_message)
                speak_text(wake_message)

    # Process commands
    if listening:
        print("Waiting for command.")
        voice_command = recognize_speech_from_mic(recognizer, microphone)

        if voice_command["error"]:
            continue

        if voice_command["transcription"]:
            doc = nlp(voice_command["transcription"].lower())
            
            if "weather" in voice_command["transcription"].lower():
                location = "Columbus"
                for token in doc:
                    if token.pos_ == "PROPN":
                        location = token.text
                        break
                location, temp = get_weather(location)
                sendData(f"{location}", "weather", 0, 0, 255)
                sendData(f"{temp}", "weather", 0, 0, 255)
                speak_text(f"The weather in {location} is {temp}.")

            elif "set color" in voice_command["transcription"].lower():
                for token in doc:
                    if token.text in HTML4_NAMES:
                        color_rgb = getColor(token.text)
                        if color_rgb:
                            r, g, b = map(int, color_rgb.split(", "))
                            sendData(f"Setting color to {token.text}", "on", r, g, b)
                            speak_text(f"Setting LED color to {token.text}")
                            user_color = color_rgb
                            break

            elif "turn off" in voice_command["transcription"].lower():
                sendData("Goodbye", "off", 0, 0, 0)
                speak_text("Turning off system.")
                listening = False
