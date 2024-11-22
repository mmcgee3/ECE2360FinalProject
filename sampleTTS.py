import serial
import pyttsx3
import wave
import os
import time

arduino = serial.Serial(port='/dev/cu.usbserial-120', baudrate=9600, timeout=.1)
time.sleep(2)

def text_to_speech_to_wav(text, output_file):
    """Convert text to speech and save as a WAV file."""
    engine = pyttsx3.init()
    engine.save_to_file(text, output_file)
    engine.runAndWait()

def send_audio_to_arduino(wav_file, serial_port):
    """Send audio data from a WAV file to the Arduino."""
    with wave.open(wav_file, "rb") as wav_file:
        # Ensure the format matches
        assert wav_file.getsampwidth() == 2  # 16-bit
        assert wav_file.getframerate() == 44100  # 44.1 kHz
        assert wav_file.getnchannels() == 1  # Mono

        # Read and send audio data in chunks
        while True:
            data = wav_file.readframes(128)  # Read 128 frames at a time
            if not data:
                break  # End of file
            serial_port.write(data)  # Send data over serial
            time.sleep(128 / 44100)  # Maintain playback rate
        
while True:
    # Get user input
    user_input = input("Enter a command (or 'exit' to quit): ")
    if user_input.lower() == "exit":
        break

    # Convert text to speech and save as WAV
    wav_file = "command.wav"
    text_to_speech_to_wav(user_input, wav_file)

    # Send the generated audio to the Arduino
    send_audio_to_arduino(wav_file, arduino)

    # Clean up the generated WAV file
    os.remove(wav_file)
        
arduino.close()