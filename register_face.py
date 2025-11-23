import cv2
import face_recognition
import mediapipe as mp
import time
import os

def register_new_face(filename="patient.jpeg"):
    # --- ตั้งค่า MediaPipe สำหรับตรวจจับมือ ---
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,            # ตรวจจับแค่มือเดียวก็พอ
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # --- ตัวแปรสำหรับตัวจับเวลา (Timer) ---
    gesture_start_time = 0
    capture_delay = 3.0  # ต้องถือค้างไว้ 3 วินาที
    is_counting = False  # สถานะว่ากำลังนับถอยหลังอยู่ไหม

    # เปิดกล้อง
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("--------------------------------------------------")
    print("📷 ระบบลงทะเบียนใบหน้า (Gesture Control)")
    print("--------------------------------------------------")
    print("  🖐️  ยกมือแบ 5 นิ้วค้างไว้ 3 วินาที เพื่อบันทึกภาพ")
    print("  👉 กด 'q' เพื่อยกเลิก")
    print("--------------------------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # กลับด้านภาพ (Mirror) เพื่อให้ควบคุมง่ายขึ้นเวลาชูมือ
        frame = cv2.flip(frame, 1)
        
        display_frame = frame.copy()
        height, width, _ = frame.shape
        
        # แปลงสีเป็น RGB สำหรับ MediaPipe และ Face Recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # --- 1. ตรวจจับมือ (Hand Detection) ---
        results = hands.process(rgb_frame)
        
        hand_detected = False
        finger_count = 0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # วาดเส้นมือลงในหน้าจอ (เพื่อให้รู้ว่ากล้องเห็นมือ)
                mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # นับนิ้วที่ชูขึ้น (Logic ง่ายๆ: ปลายนิ้วอยู่สูงกว่าข้อต่อนิ้ว)
                # Landmark ID: 4=Thumb, 8=Index, 12=Middle, 16=Ring, 20=Pinky
                lm_list = hand_landmarks.landmark
                
                # ตรวจสอบ 4 นิ้ว (ชี้, กลาง, นาง, ก้อย) - เช็คแกน Y (ค่ายิ่งน้อยคือยิ่งสูง)
                # *หมายเหตุ: นิ้วโป้งเช็คยากกว่าเล็กน้อย จึงเช็คแค่นิ้วชี้-ก้อย ถ้าขึ้นหมดถือว่าแบมือ
                fingers_up = []
                
                # ตรวจนิ้วชี้ถึงก้อย (Tips id: 8, 12, 16, 20 | PIP Joints id: 6, 10, 14, 18)
                tips_ids = [8, 12, 16, 20]
                pip_ids = [6, 10, 14, 18]

                for tip, pip in zip(tips_ids, pip_ids):
                    if lm_list[tip].y < lm_list[pip].y: # นิ้วชี้ขึ้น
                        fingers_up.append(True)
                    else:
                        fingers_up.append(False)
                
                # ถ้านิ้วชี้ กลาง นาง ก้อย ชูขึ้นหมด (>= 4 นิ้ว) ถือว่าแบมือ
                if fingers_up.count(True) == 4:
                    hand_detected = True

        # --- 2. Logic การนับเวลา (Timer Logic) ---
        if hand_detected:
            if not is_counting:
                gesture_start_time = time.time() # เริ่มจับเวลา
                is_counting = True
            
            # คำนวณเวลาที่ผ่านไป
            elapsed_time = time.time() - gesture_start_time
            time_left = capture_delay - elapsed_time

            if time_left > 0:
                # แสดงกราฟิกนับถอยหลัง
                progress = int((elapsed_time / capture_delay) * 100)
                cv2.putText(display_frame, f"HOLD STILL: {int(time_left)+1}", (50, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 165, 255), 3)
                
                # วาดหลอด Progress Bar ด้านบน
                cv2.rectangle(display_frame, (50, 50), (50 + progress * 3, 70), (0, 255, 0), -1)
                cv2.rectangle(display_frame, (50, 50), (350, 70), (255, 255, 255), 2)
            
            else:
                # --- 3. เวลาครบกำหนด! ทำการบันทึก (Trigger Save) ---
                print("📸 กำลังตรวจสอบใบหน้าเพื่อบันทึก...")
                
                # ตรวจหาใบหน้า
                face_locations = face_recognition.face_locations(rgb_frame)

                if len(face_locations) > 0:
                    # บันทึกภาพ (ใช้ภาพต้นฉบับ frame ที่ไม่มีกราฟิกทับ)
                    cv2.imwrite(filename, frame)
                    print(f"✅ บันทึกเรียบร้อย! ({filename})")
                    
                    # เอฟเฟกต์หน้าจอ Flash สีขาว
                    cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), -1)
                    cv2.imshow("Register New Face", display_frame)
                    cv2.waitKey(100)
                    
                    # แสดงข้อความ Saved แล้วจบ
                    cv2.putText(display_frame, "SAVED!", (width//2 - 100, height//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                    cv2.imshow("Register New Face", display_frame)
                    cv2.waitKey(2000)
                    break
                else:
                    # เวลาครบแต่ไม่เจอหน้า
                    cv2.putText(display_frame, "NO FACE!", (50, 150), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                    # รีเซ็ตเวลา เพื่อให้ลองใหม่
                    gesture_start_time = time.time() 
        else:
            # ถ้าเอามือลง หรือมือไม่นิ่ง -> รีเซ็ต
            is_counting = False
            gesture_start_time = 0
            cv2.putText(display_frame, "Show Hand to Capture", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

        # วาดกรอบใบหน้า (ไกด์ไลน์)
        box_size = 400
        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        cv2.rectangle(display_frame, (x1, y1), (x1 + box_size, y1 + box_size), (161, 214, 162), 2)

        cv2.imshow("Register New Face", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face()