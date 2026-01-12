import cv2
import numpy as np
import datetime
import pickle
import sys
import time
import csv
import os
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

# 🔥 [เพิ่ม] จำนวนคนล่าสุดที่จะแสดง (ปรับแก้ตรงนี้ได้เลย)
MAX_HISTORY = 5 

SIMILARITY_THRESHOLD = 0.40
SHOW_RESULT_DURATION = 3

# ตัวแปรสถานะระบบ
scan_triggered = False      
result_frame = None         
result_timer = 0            

# ตัวแปรเก็บข้อมูลหน้าจอ
latest_face_img = None      
latest_names = []           
latest_time = ""            

# 🔥 ตัวแปรสำหรับเช็คชื่อและประวัติ
present_students = set() 
scan_history = []  # เก็บประวัติคนล่าสุด [{'name':..., 'time':...}, ...]
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
attendance_file = f"attendance_{today_str}.csv" 

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

    # อ่านข้อมูลทั้งหมดเข้ามาก่อน
    with open(attendance_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader, None) # ข้าม header
        rows = list(reader) # อ่านทั้งหมดเป็น List
        
        # 1. คืนค่าคนทีมาแล้ว (Set)
        for row in rows:
            if row and len(row) >= 1:
                if row[0] in STUDENT_DB:
                    present_students.add(row[0])
        
        # 2. คืนค่าประวัติล่าสุด (scan_history) เอาแค่ MAX_HISTORY คนท้ายสุด
        # ข้อมูลใน csv คือ [id, name, time]
        valid_rows = [r for r in rows if len(r) >= 3 and r[0] in STUDENT_DB]
        recent_rows = valid_rows[-MAX_HISTORY:] # ตัดเอาเฉพาะกลุ่มท้ายๆ
        
        # ใส่เข้า history แบบกลับด้าน (คนล่าสุดอยู่บนสุด)
        for row in reversed(recent_rows):
            scan_history.append({"name": row[1], "time": row[2]})
            
    print(f"✅ โหลดข้อมูลเก่า: มาแล้ว {len(present_students)} คน (History: {len(scan_history)})")

def mark_attendance(student_id, name):
    """บันทึกและอัปเดตประวัติ"""
    global scan_history
    
    # เช็คว่ายังไม่เคยมาวันนี้
    if student_id in STUDENT_DB and student_id not in present_students:
        present_students.add(student_id)
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 1. บันทึกลงไฟล์
        try:
            with open(attendance_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, name, current_time])
            print(f"💾 บันทึก: {name} เวลา {current_time}")
        except Exception as e:
            print(f"❌ Error บันทึกไฟล์: {e}")
            
        # 2. 🔥 เพิ่มลงในประวัติหน้าจอ (คนล่าสุดอยู่ index 0)
        scan_history.insert(0, {"name": name, "time": current_time})
        
        # ถ้าเกินจำนวนที่ตั้งไว้ ให้ลบคนเก่าสุดออก
        if len(scan_history) > MAX_HISTORY:
            scan_history.pop()

def on_mouse_click(event, x, y, flags, param):
    global scan_triggered
    if event == cv2.EVENT_LBUTTONDOWN:
        if BTN_X <= x <= BTN_X + BTN_W and BTN_Y <= y <= BTN_Y + BTN_H:
            scan_triggered = True
            print("🖱️ Button Clicked! Scanning...")

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

window_name = 'Smart Sign-In (Full Option)'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 1280, 720) 
cv2.setMouseCallback(window_name, on_mouse_click)

print("✅ ระบบพร้อม!")

