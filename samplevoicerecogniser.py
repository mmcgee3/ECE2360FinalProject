import speech_recognition as sr
import serial
import time
import spacy
import webcolors

# Load the English language model from spaCy
nlp = spacy.load("en_core_web_sm")

arduino = serial.Serial(port='/dev/cu.usbserial-120', baudrate=9600, timeout=.1)
time.sleep(2)

def sendData(x): 
    arduino.write(bytes(x, 'utf-8')) 
    time.sleep(0.05)
    
def getColor(color):
    try:
        rgb = webcolors.name_to_rgb(color)
        return f"{rgb.red}, {rgb.green}, {rgb.blue}"
    except ValueError:
        return 

def parse_command(command):
    # Process the user input using spaCy
    doc = nlp(command.lower())
    
    # Extract tokens for action and color
    action = None
    color = None
    
    for token in doc:
        if token.text in {"on", "off"}:
            action = token.text.upper()
        else:
            color = getColor(token.text)
            if color:
                break
    
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
    
    # give the user 5 attempts to get a clear audio command
    PROMPT_LIMIT = 5
    for j in range(PROMPT_LIMIT):
        print("Say a command for the LED (e.g., 'turn on red', 'turn off'): ")
        voice_command = recognize_speech_from_mic(recognizer, microphone)
        if voice_command["transcription"]:
            break
        if not voice_command["success"]:
            break
        print("I didn't catch that. What did you say?\n")
        
    if voice_command["error"]:
        print("ERROR: {}".format(voice_command["error"]))
        break
    
    print("You said: {}".format(voice_command["transcription"]))
    
    
    command = parse_command(voice_command["transcription"])
    
    if command:
        print(f"Sending command to Arduino: {command}")
        sendData(command)
    else:
        print("Invalid command.")