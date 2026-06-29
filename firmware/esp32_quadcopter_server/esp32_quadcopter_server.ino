/*
 * ESP32 Quadcopter Control Server
 *
 * Companion firmware for the iOS Quadcopter Control app.
 * Exposes a simple HTTP JSON API over Wi-Fi.
 *
 * Required libraries (Arduino IDE / PlatformIO):
 *   - WiFi (built-in)
 *   - WebServer (built-in)
 *   - ArduinoJson (v6+)
 *
 * Connect your iPhone to the ESP32 access point, then open the iOS app.
 * Default ESP32 AP IP: 192.168.4.1
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

const char* AP_SSID = "Quadcopter-ESP32";
const char* AP_PASSWORD = "12345678";

WebServer server(80);

bool armed = false;
bool flying = false;
float posX = 0.0f;
float posY = 0.0f;
float posZ = 0.0f;
int batteryPercent = 100;
String flightMode = "idle";

void sendJSON(int code, const String& body) {
  server.send(code, "application/json", body);
}

void handleStatus() {
  StaticJsonDocument<256> doc;
  doc["armed"] = armed;
  doc["flying"] = flying;
  doc["x"] = posX;
  doc["y"] = posY;
  doc["z"] = posZ;
  doc["battery"] = batteryPercent;
  doc["mode"] = flightMode;
  doc["message"] = "ok";

  String response;
  serializeJson(doc, response);
  sendJSON(200, response);
}

void handleCommand() {
  if (!server.hasArg("plain")) {
    sendJSON(400, "{\"success\":false,\"message\":\"Missing JSON body\"}");
    return;
  }

  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, server.arg("plain"));
  if (error) {
    sendJSON(400, "{\"success\":false,\"message\":\"Invalid JSON\"}");
    return;
  }

  const char* action = doc["action"] | "";
  String message = "Command accepted";

  if (strcmp(action, "arm") == 0) {
    armed = true;
    flightMode = "armed";
  } else if (strcmp(action, "disarm") == 0) {
    armed = false;
    flying = false;
    flightMode = "idle";
  } else if (strcmp(action, "takeoff") == 0) {
    if (!armed) {
      sendJSON(400, "{\"success\":false,\"message\":\"Arm motors first\"}");
      return;
    }
    flying = true;
    flightMode = "flying";
    posZ = 1.5f;
  } else if (strcmp(action, "land") == 0) {
    flying = false;
    flightMode = "landing";
    posZ = 0.0f;
  } else if (strcmp(action, "hover") == 0) {
    flightMode = flying ? "flying" : "idle";
  } else if (strcmp(action, "goto") == 0) {
    posX = doc["x"] | posX;
    posY = doc["y"] | posY;
    posZ = doc["z"] | posZ;
    flying = true;
    flightMode = "flying";
    message = "Navigating to target coordinates";
    // TODO: feed posX/posY/posZ into your PID / flight controller
  } else if (strcmp(action, "mission") == 0) {
    JsonArray waypoints = doc["waypoints"];
    if (waypoints.isNull() || waypoints.size() == 0) {
      sendJSON(400, "{\"success\":false,\"message\":\"Mission requires waypoints\"}");
      return;
    }
    flightMode = "mission";
    flying = true;
    for (JsonObject wp : waypoints) {
      posX = wp["x"] | posX;
      posY = wp["y"] | posY;
      posZ = wp["z"] | posZ;
      float holdSeconds = wp["hold_seconds"] | 2.0f;
      // TODO: move to each waypoint using your autonomous controller
      delay((uint32_t)(holdSeconds * 1000));
    }
    message = "Mission complete";
  } else if (strcmp(action, "home") == 0) {
    posX = 0;
    posY = 0;
    posZ = flying ? 1.5f : 0.0f;
    message = "Returning home";
  } else if (strcmp(action, "emergency_stop") == 0) {
    armed = false;
    flying = false;
    flightMode = "idle";
    message = "Emergency stop executed";
    // TODO: cut motor outputs immediately
  } else {
    sendJSON(400, "{\"success\":false,\"message\":\"Unknown action\"}");
    return;
  }

  StaticJsonDocument<128> response;
  response["success"] = true;
  response["message"] = message;
  String body;
  serializeJson(response, body);
  sendJSON(200, body);
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  server.on("/status", HTTP_GET, handleStatus);
  server.on("/command", HTTP_POST, handleCommand);
  server.begin();

  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  server.handleClient();
  // TODO: read IMU/GPS, update posX/posY/posZ, run control loop
}