while True:
    frame_display = bg_img.copy()
    
    ret, frame_full = cap.read()
    if not ret: break

    current_time = time.time()

    # =========================================
    # ส่วนประมวลผล (Processing Logic)
    # =========================================
    
    # 1. กรณีแสดงผลค้าง (Freeze)
    if result_frame is not None and current_time < result_timer:
        display_cam = result_frame
        time_left = int(result_timer - current_time)
        btn_text = f"โชว์ผลอีก {time_left} วิ"
        btn_bg = (100, 100, 100)

    # 2. กรณีสั่งสแกน (Scan Triggered)
    elif scan_triggered:
        faces = app.get(frame_full)
        current_scan_names = [] 
        
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
                
                # 🔥 บันทึกการมาเรียน + อัปเดตประวัติหน้าจอ
                mark_attendance(student_id, name)
                
            else:
                name = "ไม่รู้จัก"
                color = (0, 0, 255)
                current_scan_names.append(name)
            
            # วาดกรอบบนภาพ
            box = face.bbox.astype(int)
            cv2.rectangle(frame_full, (box[0], box[1]), (box[2], box[3]), color, 3)
            frame_full = put_thai_text(frame_full, name, (box[0], box[1]-40), (color[2], color[1], color[0]), 40)

        if faces:
            latest_names = current_scan_names 
            latest_face_img = frame_full.copy() 
            latest_time = datetime.datetime.now().strftime("%H:%M:%S")
        elif not faces:
             frame_full = put_thai_text(frame_full, "ไม่พบใบหน้า", (50, 50), (255, 0, 0), 40)

        result_frame = cv2.resize(frame_full, (CAM_W, CAM_H))
        display_cam = result_frame
        result_timer = current_time + SHOW_RESULT_DURATION
        scan_triggered = False
        btn_text = "เรียบร้อย!"
        btn_bg = (0, 100, 0)

    # 3. โหมดปกติ (Live View)
    else:
        display_cam = cv2.resize(frame_full, (CAM_W, CAM_H))
        result_frame = None
        btn_text = "คลิกเพื่อสแกนใบหน้า"
        btn_bg = BTN_COLOR

    # =========================================
    # ส่วนวาดหน้าจอ (Drawing Logic)
    # =========================================

    # --- A. วาดกล้องหลัก ---
    if CAM_Y + CAM_H <= frame_display.shape[0] and CAM_X + CAM_W <= frame_display.shape[1]:
        frame_display[CAM_Y:CAM_Y+CAM_H, CAM_X:CAM_X+CAM_W] = display_cam
        cv2.rectangle(frame_display, (CAM_X-2, CAM_Y-2), (CAM_X+CAM_W+2, CAM_Y+CAM_H+2), (255, 255, 255), 2)

    # --- B. วาดปุ่มกด ---
    cv2.rectangle(frame_display, (BTN_X, BTN_Y), (BTN_X+BTN_W, BTN_Y+BTN_H), btn_bg, -1)
    cv2.rectangle(frame_display, (BTN_X, BTN_Y), (BTN_X+BTN_W, BTN_Y+BTN_H), (255, 255, 255), 2)
    frame_display = put_thai_text(frame_display, btn_text, (BTN_X + 20, BTN_Y + 10), BTN_TEXT_COLOR, 30)

    # --- C. วาดกล่องคนล่าสุด (รูปภาพ) ---
    if latest_face_img is not None:
        try:
            face_display = cv2.resize(latest_face_img, (LAST_W, LAST_H))
            frame_display[LAST_Y:LAST_Y+LAST_H, LAST_X:LAST_X+LAST_W] = face_display
        except Exception as e:
            print(f"Error drawing face: {e}")
    else:
        cv2.putText(frame_display, "?", (LAST_X + 180, LAST_Y + 180), cv2.FONT_HERSHEY_SIMPLEX, 4, (100, 100, 100), 5)

    # 🔥🔥 --- D. แสดงประวัติ 5 คนล่าสุด (History List) --- 🔥🔥
    # ตำแหน่งเริ่มเขียนข้อความ (ใต้รูปภาพ)
    info_y_start = LAST_Y + LAST_H + 20 
    
    # วาดหัวข้อ
    # header_text = f"ประวัติ {MAX_HISTORY} คนล่าสุด"
    # frame_display = put_thai_text(frame_display, header_text, (LAST_X, info_y_start), (0, 255, 255), 28)
    
    # วนลูปแสดงรายชื่อจาก scan_history
    list_y_start = info_y_start + 40
    if len(scan_history) > 0:
        for i, item in enumerate(scan_history):
            # item คือ {'name': 'ชื่อ', 'time': 'เวลา'}
            display_text = f"{i+1}. {item['name']} ({item['time']})"
            
            y_pos = list_y_start + (i * 25) # บรรทัดละ 30 pixel
            
            # ตรวจสอบไม่ให้เขียนเกินขอบจอ
            if y_pos < frame_display.shape[0] - 10:
                frame_display = put_thai_text(frame_display, display_text, (LAST_X + 10, y_pos), (255, 255, 255), 24)
    else:
        frame_display = put_thai_text(frame_display, "- รอการสแกน -", (LAST_X + 20, list_y_start), (200, 200, 200), 24)


    # --- E. ข้อมูลวันที่และเวลา + ตัวนับ (Counter) ---
    now = datetime.datetime.now()
    
    # วันที่
    thai_year = now.year + 543
    thai_month = THAI_MONTHS[now.month - 1]
    date_str = f"{now.day} {thai_month} {thai_year}"
    frame_display = put_thai_text(frame_display, date_str, (140, 170), (255, 255, 255), 40)

    # นาฬิกา
    time_str = now.strftime("%H:%M:%S")
    cv2.putText(frame_display, time_str, (985, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
    
    # ตัวนับ
    total_students = len(STUDENT_DB)
    present_count = len(present_students)
    count_str = f"{present_count} / {total_students} คน"
    
    frame_display = put_thai_text(frame_display, count_str, (585, 165), (255, 255, 255), 55)

    cv2.imshow(window_name, frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()