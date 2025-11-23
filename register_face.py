import cv2
import face_recognition
import mediapipe as mp
import time
import os

def register_new_face(filename="patient.jpeg"):
    # --- ตั้งค่า MediaPipe ---
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # --- ตัวแปรระบบนับถอยหลัง ---
    is_counting_down = False # สถานะว่ากำลังนับถอยหลังอยู่ไหม
    start_time = 0
    countdown_duration = 3.0 # เวลานับถอยหลัง (วินาที)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("--------------------------------------------------")
    print("📷 ระบบถ่ายภาพอัตโนมัติ (Auto Selfie)")
    print("--------------------------------------------------")
    print("  🖐️  แบมือ 5 นิ้ว เพื่อเริ่มนับถอยหลัง")
    print("  ⬇️  เมื่อเลขนับถอยหลังขึ้น เอามือลงได้เลย")
    print("  👉 กด 'q' เพื่อยกเลิก")
    print("--------------------------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # กลับด้านภาพ (Mirror)
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        height, width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # --- ส่วนที่ 1: ตรวจจับมือ (ทำงานเฉพาะตอนที่ยังไม่เริ่มนับถอยหลัง) ---
        if not is_counting_down:
            results = hands.process(rgb_frame)
            
            hand_detected = False
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    lm_list = hand_landmarks.landmark
                    fingers_up = []
                    
                    # Logic เช็คนิ้วเดิม (Tip < PIP = นิ้วชี้ขึ้น)
                    tips_ids = [8, 12, 16, 20]
                    pip_ids = [6, 10, 14, 18]

                    for tip, pip in zip(tips_ids, pip_ids):
                        if lm_list[tip].y < lm_list[pip].y:
                            fingers_up.append(True)
                        else:
                            fingers_up.append(False)
                    
                    # เช็คนิ้วโป้ง (Tip อยู่ซ้าย/ขวาของ IP ขึ้นอยู่กับมือซ้าย/ขวา) - เช็คแบบง่าย: 4 นิ้วหลักต้องขึ้น
                    if fingers_up.count(True) == 4:
                        hand_detected = True

            # ถ้าเจอแบมือ -> เริ่มนับถอยหลังทันที!
            if hand_detected:
                is_counting_down = True
                start_time = time.time()
                print("🚀 เริ่มนับถอยหลัง! เอามือลงได้เลยครับ")

            # แสดงข้อความบอกสถานะปกติ
            cv2.putText(display_frame, "Show Hand to Start Timer", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # --- ส่วนที่ 2: การทำงานตอนนับถอยหลัง (ไม่ต้องสนเรื่องมือแล้ว) ---
        else:
            elapsed_time = time.time() - start_time
            time_left = countdown_duration - elapsed_time

            if time_left > 0:
                # แสดงตัวเลขนับถอยหลังกลางจอใหญ่ๆ
                seconds_display = int(time_left) + 1
                text_size = cv2.getTextSize(str(seconds_display), cv2.FONT_HERSHEY_SIMPLEX, 10, 20)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                
                cv2.putText(display_frame, str(seconds_display), (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 255), 20)
                
                cv2.putText(display_frame, "Put hand down & Smile!", (width//2 - 200, height - 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            else:
                # --- เวลาหมด! ถ่ายรูปทันที ---
                print("📸 แชะ!")
                
                # เช็คใบหน้าครั้งสุดท้ายก่อนบันทึก (เพื่อให้แน่ใจว่ามีคนอยู่)
                face_locations = face_recognition.face_locations(rgb_frame)

                if len(face_locations) > 0:
                    # บันทึกภาพ (Clean frame)
                    cv2.imwrite(filename, frame)
                    print(f"✅ บันทึกเรียบร้อย: {filename}")

                    # Effect แฟลชและโชว์รูป
                    cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), -1)
                    cv2.imshow("Register New Face", display_frame)
                    cv2.waitKey(100)
                    
                    cv2.putText(display_frame, "SAVED!", (width//2 - 150, height//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                    cv2.imshow("Register New Face", display_frame)
                    cv2.waitKey(2000)
                    break # ออกจากลูป จบโปรแกรม
                else:
                    print("⚠️ ไม่พบใบหน้า! ลองใหม่อีกครั้ง")
                    is_counting_down = False # รีเซ็ตกลับไปสถานะรอมือใหม่
                    
        # วาดกรอบไกด์ไลน์เสมอ
        box_size = 400
        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        cv2.rectangle(display_frame, (x1, y1), (x1 + box_size, y1 + box_size), (161, 214, 162), 2)

        cv2.imshow("Register New Face", display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face()