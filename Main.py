import cv2
import numpy as np
import datetime
import pickle
import sys
import time
import csv
import os
import threading  
from insightface.app import FaceAnalysis
from PIL import ImageFont, ImageDraw, Image

# เรียกใช้ข้อมูลจากไฟล์ student_db.py
from student_db import STUDENT_DB 

# ==========================================
# ⚙️ ส่วนตั้งค่า (CONFIG)
# ==========================================
BG_IMAGE_PATH = 'D:\\Work\\sign-in-facescan\\bg.jpg'
DATABASE_PATH = 'database/faces_data.pkl'
FONT_PATH = "c:\\WINDOWS\\Fonts\\UPCJB.TTF" 

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

# --- 1. ตั้งค่าหน้าจอ (Camera หลัก) ---
CAM_W, CAM_H = 760, 450
CAM_X, CAM_Y = 45, 250

# --- 2. ตั้งค่าปุ่มกด ---
BTN_X, BTN_Y = 530, 650
BTN_W, BTN_H = 250, 50
BTN_COLOR = (0, 200, 0)
BTN_TEXT_COLOR = (255, 255, 255)

# --- 3. กล่องแสดงผลหน้าล่าสุด ---
LAST_X, LAST_Y = 840, 250  
LAST_W, LAST_H = 410, 260  
TEXT_OFFSET_Y = 40         

MAX_HISTORY = 5 
SIMILARITY_THRESHOLD = 0.40

# ตัวแปรเก็บข้อมูลหน้าจอ
latest_face_img = None      
latest_names = []           
latest_time = ""            

# 🔥 ตัวแปรสำหรับเช็คชื่อและประวัติ
present_students = set() 
scan_history = [] 
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
attendance_file = f"attendance_{today_str}.csv" 

# 🔥 ตัวแปรสำหรับ Thread (Scan อัตโนมัติ)
frame_to_process = None  
scan_running = True      

# ==========================================
# 🔧 ฟังก์ชันช่วยเหลือ
# ==========================================

def load_today_attendance():
    """โหลดข้อมูลเก่าและประวัติล่าสุดเมื่อเปิดโปรแกรม"""
    global scan_history
    if not os.path.exists(attendance_file):
        with open(attendance_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Student ID", "Name", "Time"])
        return

    with open(attendance_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader, None)
        rows = list(reader)
        
        for row in rows:
            if row and len(row) >= 1:
                if row[0] in STUDENT_DB:
                    present_students.add(row[0])
        
        valid_rows = [r for r in rows if len(r) >= 3 and r[0] in STUDENT_DB]
        recent_rows = valid_rows[-MAX_HISTORY:]
        
        for row in reversed(recent_rows):
            scan_history.append({"name": row[1], "time": row[2]})
            
    print(f"✅ โหลดข้อมูลเก่า: มาแล้ว {len(present_students)} คน (History: {len(scan_history)})")

def mark_attendance(student_id, name):
    """
    บันทึกและอัปเดตประวัติ 
    Return: True ถ้าเป็นการบันทึกครั้งแรกของวัน (New Record)
    Return: False ถ้าเคยมาแล้ว
    """
    global scan_history
    
    # เช็คว่ายังไม่เคยมาวันนี้
    if student_id in STUDENT_DB and student_id not in present_students:
        present_students.add(student_id)
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        try:
            with open(attendance_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, name, current_time])
            print(f"💾 บันทึก: {name} เวลา {current_time}")
        except Exception as e:
            print(f"❌ Error บันทึกไฟล์: {e}")
            
        scan_history.insert(0, {"name": name, "time": current_time})
        if len(scan_history) > MAX_HISTORY:
            scan_history.pop()
        
        return True # ✅ เป็นคนใหม่ (ครั้งแรกของวัน)
    
    return False # ❌ เคยมาแล้ว

def put_thai_text(img, text, position, color, font_size):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ==========================================
# 🧠 ฟังก์ชันสแกนหน้าเบื้องหลัง (Thread Function)
# ==========================================
def process_scan_thread():
    global latest_face_img, latest_names, latest_time
    
    print("🚀 Background Scan Started...")
    
    while scan_running:
        if frame_to_process is None:
            time.sleep(0.1)
            continue
            
        try:
            img_scan = frame_to_process.copy()
            faces = app.get(img_scan)
            
            # 🔥 ตัวแปรเช็คว่ารอบนี้ "เจอคนใหม่" (New Record) หรือไม่
            found_new_person = False 
            current_scan_names = []
            
            if len(faces) > 0:
                for face in faces:
                    emb = face.embedding / np.linalg.norm(face.embedding)
                    scores = np.dot(known_embeds, emb) if len(known_embeds) > 0 else []
                    best_idx = np.argmax(scores) if len(scores) > 0 else -1
                    best_score = scores[best_idx] if len(scores) > 0 else 0
                    
                    if best_score > SIMILARITY_THRESHOLD:
                        student_id = known_names[best_idx]
                        name = STUDENT_DB.get(student_id, student_id)
                        color = (0, 255, 0)
                        current_scan_names.append(name)
                        
                        # เช็คว่าเป็นคนใหม่หรือไม่?
                        is_new_record = mark_attendance(student_id, name)
                        
                        if is_new_record:
                            found_new_person = True # ✅ ถ้าเป็นคนใหม่ ให้ปักธงอัปเดตรูป
                        
                    else:
                        name = "ไม่รู้จัก"
                        color = (0, 0, 255)
                        current_scan_names.append(name)
                    
                    # วาดกรอบเตรียมไว้
                    box = face.bbox.astype(int)
                    cv2.rectangle(img_scan, (box[0], box[1]), (box[2], box[3]), color, 3)
                    img_scan = put_thai_text(img_scan, name, (box[0], box[1]-40), (color[2], color[1], color[0]), 40)
            
                # 🔥 อัปเดตกล่องขวา "เฉพาะเมื่อเจอคนใหม่ (First Time Scan)" เท่านั้น
                if found_new_person:
                    latest_names = current_scan_names 
                    latest_face_img = img_scan.copy() 
                    latest_time = datetime.datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print(f"Error in thread: {e}")

        time.sleep(1)

