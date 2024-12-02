#include "BluetoothA2DPSink.h" // Include Bluetooth A2DP library
#include <Adafruit_NeoPixel.h> // Include the Adafruit NeoPixel library

// Bluetooth A2DP Setup
BluetoothA2DPSink a2dp_sink;

// NeoPixel LED Strip Setup
#define LED_PIN 14 // NeoPixel LED strip pin
#define NUM_LEDS 8 // Number of LEDs
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Serial Input Setup
const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;

void setup() {
  // Bluetooth A2DP setup
  const i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_DAC_BUILT_IN),
    .sample_rate = 44100,                          // corrected by info from Bluetooth
    .bits_per_sample = (i2s_bits_per_sample_t)16,  // the DAC module will only take the 8 bits from MSB
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = (i2s_comm_format_t)I2S_COMM_FORMAT_STAND_MSB,
    .intr_alloc_flags = 0,  // default interrupt priority
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false
  };
  a2dp_sink.set_i2s_config(i2s_config);
  a2dp_sink.start("ESP32_Bluetooth");

  // Serial and NeoPixel setup
  Serial.begin(9600); // Initialize the serial channel
  strip.begin();      // Initialize the NeoPixel strip
  strip.show();       // Set initial color to black (off)
}

void loop() {
  receiveInput(); // Check for new serial input
  if (newData) {
    processInput();
    newData = false;
  }
}

// Reads in data surrounded by <> and ignores other serial data
void receiveInput() {
  static boolean receivingInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (receivingInProgress) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) ndx = numChars - 1;
      } else {
        receivedChars[ndx] = '\0'; // Null-terminate the string
        receivingInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == startMarker) {
      receivingInProgress = true;
    }
  }
}

// Process the received input and control the LED strip
void processInput() {
  String input = String(receivedChars);
  int firstComma = input.indexOf(',');
  int secondComma = input.indexOf(',', firstComma + 1);
  int thirdComma = input.indexOf(',', secondComma + 1);

  // Extract state and RGB values
  String state = input.substring(0, firstComma);
  int r = input.substring(firstComma + 1, secondComma).toInt();
  int g = input.substring(secondComma + 1, thirdComma).toInt();
  int b = input.substring(thirdComma + 1).toInt();

  controlLED(state, r, g, b); // Control LED based on state and RGB values
}

// Control the LED strip based on the parsed command and color values
void controlLED(String state, int r, int g, int b) {
  if (state == "on") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, r, g, b); // Set each LED to the specified color
    }
    strip.show(); // Update the LED strip
  } else if (state == "off") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, 0, 0, 0); // Turn off each LED
      delay(75);
      strip.show(); // Update the LED strip
    }
  } else if (state == "wake") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, r, g, b); // Set each LED to the specified color
      strip.show(); // Update the LED strip
      delay(75);
    }
  }
}
