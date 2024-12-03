#include "BluetoothA2DPSink.h" // Include Bluetooth A2DP library
#include <Adafruit_NeoPixel.h> // Include the Adafruit NeoPixel library
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Bluetooth A2DP Setup
BluetoothA2DPSink a2dp_sink;

// NeoPixel LED Strip Setup
#define LED_PIN 14 // NeoPixel LED strip pin
#define NUM_LEDS 8 // Number of LEDs
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// SDA->21, SCL->22
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Serial Input Setup
const byte numChars = 64;
char receivedChars[numChars];
boolean newData = false;

// set pin numbers
const int pirPin = 14;  // the number of the PIR pin
const int ledPin = 26;  // LED pin

// variable for storing the PIR status 
int pirState = 0;

void setup() {
  // Bluetooth A2DP setup
  const i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_DAC_BUILT_IN),
    .sample_rate = 44100,
    .bits_per_sample = (i2s_bits_per_sample_t)16,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = (i2s_comm_format_t)I2S_COMM_FORMAT_STAND_MSB,
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false
  };
  a2dp_sink.set_i2s_config(i2s_config);
  a2dp_sink.start("ESP32_Bluetooth");

  lcd.init();         // Initialize the LCD
  lcd.backlight();    // Turn on the LCD backlight

  // initialize the PIR pin as an input
  pinMode(pirPin, INPUT);
  // initialize the LED pin as an output
  pinMode(ledPin, OUTPUT);

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
  // read the state of the PIR value
  pirState = digitalRead(pirPin);

  // if the PIR is triggered, the pirState is HIGH
  if (pirState == HIGH) {
    // turn LED on
    digitalWrite(ledPin, HIGH);
    // send wake-up signal to Python
    Serial.println("WAKE");
    delay(2000); // Avoid spamming the wake signal
  } else {
    // turn LED off
    digitalWrite(ledPin, LOW);
  }
  delay(50);
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
  int fourthComma = input.indexOf(',', thirdComma + 1);

  // Extract message, state, and RGB values
  String message = input.substring(1, firstComma - 1);
  String state = input.substring(firstComma + 1, secondComma);
  int r = input.substring(secondComma + 1, thirdComma).toInt();
  int g = input.substring(thirdComma + 1, fourthComma).toInt();
  int b = input.substring(fourthComma + 1).toInt();

  // Display the message on the LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(message);

  // Control the LED strip based on the command
  controlLED(state, r, g, b);
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