# ==========================================
# 🚀 เริ่มต้นระบบ
# ==========================================
bg_img = cv2.imread(BG_IMAGE_PATH)
if bg_img is None:
    print(f"❌ ไม่พบไฟล์พื้นหลัง: {BG_IMAGE_PATH}")
    sys.exit()

bg_img = cv2.resize(bg_img, (1280, 720))

load_today_attendance()

print("⏳ กำลังโหลด AI...")
try:
    with open(DATABASE_PATH, 'rb') as f:
        data = pickle.load(f)
        known_embeds = np.array(data['embeddings'])
        known_names = data['names']
except Exception:
    known_embeds, known_names = [], []

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

window_name = 'Smart Sign-In (Auto Scan)'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 1280, 720) 

# --- เริ่มต้น Thread ---
t = threading.Thread(target=process_scan_thread, daemon=True)
t.start()

print("✅ ระบบพร้อม! (Auto Mode - Show First Time Only)")

while True:
    frame_display = bg_img.copy()
    
    ret, frame_full = cap.read()
    if not ret: break

    frame_to_process = frame_full.copy()

    # =========================================
    # ส่วนวาดหน้าจอ
    # =========================================

    # --- A. วาดกล้องหลัก ---
    display_cam = cv2.resize(frame_full, (CAM_W, CAM_H))
    if CAM_Y + CAM_H <= frame_display.shape[0] and CAM_X + CAM_W <= frame_display.shape[1]:
        frame_display[CAM_Y:CAM_Y+CAM_H, CAM_X:CAM_X+CAM_W] = display_cam
        cv2.rectangle(frame_display, (CAM_X-2, CAM_Y-2), (CAM_X+CAM_W+2, CAM_Y+CAM_H+2), (255, 255, 255), 2)

    # --- B. สถานะ ---
    cv2.rectangle(frame_display, (BTN_X, BTN_Y), (BTN_X+BTN_W, BTN_Y+BTN_H), (0, 100, 0), -1)
    frame_display = put_thai_text(frame_display, "ระบบสแกนอัตโนมัติ", (BTN_X + 25, BTN_Y + 10), (255, 255, 255), 30)

    # --- C. วาดกล่องคนล่าสุด (รูปภาพ) ---
    if latest_face_img is not None:
        try:
            face_display = cv2.resize(latest_face_img, (LAST_W, LAST_H))
            frame_display[LAST_Y:LAST_Y+LAST_H, LAST_X:LAST_X+LAST_W] = face_display
        except Exception as e:
            pass
    else:
        cv2.putText(frame_display, "?", (LAST_X + 180, LAST_Y + 180), cv2.FONT_HERSHEY_SIMPLEX, 4, (100, 100, 100), 5)

    # --- D. รายชื่อ --- 
    info_y_start = LAST_Y + LAST_H + 20 
    list_y_start = info_y_start + 40
    
    if len(scan_history) > 0:
        for i, item in enumerate(scan_history):
            display_text = f"{i+1}. {item['name']} ({item['time']})"
            y_pos = list_y_start + (i * 25)
            if y_pos < frame_display.shape[0] - 10:
                frame_display = put_thai_text(frame_display, display_text, (LAST_X + 10, y_pos), (255, 255, 255), 24)
    else:
        frame_display = put_thai_text(frame_display, "- รอการสแกน -", (LAST_X + 20, list_y_start), (200, 200, 200), 24)

    # --- E. วันที่เวลา ---
    now = datetime.datetime.now()
    thai_year = now.year + 543
    thai_month = THAI_MONTHS[now.month - 1]
    date_str = f"{now.day} {thai_month} {thai_year}"
    frame_display = put_thai_text(frame_display, date_str, (140, 170), (255, 255, 255), 40)

    time_str = now.strftime("%H:%M:%S")
    cv2.putText(frame_display, time_str, (985, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
    
    total_students = len(STUDENT_DB)
    present_count = len(present_students)
    count_str = f"{present_count} / {total_students} คน"
    frame_display = put_thai_text(frame_display, count_str, (585, 165), (255, 255, 255), 55)

    cv2.imshow(window_name, frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        scan_running = False 
        break

cap.release()
cv2.destroyAllWindows()