# 💊 Tuberbox System: Face-Verified Automatic Drug Dispenser

**ระบบจ่ายยาอัตโนมัติด้วยการสแกนใบหน้าและติดตามผู้ป่วยวัณโรค (Face-Verified Automatic Drug Dispenser with Patient Monitoring)**

โครงการนี้คือระบบจ่ายยาอัจฉริยะที่ผสมผสานเทคโนโลยี **Computer Vision**, **IoT** และ **Web Technology** เข้าด้วยกัน เพื่อให้มั่นใจว่าผู้ป่วยได้รับยาอย่างถูกต้องและตรงเวลา โดยใช้ **Raspberry Pi** (หรือ PC) เป็นหน่วยประมวลผลหลัก ควบคุมการทำงานผ่านหน้าจอสัมผัส (Touchscreen GUI) และสั่งการฮาร์ดแวร์จ่ายยาผ่าน **ESP32** พร้อมระบบติดตามผลผ่าน Web Dashboard แบบ Real-time





[![วิดีโอตัวอย่างการทำงาน](https://img5.pic.in.th/file/secure-sv1/Portfolio--3.png)](https://drive.google.com/file/d/12Y-gntrWKoKE5B0EZOnevoNy0pt2GfrG/view?usp=drive_link)

คลิกภาพเพื่อดูวิดีโอตัวอย่างการทำงาน



---

## 🌟 ฟีเจอร์เด่น (Key Features)

### 1. 👤 ระบบยืนยันตัวตนและลงทะเบียนอัจฉริยะ
* **Face Verification:** ใช้เทคโนโลยี **Face Recognition** ตรวจจับและยืนยันใบหน้าผู้ใช้งาน
* **Liveness Check (Hold Time):** ผู้ใช้ต้องมองกล้องค้างไว้ตามเวลาที่กำหนด (เช่น 3 วินาที) เพื่อป้องกันการกดพลาดหรือใช้รูปถ่าย
* **Auto Selfie Registration (New!):** ระบบลงทะเบียนใบหน้าใหม่ด้วยการใช้ **MediaPipe Hand Tracking** (ชู 5 นิ้วเพื่อเริ่มนับถอยหลังถ่ายรูปอัตโนมัติ) ทำให้ผู้ป่วยลงทะเบียนได้ด้วยตนเองโดยไม่ต้องใช้คีย์บอร์ด

### 2. 🖥️ หน้าจอควบคุมและคู่มือ (Interactive GUI)
* **Full Screen Interface:** พัฒนาด้วย **Python (Tkinter)** ใช้งานง่ายผ่านหน้าจอสัมผัส
* **Dashboard:** แสดงจำนวนวันที่ทานยาต่อเนื่อง, วันที่/เวลาปัจจุบัน และเวลาที่ต้องทานยา
* **Manual Mode:** คู่มือการใช้งานในตัว รองรับ 2 ภาษา (ไทย/อังกฤษ)

### 3. ☁️ ระบบติดตามและแจ้งเตือน (IoT & Monitoring)
* **LINE Messaging API:** แจ้งเตือนข้อความไปยังผู้ป่วยหรือญาติเมื่อถึงเวลาทานยา (รองรับ Push Message)
* **Web Dashboard (New!):** หน้าเว็บสำหรับแพทย์/แอดมิน เพื่อดูสถานะผู้ป่วยทุกคน (กินยาแล้ว/ยังไม่กิน), ประวัติย้อนหลัง, และจัดการข้อมูลผู้ป่วย
* **Offline Mode Support (New!):** หากอินเทอร์เน็ตหลุด ระบบจะบันทึกข้อมูลการกินยาลงไฟล์ `offline_logs.json` และส่งขึ้น Google Sheets อัตโนมัติเมื่อต่อเน็ตได้

### 4. 🤖 ควบคุมฮาร์ดแวร์ (Hardware Control)
* **ESP32 Integration:** สื่อสารผ่าน Serial (UART) เพื่อควบคุมมอเตอร์และระบบเสียง
* **Motor Control:** ควบคุม DC Motor จ่ายยา พร้อมระบบตรวจสอบด้วย Limit Switch
* **Voice Feedback (New!):** มีระบบเสียงตอบโต้ (MP3) แจ้งเตือนสถานะการทำงานผ่านลำโพง

---

## 🛠️ อุปกรณ์ที่ต้องใช้ (Hardware Requirements)

1.  **Raspberry Pi 5** (หรือ PC ที่รัน Python ได้)
2.  **กล้อง USB Webcam**
3.  **หน้าจอสัมผัส (Touchscreen)**
4.  **ESP32 Development Board**
5.  **Motor Driver (L298N)**
6.  **DC Motor** (สำหรับกลไกจ่ายยา)
7.  **Limit Switch** (เซ็นเซอร์นับรอบถาดจ่ายยา)
8.  **MP3 Module** (Serial MP3 Player เช่น RedMP3) + ลำโพง

---

## 💻 ความต้องการซอฟต์แวร์ (Software Requirements)

* **Python 3.x**
* **Python Libraries:**
    ```bash
    pip install face_recognition opencv-python numpy requests pyserial Pillow mediapipe
    ```
* **Arduino IDE** (สำหรับอัปโหลดโค้ดลง ESP32)
* **Google Apps Script** (สำหรับระบบ Web Dashboard และ Database)

---

## 🚀 การติดตั้งและใช้งาน (Installation & Setup)

### 1. การเตรียม Hardware (ESP32)
1.  เปิดไฟล์ `esp.ino` ด้วย Arduino IDE
2.  ติดตั้งไลบรารีที่จำเป็น (เช่น `RedMP3.h`)
3.  เชื่อมต่อสาย:
    * **Motor Driver:** Pin 18 (PWM), 19 (IN1), 21 (IN2)
    * **Limit Switch:** Pin 14
    * **MP3 Module:** RX=15, TX=2
4.  Upload โค้ดลงบอร์ด ESP32

### 2. การตั้งค่าระบบ (Configuration) - **สำคัญ!**
แก้ไขไฟล์ `config.py` เพื่อตั้งค่าระบบให้ตรงกับการใช้งาน:

```python
# config.py

# LINE Messaging API
LINE_ACCESS_TOKEN = "ใส่_Token_ของคุณ"
LINE_USER_ID = "ใส่_UserID_ที่ต้องการแจ้งเตือน"

# Google Web App
WEBAPP_URL = "URL_จาก_Google_Apps_Script"

# Hardware
SERIAL_PORT = "/dev/ttyUSB0"  # หรือ COM3 บน Windows

```

### 3. การเตรียม Google Apps Script (Web Dashboard)

1.  นำไฟล์ในโฟลเดอร์ `GoogleAppScript/` ไปสร้างโปรเจกต์ใหม่ใน Google Apps Script
2.  Deploy เป็น Web App (ตั้งค่า Execute as: Me, Who has access: Anyone)
3.  นำ URL ที่ได้มาใส่ใน `config.py`

### 4\. การรันโปรแกรม

```bash
python Main.py
```

-----

## 📖 วิธีการใช้งาน (User Guide)

1.  **การลงทะเบียนผู้ป่วยใหม่:**

      * กดปุ่ม **"ลงทะเบียน"** ที่หน้าจอ
      * ยกมือชู 5 นิ้วค้างไว้ หน้าจอจะนับถอยหลังเพื่อถ่ายรูปใบหน้า
      * ใส่รหัสผู้ป่วยผ่าน Numpad บนหน้าจอ

2.  **การรับยาประจำวัน:**

      * เมื่อถึงเวลา ระบบจะแจ้งเตือนผ่าน LINE และมีเสียงเตือน
      * กดปุ่ม **"กดเพื่อรับยา"**
      * มองกล้องค้างไว้จนกว่าจะขึ้น **"VERIFIED"**
      * เครื่องจะจ่ายยาและบันทึกข้อมูลเข้าระบบออนไลน์ทันที

-----

## 📂 โครงสร้างไฟล์ (File Structure)

  * `Main.py`: โปรแกรมหลัก GUI และการเชื่อมต่อระบบ
  * `config.py`: ไฟล์ตั้งค่าระบบทั้งหมด (Token, URL, Serial Port)
  * `Facescan.py`: ระบบสแกนใบหน้า, จัดการ Offline Log, สื่อสาร ESP32
  * `register_face.py`: ระบบลงทะเบียนใบหน้าด้วยท่าทางมือ (MediaPipe)
  * `Manual.py`: ระบบแสดงคู่มือการใช้งาน
  * `esp.ino`: โค้ดควบคุมฮาร์ดแวร์ (ESP32)
  * `GoogleAppScript/`: โค้ดสำหรับทำ Web Dashboard และ API

-----
