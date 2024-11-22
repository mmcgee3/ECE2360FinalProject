import speech_recognition as sr
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
            action = token.text.upper()
        elif token.text in {"red", "green", "blue"}:
            if token.text == "red":
                color = "255, 0, 0"
            elif token.text == "green":
                color = "0, 255, 0"
            elif token.text == "blue":
                color = "0, 0, 255"
    
    # Format the command for the Arduino
    if action == "OFF":
        return "<off, 0, 0, 0>"
    elif action == "ON" and color:
        return f"<on, {color}>"
    else:
        return None


def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response

while True:
    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    