import cv2
import numpy as np
import datetime
import pickle
import sys
import time
from insightface.app import FaceAnalysis
from PIL import ImageFont, ImageDraw, Image

# ==========================================
# ⚙️ ส่วนตั้งค่า (CONFIG)
# ==========================================
BG_IMAGE_PATH = 'D:\\Work\\FaceScan\\Main\\bg.jpg'
DATABASE_PATH = 'database/faces_data.pkl'
FONT_PATH = "c:\\WINDOWS\\Fonts\\UPCJB.TTF" 

# --- ตั้งค่าหน้าจอ ---
# ขนาดและตำแหน่งกล้องเล็ก (Picture-in-Picture)
CAM_W, CAM_H = 760, 450
CAM_X, CAM_Y = 45, 250

# ปุ่มกดสแกน (อยู่ใต้กล้อง)
BTN_X, BTN_Y = 530, 650
BTN_W, BTN_H = 250, 50
BTN_COLOR = (0, 200, 0)       # สีปุ่ม (เขียว)
BTN_TEXT_COLOR = (255, 255, 255)

SIMILARITY_THRESHOLD = 0.40
SHOW_RESULT_DURATION = 3 # โชว์ผลค้างไว้กี่วินาที

# สมุดรายชื่อ
STUDENT_DB = {
    "61": "นายพงศธร ชาลีโสม",
    "66010002": "น.ส.สมศรี เรียนเก่ง",
    "66010003": "ชิอิเนะ มาฮิรุ",
    "12345": "แอดมิน ทดสอบระบบ"
}

# ตัวแปรสถานะ
scan_triggered = False      # สั่งให้เริ่มสแกน
result_frame = None         # เก็บภาพผลลัพธ์ที่สแกนเสร็จแล้ว
result_timer = 0            # จับเวลาการโชว์ผล

# ==========================================
# 🔧 ฟังก์ชันช่วยเหลือ
# ==========================================
def on_mouse_click(event, x, y, flags, param):
    """ฟังก์ชันตรวจจับการคลิกเมาส์ที่ปุ่ม"""
    global scan_triggered
    if event == cv2.EVENT_LBUTTONDOWN:
        # เช็คว่าคลิกโดนปุ่มหรือไม่
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

print("⏳ กำลังโหลด Database และ AI Model...")
try:
    with open(DATABASE_PATH, 'rb') as f:
        data = pickle.load(f)
        known_embeds = np.array(data['embeddings'])
        known_names = data['names']
except Exception:
    known_embeds, known_names = [], []

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(1) # หรือ 0
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

window_name = 'Smart Sign-In (Button Mode)'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(window_name, on_mouse_click) # ผูกเมาส์กับหน้าต่าง

print("✅ ระบบพร้อม! กดปุ่มสีเขียวเพื่อสแกน")

while True:
    # 1. เตรียมพื้นหลัง (Canvas)
    frame_display = bg_img.copy()
    
    # 2. อ่านกล้อง (แต่อย่าเพิ่งส่งเข้า AI เพื่อความลื่น)
    ret, frame_full = cap.read()
    if not ret: break

    # 3. ตรวจสอบสถานะการทำงาน
    current_time = time.time()
    
    # --- กรณี A: กำลังแสดงผลลัพธ์ (Freeze Result) ---
    if result_frame is not None and current_time < result_timer:
        # ใช้ภาพนิ่งที่สแกนเสร็จแล้วมาแสดง
        display_cam = result_frame
        
        # วาดแถบเวลานับถอยหลังที่ปุ่ม
        time_left = int(result_timer - current_time)
        btn_text = f"โชว์ผลอีก {time_left} วิ"
        btn_bg = (100, 100, 100) # สีเทา (Disabled)

    # --- กรณี B: สั่งสแกน (Processing) ---
    elif scan_triggered:
        # ส่งเข้า AI (กระตุกนิดนึงแค่วินาทีนี้)
        faces = app.get(frame_full)
        
        # วาดผลลัพธ์ลงบน frame_full
        for face in faces:
            emb = face.embedding / np.linalg.norm(face.embedding)
            scores = np.dot(known_embeds, emb) if len(known_embeds) > 0 else []
            best_idx = np.argmax(scores) if len(scores) > 0 else -1
            best_score = scores[best_idx] if len(scores) > 0 else 0
            
            if best_score > SIMILARITY_THRESHOLD:
                name = STUDENT_DB.get(known_names[best_idx], known_names[best_idx])
                color = (0, 255, 0)
            else:
                name = "ไม่รู้จัก"
                color = (0, 0, 255)
            
            box = face.bbox.astype(int)
            cv2.rectangle(frame_full, (box[0], box[1]), (box[2], box[3]), color, 3)
            # ใส่ชื่อ
            frame_full = put_thai_text(frame_full, name, (box[0], box[1]-40), (color[2], color[1], color[0]), 40)
        
        if not faces:
             frame_full = put_thai_text(frame_full, "ไม่พบใบหน้า", (50, 50), (255, 0, 0), 40)

        # บันทึกภาพผลลัพธ์ และตั้งเวลาโชว์
        result_frame = cv2.resize(frame_full, (CAM_W, CAM_H))
        display_cam = result_frame
        result_timer = current_time + SHOW_RESULT_DURATION
        scan_triggered = False # รีเซ็ตปุ่ม
        
        btn_text = "เรียบร้อย!"
        btn_bg = (0, 100, 0)

    # --- กรณี C: โหมดปกติ (Live View) ---
    else:
        # ย่อภาพมาแสดงเฉยๆ ลื่นๆ
        display_cam = cv2.resize(frame_full, (CAM_W, CAM_H))
        result_frame = None # เคลียร์ภาพค้าง
        
        btn_text = "คลิกเพื่อสแกนใบหน้า"
        btn_bg = BTN_COLOR

    # 4. ประกอบร่าง (Drawing UI)
    
    # 4.1 แปะภาพกล้องลงพื้นหลัง
    if CAM_Y + CAM_H <= frame_display.shape[0] and CAM_X + CAM_W <= frame_display.shape[1]:
        frame_display[CAM_Y:CAM_Y+CAM_H, CAM_X:CAM_X+CAM_W] = display_cam
        # วาดกรอบรอบกล้อง
        cv2.rectangle(frame_display, (CAM_X-2, CAM_Y-2), (CAM_X+CAM_W+2, CAM_Y+CAM_H+2), (255, 255, 255), 2)

    # 4.2 วาดปุ่มกด (Button)
    cv2.rectangle(frame_display, (BTN_X, BTN_Y), (BTN_X+BTN_W, BTN_Y+BTN_H), btn_bg, -1)
    cv2.rectangle(frame_display, (BTN_X, BTN_Y), (BTN_X+BTN_W, BTN_Y+BTN_H), (255, 255, 255), 2)
    
    # คำนวณตำแหน่งข้อความให้อยู่กลางปุ่ม
    text_size = cv2.getTextSize(btn_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0] # คำนวณคร่าวๆ
    # แต่เราใช้ฟังก์ชันภาษาไทย ดังนั้นกะระยะเอาหน่อย
    frame_display = put_thai_text(frame_display, btn_text, (BTN_X + 20, BTN_Y + 10), BTN_TEXT_COLOR, 30)

    # 4.3 แสดงนาฬิกา (เดินตลอดเวลา ไม่หยุด)
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")
    cv2.putText(frame_display, time_str, (985, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)

    # แสดงผล
    cv2.imshow(window_name, frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()