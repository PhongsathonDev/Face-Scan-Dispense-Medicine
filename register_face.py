import cv2
import face_recognition
import os
import time
import numpy as np

def register_new_face_with_nod(filename="patient.jpeg"):
    # --- ตั้งค่าความไวของการพยักหน้า (ปรับแก้ได้ตรงนี้) ---
    NOD_THRESHOLD = 15       # ค่าความเปลี่ยนแปลงของแกน Y ที่ถือว่าพยักหน้า (ค่ายิ่งน้อยยิ่งไวยิ่งติดง่าย)
    NOD_FRAMES = 10          # จำนวนเฟรมที่จะเช็คย้อนหลัง (เพื่อดูการเคลื่อนไหว)
    COUNTDOWN_TIME = 3       # เวลาในการนับถอยหลัง (วินาที)
    # ------------------------------------------------

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("--------------------------------------------------")
    print("📷 ระบบลงทะเบียนใบหน้า (Head Nod Edition)")
    print("--------------------------------------------------")
    print("  👉 'พยักหน้า' ขึ้น-ลง เพื่อเริ่มนับถอยหลังและบันทึก")
    print("  👉 กด 'q' เพื่อยกเลิก (Quit)")
    print("--------------------------------------------------")

    # ตัวแปรสำหรับตรวจจับการพยักหน้า
    nose_y_history = []
    
    # ตัวแปรสำหรับระบบนับถอยหลัง
    is_counting_down = False
    countdown_start_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ ไม่สามารถเปิดกล้องได้")
            break

        # กลับด้านภาพเพื่อให้เหมือนกระจก (Mirror) จะได้กะระยะง่าย
        frame = cv2.flip(frame, 1)
        
        display_frame = frame.copy()
        height, width, _ = frame.shape

        # ลดขนาดภาพลง 1/4 เฉพาะตอนประมวลผล AI เพื่อให้ FPS ลื่นไหล (การบันทึกยังชัดเท่าเดิม)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # 1. ค้นหาใบหน้าและจุด Landmark
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        # ถ้ายังไม่เริ่มนับถอยหลัง ให้ตรวจจับการพยักหน้า
        if not is_counting_down:
            if len(face_locations) > 0:
                # หา Landmark (ตา จมูก ปาก)
                face_landmarks = face_recognition.face_landmarks(rgb_small_frame, face_locations)
                
                if face_landmarks:
                    # ใช้ตำแหน่ง "ปลายจมูก" (Nose Tip) จุดแรกในการเช็ค
                    # ต้องคูณ 4 กลับ เพราะเราย่อภาพไป 0.25
                    nose_tip = face_landmarks[0]['nose_tip'][0]
                    nose_y = nose_tip[1] * 4 

                    # เก็บประวัติแกน Y ของจมูก
                    nose_y_history.append(nose_y)
                    if len(nose_y_history) > NOD_FRAMES:
                        nose_y_history.pop(0)

                    # คำนวณส่วนต่างของตำแหน่งสูงสุดและต่ำสุดในช่วงเวลาสั้นๆ
                    if len(nose_y_history) == NOD_FRAMES:
                        movement = max(nose_y_history) - min(nose_y_history)
                        
                        # ถ้ามีการขยับขึ้นลงมากกว่าค่าที่ตั้งไว้ -> ถือว่าพยักหน้า
                        if movement > NOD_THRESHOLD:
                            print("💡 ตรวจพบการพยักหน้า! เริ่มนับถอยหลัง...")
                            is_counting_down = True
                            countdown_start_time = time.time()
                            nose_y_history = [] # เคลียร์ค่าป้องกันการกดซ้ำ

                # วาดกรอบหน้า (สีขาว) ให้รู้ว่าเจอหน้าแล้ว
                for (top, right, bottom, left) in face_locations:
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    cv2.rectangle(display_frame, (left, top), (right, bottom), (255, 255, 255), 2)

            else:
                # ถ้าไม่เจอหน้า ให้เคลียร์ประวัติ (กัน error)
                nose_y_history = []
                cv2.putText(display_frame, "Please show your face", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 2. วาด Interface
        # กรอบสี่เหลี่ยมกลางหน้าจอ (Zone ที่ควรอยู่)
        box_size = 400
        x1, y1 = (width - box_size) // 2, (height - box_size) // 2
        x2, y2 = x1 + box_size, y1 + box_size
        
        color = (161, 214, 162) if not is_counting_down else (0, 165, 255) # เปลี่ยนสีเป็นส้มตอนนับถอยหลัง
        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

        if not is_counting_down:
            cv2.putText(display_frame, "Nod to Save", (x1 + 110, y1 - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # 3. Logic การนับถอยหลังและบันทึก
        if is_counting_down:
            elapsed_time = time.time() - countdown_start_time
            time_left = COUNTDOWN_TIME - int(elapsed_time)

            if time_left > 0:
                # แสดงตัวเลขนับถอยหลังกลางจอ
                text_size = cv2.getTextSize(str(time_left), cv2.FONT_HERSHEY_SIMPLEX, 10, 20)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                cv2.putText(display_frame, str(time_left), (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 255), 20)
            else:
                # --- หมดเวลา: บันทึกภาพ ---
                cv2.imwrite(filename, frame)
                print(f"✅ บันทึกรูปภาพเรียบร้อย! ({filename})")
                
                # แสดงข้อความ Saved
                cv2.putText(display_frame, "SAVED!", (width//2 - 180, height//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                cv2.imshow("Register New Face", display_frame)
                cv2.waitKey(2000) # โชว์ค้างไว้ 2 วินาที
                break

        cv2.imshow("Register New Face", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("❌ ยกเลิก")
            break
        # เผื่ออยากกด s บันทึกเองเหมือนเดิม
        elif key == ord('s') and not is_counting_down:
            is_counting_down = True
            countdown_start_time = time.time()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face_with_nod()