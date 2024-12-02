#include <Adafruit_NeoPixel.h> // Include the Adafruit NeoPixel library

#define LED_PIN 14 // NeoPixel LED strip pin
#define NUM_LEDS 8 // Number of LEDs

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;

void setup() {
  Serial.begin(9600); // Initialize the serial channel
  strip.begin(); // Initialize the NeoPixel strip
  strip.show(); // Set initial color to black (off)
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
    }
    strip.show(); // Update the LED strip
  } else if (state == "wake") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, r, g, b); // Set each LED to the specified color
      strip.show(); // Update the LED strip
      delay(50);
    }
  }
}
