
#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <math.h>

Adafruit_MCP4725 dac;

// Параметры генератора
const int SAMPLES = 64;
const float DAC_MAX = 4095.0;
const float REFERENCE_VOLTAGE = 5.0;

float frequency = 5.0;
float amplitude = 1.9;
float offsetVoltage = 2.5;

String waveform = "SINE";

bool generatorRunning = true;

int sampleIndex = 0;

unsigned long nextSampleTime = 0;
unsigned long sampleInterval = 2000;

String commandBuffer = "";


// =================================
// ПОЛУЧЕНИЕ ЗНАЧЕНИЯ ФОРМЫ СИГНАЛА
// =================================

float getWaveformValue(float phase) {

  if (waveform == "SINE") {
    return sin(2.0 * PI * phase);
  }

  if (waveform == "SQUARE") {
    return phase < 0.5 ? 1.0 : -1.0;
  }

  if (waveform == "TRIANGLE") {
    return 1.0 - 4.0 * fabs(phase - 0.5);
  }

  if (waveform == "SAWTOOTH") {
    return 2.0 * phase - 1.0;
  }

  return sin(2.0 * PI * phase);
}


// =================================
// ОБНОВЛЕНИЕ ПАРАМЕТРОВ
// =================================

void updateSampleInterval() {

  sampleInterval = (unsigned long)(
    1000000.0 / (frequency * SAMPLES)
  );

  if (sampleInterval < 2000) {
    sampleInterval = 2000;
  }
}


// =================================
// ОБРАБОТКА КОМАНД PYTHON
// =================================

void processCommand(String command) {

  command.trim();

  if (command == "RUN,1") {

    generatorRunning = true;
    sampleIndex = 0;
    nextSampleTime = micros();

    Serial.println("GENERATION_STARTED");
    return;
  }

  if (command == "RUN,0") {

    generatorRunning = false;

    dac.setVoltage(0, false);

    Serial.println("GENERATION_STOPPED");
    return;
  }

  if (command.startsWith("SET,")) {

    int firstComma = command.indexOf(',');
    int secondComma = command.indexOf(',', firstComma + 1);
    int thirdComma = command.indexOf(',', secondComma + 1);

    if (secondComma < 0 || thirdComma < 0) {
      Serial.println("ERROR,INVALID_COMMAND");
      return;
    }

    String newWaveform = command.substring(
      firstComma + 1,
      secondComma
    );

    float newFrequency = command.substring(
      secondComma + 1,
      thirdComma
    ).toFloat();

    float newAmplitude = command.substring(
      thirdComma + 1
    ).toFloat();

    if (
      newWaveform != "SINE" &&
      newWaveform != "SQUARE" &&
      newWaveform != "TRIANGLE" &&
      newWaveform != "SAWTOOTH"
    ) {
      Serial.println("ERROR,INVALID_WAVEFORM");
      return;
    }

    if (newFrequency < 0.5 || newFrequency > 7.0) {
      Serial.println("ERROR,FREQUENCY_RANGE");
      return;
    }

    if (newAmplitude < 0.1 || newAmplitude > 2.4) {
      Serial.println("ERROR,AMPLITUDE_RANGE");
      return;
    }

    waveform = newWaveform;
    frequency = newFrequency;
    amplitude = newAmplitude;

    updateSampleInterval();

    sampleIndex = 0;
    nextSampleTime = micros();

    Serial.println("SET_OK");
    return;
  }

  Serial.println("ERROR,UNKNOWN_COMMAND");
}


// =================================
// ЧТЕНИЕ КОМАНД ИЗ SERIAL
// =================================

void readSerialCommands() {

  while (Serial.available() > 0) {

    char incoming = Serial.read();

    if (incoming == '\n') {

      processCommand(commandBuffer);
      commandBuffer = "";

    } else if (incoming != '\r') {

      if (commandBuffer.length() < 80) {
        commandBuffer += incoming;
      } else {
        commandBuffer = "";
      }
    }
  }
}


// =================================
// ГЕНЕРАЦИЯ ОДНОГО ОТСЧЁТА
// =================================

void generateSample() {

  float phase = (float)sampleIndex / SAMPLES;

  float signalValue = getWaveformValue(phase);

  float outputVoltage =
    offsetVoltage + amplitude * signalValue;

  outputVoltage = constrain(
    outputVoltage,
    0.0,
    REFERENCE_VOLTAGE
  );

  int dacValue = (int)(
    outputVoltage / REFERENCE_VOLTAGE * DAC_MAX
  );

  dac.setVoltage(dacValue, false);

  int adcValue = analogRead(A0);

  unsigned long timeStamp = micros();

  Serial.print(timeStamp);
  Serial.print(",");
  Serial.println(adcValue);

  sampleIndex++;

  if (sampleIndex >= SAMPLES) {
    sampleIndex = 0;
  }
}


// =================================
// SETUP
// =================================

void setup() {

  Serial.begin(115200);

  Wire.begin();

  if (!dac.begin(0x60)) {

    Serial.println("ERROR,MCP4725_NOT_FOUND");

    while (1) {
      delay(100);
    }
  }

  updateSampleInterval();

  nextSampleTime = micros();

  Serial.println("SIGNAL_DOCTOR_READY");
  Serial.println("GENERATOR_READY");
}


// =================================
// LOOP
// =================================

void loop() {

  readSerialCommands();

  if (!generatorRunning) {
    return;
  }

  unsigned long currentTime = micros();

  if ((long)(currentTime - nextSampleTime) >= 0) {

    generateSample();

    nextSampleTime += sampleInterval;
  }
}
