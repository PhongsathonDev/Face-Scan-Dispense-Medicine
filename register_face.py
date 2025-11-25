import cv2
import face_recognition
import mediapipe as mp
import time
import os
import re
import requests  # ✅ เพิ่ม import requests
import config    # ✅ เพิ่ม import config เพื่อเอา WEBAPP_URL

# ✅ ตัวแปร Global เก็บเลขที่มีให้เลือก (Default เป็น 1-9 เผื่อเน็ตหลุด)
available_patient_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]

# ✅ ฟังก์ชันดึงรายการ Sheet จาก Google Apps Script
def fetch_available_patients():
    global available_patient_ids
    print("📡 กำลังเช็คข้อมูล Patient จาก Google Sheet...")
    try:
        # ยิง Request ไปถาม GAS
        url = f"{config.WEBAPP_URL}?action=getSheets"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json() # คาดหวัง list เช่น [1, 2, 3]
            if isinstance(data, list):
                available_patient_ids = data
                print(f"✅ พบข้อมูลผู้ป่วย: Patient {available_patient_ids}")
            else:
                print("⚠️ รูปแบบข้อมูลไม่ถูกต้อง ใช้ค่าเริ่มต้น 1-9")
        else:
            print(f"⚠️ เชื่อมต่อไม่ได้ (Status {response.status_code}) ใช้ค่าเริ่มต้น 1-9")
            
    except Exception as e:
        print(f"❌ เช็คข้อมูลไม่สำเร็จ (Offline mode): {e}")
        # ถ้า error ให้ปล่อยเป็นค่าเดิม หรือจะกำหนดเป็น [] ก็ได้ตามต้องการ

