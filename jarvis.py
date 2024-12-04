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
arduino = serial.Serial(port='/dev/cu.usbserial-120', baudrate=9600, timeout=.1)
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
    data = f"<\"{message}\", {state}, {r}, {g}, {b}>"
    print(f"Sending: {data}")
    arduino.write(bytes(data, 'utf-8'))
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
        print("Waiting for wake word.")
        voice_command = recognize_speech_from_mic(recognizer, microphone)

        if voice_command["error"]:
            continue

        if voice_command["transcription"] and "computer" in voice_command["transcription"].lower():
            listening = True
            sendData("Welcome sir", "wake", 0, 150, 255)
            speak_text("Welcome sir. How can I assist you?")
        else:
            continue

    # Await command
    if listening:
        print("Listening...")
        command = recognize_speech_from_mic(recognizer, microphone)

        if command["error"]:
            print("Error in recognition.")
            speak_text("I didn't catch that. Please try again.")
            continue

        if command["transcription"]:
            transcript = command["transcription"].lower()
            print(f"Command: {transcript}")

            if "color" in transcript:
                color_word = next((word.text for word in nlp(transcript) if word.text in HTML4_NAMES), None)
                if color_word:
                    user_color = getColor(color_word)
                    if user_color:
                        r, g, b = map(int, user_color.split(","))
                        sendData("Color updated", "on", r, g, b)
                        speak_text(f"Color set to {color_word}.")
                    else:
                        speak_text("Sorry, I couldn't understand the color.")
            elif "weather" in transcript:
                location, temp = get_weather()
                speak_text(f"The temperature in {location} is {temp}.")
                sendData(f"{location} {temp}", "on", 0, 150, 255)
            elif "turn off" in transcript:
                listening = False
                sendData("Goodbye", "off", 0, 0, 0)
                speak_text("Goodbye.")
