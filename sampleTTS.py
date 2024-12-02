import asyncio
from bleak import BleakClient, BleakScanner
from gtts import gTTS
from pydub import AudioSegment
import os

SERVICE_UUID = "8785d8b3-9d23-473b-aee5-3fabe2ba9583"
CHARACTERISTIC_UUID_RX = "b2bcd13b-aab6-4660-92ae-40abf6941fce"

async def find_and_connect(target_name):
    """Find and connect to the Bluetooth device by name."""
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and target_name in device.name:  # Check if device.name is not None
            print(f"Found target device: {device.name} ({device.address})")
            return device.address
    print("Target device not found.")
    return None

async def send_text_as_audio(address):
    """Send user-input text converted to speech to the ESP32."""
    async with BleakClient(address) as client:
        print("Connected to the ESP32")
        user_input = input("Enter text to convert to speech: ")
        
        # Convert text to speech and save as an audio file (MP3)
        tts = gTTS(text=user_input, lang="en")
        mp3_file_path = "output.mp3"
        tts.save(mp3_file_path)
        print(f"Audio saved to {mp3_file_path}")
        
        # Convert the MP3 file to WAV using pydub
        wav_file_path = "output.wav"
        audio = AudioSegment.from_mp3(mp3_file_path)
        audio.export(wav_file_path, format="wav")
        print(f"Audio converted to WAV and saved to {wav_file_path}")
        
        # Play the audio locally (using default player)
        os.system(f"afplay {wav_file_path}" if os.name == "posix" else f"start {wav_file_path}")
        
        # Send the WAV audio data to ESP32 via BLE
        with open(wav_file_path, "rb") as audio_file:
            data = audio_file.read(512)
            while data:
                await client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
                data = audio_file.read(512)
        
        print("Audio sent to ESP32.")
        os.remove(mp3_file_path)
        os.remove(wav_file_path)

if __name__ == "__main__":
    target_name = "ESP32_Bluetooth"
    address = asyncio.run(find_and_connect(target_name))
    if address:
        asyncio.run(send_text_as_audio(address))
    else:
        print("ESP32 not found. Ensure it is powered on and in range.")