# ฟังก์ชันสำหรับอัปเดตไฟล์ config.py (เหมือนเดิม)
def update_config(sheet_number):
    config_path = "config.py"
    new_sheet_name = f"Patient{sheet_number}"
    new_known_name = f"Patient{sheet_number}"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        with open(config_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip().startswith("SHEET_NAME ="):
                    f.write(f'SHEET_NAME = "{new_sheet_name}"      # อัปเดตอัตโนมัติ\n')
                elif line.strip().startswith("KNOWN_NAME ="):
                    f.write(f'KNOWN_NAME = "{new_known_name}"      # อัปเดตอัตโนมัติ\n')
                else:
                    f.write(line)
        print(f"✅ อัปเดต config.py เรียบร้อย: Sheet -> {new_sheet_name}")
        return new_sheet_name
    except Exception as e:
        print(f"❌ ไม่สามารถแก้ไข config.py: {e}")
        return None

# ตัวแปร Global สำหรับเก็บค่าจาก Mouse Callback
selected_number = None

def mouse_callback(event, x, y, flags, param):
    global selected_number, available_patient_ids
    if event == cv2.EVENT_LBUTTONDOWN:
        start_x, start_y = 440, 200
        btn_size, gap = 100, 20
        
        count = 1
        for row in range(3):
            for col in range(3):
                bx = start_x + (col * (btn_size + gap))
                by = start_y + (row * (btn_size + gap))
                
                if bx < x < bx + btn_size and by < y < by + btn_size:
                    # ✅ เช็คก่อนว่าเลขนี้มีใน Sheet หรือไม่
                    if count in available_patient_ids:
                        selected_number = count
                    else:
                        print(f"🚫 Patient{count} ไม่มีในระบบ")
                    return
                count += 1

def draw_numpad(frame):
    global available_patient_ids
    height, width, _ = frame.shape
    overlay = frame.copy()
    
    cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    cv2.putText(frame, "Select Patient ID", (width//2 - 200, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    start_x, start_y = 440, 200
    btn_size, gap = 100, 20
    
    count = 1
    for row in range(3):
        for col in range(3):
            bx = start_x + (col * (btn_size + gap))
            by = start_y + (row * (btn_size + gap))
            
            # ✅ ปรับสี: ถ้ามีเลขใน Sheet ให้เป็นสีเขียว, ถ้าไม่มีให้เป็นสีเทา
            if count in available_patient_ids:
                color = (161, 214, 162) # เขียว (Active)
                text_color = (255, 255, 255)
                thickness = -1 # ถมเต็ม
            else:
                color = (100, 100, 100) # เทา (Inactive)
                text_color = (180, 180, 180)
                thickness = 2 # แค่ขอบ
            
            # วาดปุ่ม
            if thickness == -1:
                cv2.rectangle(frame, (bx, by), (bx + btn_size, by + btn_size), color, -1)
            
            cv2.rectangle(frame, (bx, by), (bx + btn_size, by + btn_size), color, 2)
            
            # ตัวเลข
            text_size = cv2.getTextSize(str(count), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            tx = bx + (btn_size - text_size[0]) // 2
            ty = by + (btn_size + text_size[1]) // 2
            cv2.putText(frame, str(count), (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.5, text_color, 3)
            
            count += 1
            
    cv2.putText(frame, "Green = Available, Gray = Not Found", (width//2 - 280, 600), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

def register_new_face(filename="patient.jpeg"):
    # ✅ เรียกดึงข้อมูล Patient ก่อนเริ่ม loop (ทำงานครั้งเดียวตอนเข้าฟังก์ชัน)
    fetch_available_patients()
    
    # --- ตั้งค่า MediaPipe ---
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # --- ตัวแปรระบบ ---
    is_counting_down = False 
    start_time = 0
    countdown_duration = 3.0 
    hand_hold_start_time = 0  
    REQUIRED_HOLD_TIME = 1.5  

    cap = cv2.VideoCapture(0)
    # ใช้ค่าจาก config ถ้ามี หรือ hardcode ตามเดิม
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    window_name = "Register New Face"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    cv2.setMouseCallback(window_name, mouse_callback)

    print("--------------------------------------------------")
    print("📷 ระบบถ่ายภาพอัตโนมัติ (Auto Selfie)")
    print("--------------------------------------------------")

    face_saved = False 

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        
        # PHASE 1: ถ่ายรูป
        if not face_saved:
            display_frame = frame.copy()
            height, width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if not is_counting_down:
                results = hands.process(rgb_frame)
                hand_detected_5_fingers = False
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        lm_list = hand_landmarks.landmark
                        fingers_up = []
                        tips_ids = [8, 12, 16, 20]
                        pip_ids = [6, 10, 14, 18]
                        for tip, pip in zip(tips_ids, pip_ids):
                            if lm_list[tip].y < lm_list[pip].y: fingers_up.append(True)
                            else: fingers_up.append(False)
                        if fingers_up.count(True) == 4: hand_detected_5_fingers = True

                if hand_detected_5_fingers:
                    if hand_hold_start_time == 0: hand_hold_start_time = time.time()
                    hold_elapsed = time.time() - hand_hold_start_time
                    progress = min(hold_elapsed / REQUIRED_HOLD_TIME, 1.0)
                    bar_width = int(400 * progress)
                    cv2.rectangle(display_frame, (width//2 - 200, 100), (width//2 - 200 + bar_width, 130), (0, 255, 0), -1)
                    cv2.rectangle(display_frame, (width//2 - 200, 100), (width//2 + 200, 130), (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Hold: {hold_elapsed:.1f}s", (width//2 - 60, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    if hold_elapsed >= REQUIRED_HOLD_TIME:
                        is_counting_down = True
                        start_time = time.time()
                        hand_hold_start_time = 0
                else:
                    hand_hold_start_time = 0
                    cv2.putText(display_frame, "Show 5 Fingers & Hold", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            else:
                elapsed_time = time.time() - start_time
                time_left = countdown_duration - elapsed_time
                if time_left > 0:
                    seconds_display = int(time_left) + 1
                    text_size = cv2.getTextSize(str(seconds_display), cv2.FONT_HERSHEY_SIMPLEX, 10, 20)[0]
                    cv2.putText(display_frame, str(seconds_display), ((width - text_size[0]) // 2, (height + text_size[1]) // 2), cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 255), 20)
                else:
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if len(face_locations) > 0:
                        cv2.imwrite(filename, frame)
                        print(f"✅ บันทึกรูปภาพเรียบร้อย: {filename}")
                        cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), -1)
                        cv2.imshow(window_name, display_frame)
                        cv2.waitKey(100)
                        face_saved = True 
                    else:
                        print("⚠️ ไม่พบใบหน้า! ลองใหม่อีกครั้ง")
                        is_counting_down = False
            
            if not face_saved:
                box_size = 400
                x1, y1 = (width - box_size) // 2, (height - box_size) // 2
                cv2.rectangle(display_frame, (x1, y1), (x1 + box_size, y1 + box_size), (161, 214, 162), 2)
                cv2.imshow(window_name, display_frame)

        # PHASE 2: เลือก Sheet Name (Numpad)
        else:
            global selected_number
            draw_numpad(frame)
            cv2.imshow(window_name, frame)
            
            if selected_number is not None:
                print(f"🔢 Selected Number: {selected_number}")
                cv2.putText(frame, f"Saving to Patient{selected_number}...", (200, 360), 
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                cv2.imshow(window_name, frame)
                cv2.waitKey(500)
                update_config(selected_number)
                cv2.waitKey(1000)
                break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    selected_number = None

if __name__ == "__main__":
    register_new_face()