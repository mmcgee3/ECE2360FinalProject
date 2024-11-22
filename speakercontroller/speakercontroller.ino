#include <driver/dac.h>
#include <driver/i2s.h>

#define SAMPLE_RATE 44100

void setup() {
  Serial.begin(115200);  // Start serial communication for receiving audio data

  // Configure I2S for DAC output
  const i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_DAC_BUILT_IN),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S_MSB,
    .intr_alloc_flags = 0,  // Default interrupt priority
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false
  };

  // Configure I2S pins (not needed for DAC output)
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_PIN_NO_CHANGE,
    .ws_io_num = I2S_PIN_NO_CHANGE,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  // Initialize I2S
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_set_dac_mode(I2S_DAC_CHANNEL_BOTH_EN);
}

void loop() {
  // Check if there's data available on the serial port
  if (Serial.available()) {
    uint8_t buffer[128];  // Buffer to store audio data
    size_t bytes_read = Serial.readBytes(buffer, sizeof(buffer));

    // Write the audio data to the DAC
    size_t bytes_written;
    i2s_write(I2S_NUM_0, buffer, bytes_read, &bytes_written, portMAX_DELAY);
  }
}
