import face_recognition
import cv2
import numpy as np
import time
import requests
import serial

class FaceVerifier:
    def __init__(
        self,
        known_image_path: str,
        known_name: str = "User",
        tolerance: float = 0.45,
        hold_seconds: float = 3.0,
        camera_index: int = 0,
        webapp_url: str | None = None,
        sheet_name: str = "sheet1",
        face_id: str = "user_001",
        serial_port: str | None = "/dev/ttyUSB0",
        serial_baudrate: int = 115200
    ):
        self.known_image_path = known_image_path
        self.known_name = known_name
        self.tolerance = tolerance
        self.hold_seconds = hold_seconds
        self.camera_index = camera_index

        self.webapp_url = webapp_url
        self.sheet_name = sheet_name
        self.face_id = face_id

        # ====== Serial ไปยัง ESP32 ======
        self.serial_port = serial_port
        self.serial_baudrate = serial_baudrate
        self.ser = None

        if self.serial_port is not None:
            try:
                self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1)
                time.sleep(2)
                print(f"✅ เปิดพอร์ต Serial ไป ESP32 ที่ {self.serial_port} เรียบร้อย")
            except Exception as e:
                print("❌ เปิดพอร์ต Serial ไป ESP32 ไม่สำเร็จ:", e)
                self.ser = None

        # โหลดและเตรียมข้อมูลใบหน้าต้นแบบ
        self.known_face_encodings, self.known_face_names = self._load_known_faces()

        # state เวลาการมองค้าง
        self.hold_start_time = None
        self.verified = False

        self.video_capture = None

    # ---------- ส่วนส่งไป Google Sheet ----------
    def send_log_to_sheet(self, note: str = "Face verified") -> bool:
        if not self.webapp_url:
            print("⚠️ ยังไม่ได้ตั้งค่า WEBAPP_URL ข้ามการส่ง Google Sheet")
            return False

        payload = {
            "sheet": self.sheet_name,
            "data": {
                "Date": "",
                "Time": "",
                "Name": self.known_name,
                "FaceID": self.face_id,
                "Status": "Verified",
                "Note": note
            }
        }

        try:
            response = requests.post(self.webapp_url, json=payload, timeout=10)
            print("Google Sheet Status:", response.status_code)
            return response.status_code == 200
        except Exception as e:
            print("❌ ส่งข้อมูลไป Google Sheet ไม่สำเร็จ:", e)
            return False

    # ---------- ส่วนคุยกับ ESP32 ----------
    def send_command_to_esp32(self, cmd: str = "f"):
        if self.ser is None:
            return
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
            print(f"➡️ ส่งคำสั่ง '{cmd}' ไป ESP32 แล้ว")
        except Exception as e:
            print("❌ ส่งคำสั่งไป ESP32 ไม่สำเร็จ:", e)

    # ---------- ส่วน Face Recognition Core ----------
    def _load_known_faces(self):
        try:
            image = face_recognition.load_image_file(self.known_image_path)
            encoding = face_recognition.face_encodings(image)[0]
            return [encoding], [self.known_name]
        except Exception as e:
            print(f"❌ Error loading known face: {e}")
            return [], []

    def open_camera(self):
        self.video_capture = cv2.VideoCapture(self.camera_index)
        # ตั้งค่าความละเอียดกล้อง (ถ้ากล้องรองรับ)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        if not self.video_capture.isOpened():
            raise RuntimeError("ไม่สามารถเปิดกล้องได้")

    def close_camera(self):
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    def _process_frame(self, frame):
        """ประมวลผลใบหน้าและคืนค่าตำแหน่ง+ชื่อ (ไม่วาดรูปที่นี่)"""
        # ย่อภาพเพื่อให้เร็วขึ้น
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        recognized_this_frame = False

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=self.tolerance
            )
            name = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < self.tolerance:
                    name = self.known_face_names[best_match_index]
                    recognized_this_frame = True

            face_names.append(name)

        return face_locations, face_names, recognized_this_frame

    # ---------- ส่วน UI แบบ Minimal ----------
    def _draw_minimal_ui(self, frame, face_locations, face_names):
        height, width, _ = frame.shape
        
        # Palette (โทนสีเรียบง่าย)
        # ขาวสะอาด
        COLOR_WHITE = (255, 255, 255)
        # เขียวพาสเทล (Soft Green)
        COLOR_SUCCESS = (144, 238, 144)
        # แดงอ่อน (Soft Red) 
        COLOR_ERROR = (128, 128, 255)
        # เทาจางๆ
        COLOR_GRAY = (200, 200, 200)

        # 1. แสดงสถานะกลางหน้าจอแบบเรียบๆ
        if self.verified:
            # วงกลมเขียวตรงกลาง + ติ๊กถูก (จำลองด้วย Text)
            center_x, center_y = width // 2, height // 2
            cv2.circle(frame, (center_x, center_y), 60, COLOR_SUCCESS, -1)
            cv2.putText(frame, "OK", (center_x - 35, center_y + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            
            # ข้อความด้านล่าง
            msg = f"Welcome, {self.known_name}"
            text_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            cv2.putText(frame, msg, ((width - text_size[0]) // 2, center_y + 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_WHITE, 2)
            
        else:
            # 2. Loop วาดกรอบใบหน้า
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale กลับมาขนาดจริง
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # เลือกสี
                color = COLOR_WHITE
                if name == "Unknown":
                    color = COLOR_ERROR

                # A. กรอบสี่เหลี่ยมเส้นบาง (Thin Rectangle)
                # ใช้ความหนาแค่ 1 หรือ 2 pixel
                cv2.rectangle(frame, (left, top), (right, bottom), color, 1)

                # B. ชื่อคน (แสดงเฉพาะเมื่อไม่รู้จัก หรือรู้จักแล้ว)
                # วางไว้เหนือกรอบนิดหน่อย ตัวอักษรเล็กๆ แบบ Minimal
                font_scale = 0.6
                cv2.putText(frame, name.upper(), (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1)

                # C. Progress Bar แบบเส้น (Line Progress)
                # แสดงเป็นเส้นตรงเล็กๆ ใต้กรอบหน้า
                if self.hold_start_time is not None and name != "Unknown":
                    elapsed = time.time() - self.hold_start_time
                    progress = min(elapsed / self.hold_seconds, 1.0)
                    
                    # ความกว้างของเส้น Bar ตามความกว้างหน้า
                    bar_width = right - left
                    fill_width = int(bar_width * progress)
                    
                    # วาดพื้นหลังเส้น (สีเทาจาง)
                    bar_y = bottom + 15
                    cv2.line(frame, (left, bar_y), (right, bar_y), COLOR_GRAY, 2)
                    
                    # วาดเส้น Progress (สีขาวหรือเขียว)
                    if fill_width > 0:
                        cv2.line(frame, (left, bar_y), (left + fill_width, bar_y), COLOR_SUCCESS, 2)

    def _update_hold_state(self, recognized_this_frame: bool):
        """Logic จับเวลา"""
        if recognized_this_frame:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            else:
                elapsed = time.time() - self.hold_start_time
                if elapsed >= self.hold_seconds and not self.verified:
                    self.verified = True
                    print("✅ สแกนใบหน้าผ่านแล้ว")
                    ok = self.send_log_to_sheet(note="Face verified from camera")
                    if ok:
                        self.send_command_to_esp32("f")
        else:
            self.hold_start_time = None

    def run(self):
        self.hold_start_time = None
        self.verified = False

        self.open_camera()
        print("📷 เริ่มระบบสแกนใบหน้า (Minimal Mode)...")

        # Setup Fullscreen Window
        window_name = 'Tuberbox Minimal'
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        try:
            while True:
                ret, frame = self.video_capture.read()
                if not ret:
                    break

                # 1. Process Logic
                face_locations, face_names, recognized = self._process_frame(frame)
                
                # 2. Logic Hold Time
                self._update_hold_state(recognized)
                
                # 3. Draw Minimal UI
                self._draw_minimal_ui(frame, face_locations, face_names)

                cv2.imshow(window_name, frame)

                if self.verified:
                    cv2.waitKey(2000) # แสดงผลสำเร็จค้างไว้ 2 วินาที
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            self.close_camera()
            print("ปิดโปรแกรมเรียบร้อย")

        return self.verified

if __name__ == "__main__":
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"

    verifier = FaceVerifier(
        known_image_path="paper.jpeg",
        known_name="Paper",
        tolerance=0.5,
        hold_seconds=2.0,
        camera_index=0,
        webapp_url=WEBAPP_URL,
        sheet_name="Patient",
        face_id="Paper",
        serial_port="/dev/ttyUSB0", 
        serial_baudrate=115200
    )
    verifier.run()