#include <SPI.h>
#include <Ethernet.h>
#include <ArduinoJson.h>

// Define network configuration
byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 50);
EthernetServer server(5000);
EthernetClient client;

// Define GPIO pins
const int pwm_frequency = 10000; // Frequency is specified in Hz
const int pwm_resolution = 8; // PWM bit resolution
const int pwm01 = 5;
const int pwm02 = 10;
const int pwm03 = 11;

// Define log_level
constant int log_level = 0; // 0: None, 1: Error, 2: Warning, 3: Info, 4: Debug/Verbose

void setup() {
  // Setup ethernet connection
  Serial.begin(115200);
  Ethernet.begin(mac, ip);
  server.begin();
  Serial.println("ESP32 Ethernet Server Started");

  // Setup PWM pins
  ledcAttach(pwm01, pwm_frequency, pwn_resolution);
  ledcAttach(pwm02, pwm_frequency, pwm_resolution);
  ledcAttach(pwm03, pwm_frequency, pwm_resolution);
  // Set initial pwm duty cycle to off (i.e. 0)
  ledcWrite(pwm01, 0);
  ledcWrite(pwm02, 0);
  ledcWrite(pwm03, 0);
}

void loop() {
  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  if (client.available() >= 4) {
    uint32_t length = readLength();
    String jsonString = readPayload(length);

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, jsonString);

    if (!error) {
      handleMessage(doc);
    }
  }
}

uint32_t readLength() {
  uint8_t header[4];
  client.read(header, 4);
  return (header[0] << 24) |
         (header[1] << 16) |
         (header[2] << 8)  |
         (header[3]);
}

String readPayload(uint32_t length) {
  String payload = "";
  while (payload.length() < length) {
    if (client.available()) {
      payload += (char)client.read();
    }
  }
  return payload;
}

void sendJson(JsonDocument& doc) {
  String output;
  serializeJson(doc, output);

  uint32_t length = output.length();
  uint8_t header[4] = {
    (length >> 24) & 0xFF,
    (length >> 16) & 0xFF,
    (length >> 8) & 0xFF,
    length & 0xFF
  };

  client.write(header, 4);
  client.print(output);
}

void handleMessage(JsonDocument& doc) {
  const char* type = doc["type"];

  if (strcmp(type, "ping") == 0) {
    StaticJsonDocument<128> reply;
    reply["type"] = "pong";
    sendJson(reply);
    return;
  }

  if (type == "set") {
    const char* cmd = doc["set"];

    StaticJsonDocument<128> reply;
    reply["status"] = "set: " + String(cmd) + " -> " + String(cmd["value"]);
    sendJson(reply);
  }
    if (type == "get") {
    const char* cmd = doc["get"];
  }

}

void setPWM(uint8_t, uint8_t dutyCycle) {
  if (pin == 1) {ledcWrite(pwm01, dutyCycle);}
  else if (pin == 2) {ledcWrite(pwm02, dutyCycle);}
  else if (pin == 3) {ledcWrite(pwm03, dutyCycle);}
}

void pwmOff() {
  ledcWrite(pwm01, 0);
  ledcWrite(pwm02, 0);
  ledcWrite(pwm03, 0);
}

void pwmtest() {
  for (int dutyCycle = 0; dutyCycle <= 255; dutyCycle+10) {
    setPWM(1, dutyCycle);
    setPWM(2, dutyCycle);
    setPWM(3, dutyCycle);
    delay(10);
  }
}