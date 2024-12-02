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
        description = weather_data["weather"][0]["description"]
        temp = weather_data["main"]["temp"]
        weather_info = f"The current weather in {location} is {description} with a temperature of {temp}°F."
        return weather_info
    except requests.RequestException as e:
        return f"Unable to fetch weather data: {e}"

def sendData(x): 
    arduino.write(bytes(x, 'utf-8')) 
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
    while not listening:
        wake_message = "Waiting for wake word."
        print(wake_message)
        speak_text(wake_message)
        voice_command = recognize_speech_from_mic(recognizer, microphone)

        if voice_command["error"]:
            error_message = f"ERROR: {voice_command['error']}"
            print(error_message)
            speak_text(error_message)
            continue

        if voice_command["transcription"] and "computer" in voice_command["transcription"].lower():
            listening = True
            listening_message = "Welcome sir."
            sendData(f"<wake, {user_color}>")
            print(listening_message)
            speak_text(listening_message)

    # Process commands
    while listening:
        command_prompt = "Waiting for command."
        print(command_prompt)
        speak_text(command_prompt)
        voice_command = recognize_speech_from_mic(recognizer, microphone)

        if voice_command["error"]:
            error_message = f"ERROR: {voice_command['error']}"
            print(error_message)
            speak_text(error_message)
            continue

        if voice_command["transcription"]:
            user_input = f"You said: {voice_command['transcription']}"
            print(user_input)
            doc = nlp(voice_command["transcription"].lower())
            
            # Handle "weather" command
            if "weather" in voice_command["transcription"].lower():
                location = "Columbus"  # Default location
                for token in doc:
                    if token.pos_ == "PROPN":  # Extract proper nouns as potential location names
                        location = token.text
                        break
                weather_message = get_weather(location)
                print(weather_message)
                speak_text(weather_message)

            # Check for color command
            elif "set" in voice_command["transcription"].lower() and "color" in voice_command["transcription"].lower():
                # Extract color name
                for token in doc:
                    if token.text in HTML4_NAMES:
                        color_rgb = getColor(token.text)
                        if color_rgb:
                            user_color = color_rgb
                            success_message = f"Setting LED color to {token.text}"
                            sendData(f"<on, {user_color}>")
                            print(success_message)
                            speak_text(success_message)
                            break
                        else:
                            error_message = f"Color '{token.text}' not recognized."
                            print(error_message)
                            speak_text(error_message)
                            break
            
            # Handle "turn off" command
            elif "turn off" in voice_command["transcription"].lower():
                turn_off_message = "Turning off system."
                sendData(f"<off, {user_color}>")
                print(turn_off_message)
                speak_text(turn_off_message)
                listening = False
                break

            # Handle unrecognized commands
            else:
                unrecognized_message = "Command not recognized. Please try again."
                print(unrecognized_message)
                speak_text(unrecognized_message)
