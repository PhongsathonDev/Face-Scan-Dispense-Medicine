#include <WiFi.h>
#include <HTTPClient.h>

// -----------------------------
// ⚙️ ตั้งค่า Wi-Fi
// -----------------------------
const char* ssid = "testbuy";
const char* password = "123456780";

// -----------------------------
// 💬 ตั้งค่า LINE Messaging API
// -----------------------------
String lineToken = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU=";
String userId = "Uaa30a62f505cfb7a3e546ed644e4755f";

// -----------------------------
// ⏰ ตั้งเวลาการแจ้งเตือน (มิลลิวินาที)
// -----------------------------
unsigned long lastNotifyTime = 0;
const unsigned long notifyInterval = 10 * 1000; // ✅ แจ้งเตือนทุก 10 วินาที

// -----------------------------
// ฟังก์ชันส่งข้อความไป LINE
// -----------------------------
void sendLineMessage(String message) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("https://api.line.me/v2/bot/message/push");
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer " + lineToken);

    String payload = "{\"to\"😕"" + userId + "\",\"messages\":[{\"type\"😕"text\",\"text\"😕"" + message + "\"}]}";
    int httpResponseCode = http.POST(payload);

    Serial.print("📡 ส่งข้อความไป LINE: ");
    Serial.println(httpResponseCode);
    http.end();
  } else {
    Serial.println("⚠️ ยังไม่เชื่อมต่อ WiFi");
  }
}

// -----------------------------
// เริ่มต้นระบบ
// -----------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("🚀 กำลังเชื่อมต่อ WiFi...");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ เชื่อมต่อ WiFi สำเร็จ!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  sendLineMessage("🔔 ระบบแจ้งเตือนเริ่มทำงานแล้ว!");
}

// -----------------------------
// ลูปหลัก: แจ้ง LINE ทุก 10 วินาที
// -----------------------------
void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastNotifyTime >= notifyInterval) {
    lastNotifyTime = currentMillis;

    sendLineMessage("⏰ แจ้งเตือนอัตโนมัติจาก ESP32 ทุก 10 วินาที!");
    Serial.println("✅ ส่งแจ้งเตือน LINE แล้ว");
  }

  delay(1000);
}
api.line.me