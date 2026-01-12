import cv2
import numpy as np
import datetime
import pickle
import sys
import time
from insightface.app import FaceAnalysis
from PIL import ImageFont, ImageDraw, Image

# 🔥 เรียกใช้ข้อมูลจากไฟล์ student_db.py
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

SIMILARITY_THRESHOLD = 0.40
SHOW_RESULT_DURATION = 3

# ตัวแปรสถานะระบบ
scan_triggered = False      
result_frame = None         
result_timer = 0            

# ตัวแปรเก็บข้อมูลคนล่าสุด
latest_face_img = None      # เก็บรูปภาพเต็มใบ
latest_names = []           # เก็บรายชื่อทุกคนที่เจอ (List)
latest_time = ""            

# ==========================================
# 🔧 ฟังก์ชันช่วยเหลือ
# ==========================================
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

# ปรับขนาดภาพพื้นหลังให้เป็น 1280x720 ตามต้องการ
bg_img = cv2.resize(bg_img, (1280, 720))

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
# บังคับขนาดหน้าต่าง
cv2.resizeWindow(window_name, 1280, 720) 
cv2.setMouseCallback(window_name, on_mouse_click)

print("✅ ระบบพร้อม! (Resolution: 1280x720)")

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
        
        # สร้าง List ชั่วคราวเพื่อเก็บชื่อในรอบนี้
        current_scan_names = [] 
        
        for face in faces:
            emb = face.embedding / np.linalg.norm(face.embedding)
            scores = np.dot(known_embeds, emb) if len(known_embeds) > 0 else []
            best_idx = np.argmax(scores) if len(scores) > 0 else -1
            best_score = scores[best_idx] if len(scores) > 0 else 0
            
            # --- ตรวจสอบชื่อ ---
            if best_score > SIMILARITY_THRESHOLD:
                # เรียกใช้ STUDENT_DB ที่ import มา
                name = STUDENT_DB.get(known_names[best_idx], known_names[best_idx])
                color = (0, 255, 0)
                current_scan_names.append(name)
            else:
                name = "ไม่รู้จัก"
                color = (0, 0, 255)
                current_scan_names.append(name)
            
            # วาดกรอบบนภาพหลัก
            box = face.bbox.astype(int)
            cv2.rectangle(frame_full, (box[0], box[1]), (box[2], box[3]), color, 3)
            frame_full = put_thai_text(frame_full, name, (box[0], box[1]-40), (color[2], color[1], color[0]), 40)

        # อัปเดตข้อมูล Global ถ้าเจอคน
        if faces:
            latest_names = current_scan_names 
            latest_face_img = frame_full.copy() 
            latest_time = datetime.datetime.now().strftime("%H:%M:%S")
        elif not faces:
             frame_full = put_thai_text(frame_full, "ไม่พบใบหน้า", (50, 50), (255, 0, 0), 40)

        # ตั้งค่า Freeze หน้าจอ
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

    # --- C. วาดกล่องคนล่าสุด (Latest Scan Box) ---
    # 1. วาดรูปหน้าคน (ภาพเต็มใบ)
    if latest_face_img is not None:
        try:
            face_display = cv2.resize(latest_face_img, (LAST_W, LAST_H))
            frame_display[LAST_Y:LAST_Y+LAST_H, LAST_X:LAST_X+LAST_W] = face_display
        except Exception as e:
            print(f"Error drawing face: {e}")
    else:
        cv2.putText(frame_display, "?", (LAST_X + 180, LAST_Y + 180), cv2.FONT_HERSHEY_SIMPLEX, 4, (100, 100, 100), 5)

    # 2. แสดงรายการชื่อหลายคน
    info_y_start = LAST_Y + LAST_H + 20
    
    if len(latest_names) > 0:
        for i, name in enumerate(latest_names):
            y_pos = info_y_start + (i * 25) 
            if y_pos < frame_display.shape[0] - 50: 
                display_text = f"{i+1}. {name}"
                frame_display = put_thai_text(frame_display, display_text, (LAST_X + 20, y_pos + 30), (255, 255, 255), 25)
        
        # แสดงเวลา
        time_y_pos = info_y_start + (len(latest_names) * 45) + 10
        if latest_time:
            frame_display = put_thai_text(frame_display, f"เวลา: {latest_time}", (LAST_X + 20, time_y_pos), (200, 200, 200), 25)
    else:
        frame_display = put_thai_text(frame_display, "รอการสแกน...", (LAST_X + 100, info_y_start + 40), (255, 255, 255), 35)

    # --- D. แสดงวันที่และเวลาปัจจุบัน ---
    now = datetime.datetime.now()
    
    # วันที่
    thai_year = now.year + 543
    thai_month = THAI_MONTHS[now.month - 1]
    date_str = f"{now.day} {thai_month} {thai_year}"
    frame_display = put_thai_text(frame_display, date_str, (140, 170), (255, 255, 255), 40)

    # นาฬิกา
    time_str = now.strftime("%H:%M:%S")
    cv2.putText(frame_display, time_str, (985, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)

    cv2.imshow(window_name, frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()