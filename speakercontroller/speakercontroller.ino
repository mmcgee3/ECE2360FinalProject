#include "BluetoothA2DPSink.h"
#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Bluetooth A2DP Setup
BluetoothA2DPSink a2dp_sink;

// NeoPixel LED Strip Setup
#define LED_PIN 14
#define NUM_LEDS 8
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// LCD Setup
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Serial Input Setup
const byte numChars = 64;
char receivedChars[numChars];
boolean newData = false;

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

  lcd.init();
  lcd.backlight();

  Serial.begin(9600);
  strip.begin();
  strip.show();
}

void loop() {
  receiveInput();
  if (newData) {
    processInput();
    newData = false;
  }
  delay(50);
}

void receiveInput() {
  static boolean receivingInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && !newData) {
    rc = Serial.read();

    if (receivingInProgress) {
      if (rc != endMarker) {
        if (ndx < numChars - 1) {
          receivedChars[ndx++] = rc;
        }
      } else {
        receivedChars[ndx] = '\0'; // Null-terminate the string
        receivingInProgress = false;
        ndx = 0;
        newData = true;
        Serial.println("Data Received: "); // Debugging
        Serial.println(receivedChars);    // Debugging
      }
    } else if (rc == startMarker) {
      receivingInProgress = true;
      ndx = 0; // Reset index
    }
  }
}

void processInput() {
  String input = String(receivedChars);

  // Validate the format before parsing
  int firstComma = input.indexOf(',');
  int secondComma = input.indexOf(',', firstComma + 1);
  int thirdComma = input.indexOf(',', secondComma + 1);
  int fourthComma = input.indexOf(',', thirdComma + 1);

  if (firstComma == -1 || secondComma == -1 || thirdComma == -1 || fourthComma == -1) {
    Serial.println("Error: Invalid input format");
    return;
  }

  String message = input.substring(0, firstComma);
  String state = input.substring(firstComma + 1, secondComma);
  state.trim(); // Trim spaces from the 'state' variable
  int r = input.substring(secondComma + 1, thirdComma).toInt();
  int g = input.substring(thirdComma + 1, fourthComma).toInt();
  int b = input.substring(fourthComma + 1).toInt();

  Serial.print("Message: ");
  Serial.println(message);
  Serial.print("State: ");
  Serial.println(state);
  Serial.print("RGB: ");
  Serial.print(r); Serial.print(", ");
  Serial.print(g); Serial.print(", ");
  Serial.println(b);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(message);

  controlLED(state, r, g, b);
}


void controlLED(String state, int r, int g, int b) {
  if (state == "on") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
  } else if (state == "off") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, 0, 0, 0);
    }
    strip.show();
  } else if (state == "wake") {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
      strip.show();
      delay(75);
    }
  } else {
    Serial.println("Unknown state command");
  }
}
