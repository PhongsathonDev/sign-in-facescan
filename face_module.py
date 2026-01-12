import cv2
import numpy as np
import pickle
import time
from insightface.app import FaceAnalysis
from PIL import ImageFont, ImageDraw, Image # พระเอกของเราสำหรับภาษาไทย

# ==========================================
# ⚙️ ส่วนตั้งค่า (CONFIG)
# ==========================================
DATABASE_PATH = 'database/faces_data.pkl'
MODEL_NAME = 'buffalo_l' 
SIMILARITY_THRESHOLD = 0.40
SHOW_RESULT_TIME = 3 
FONT_PATH = "c:\\WINDOWS\\Fonts\\UPCJB.TTF" 

# สมุดรายชื่อนักศึกษา (รหัส -> ชื่อไทย)
STUDENT_DB = {
    "61": "นายพงศธร ชาลีโสม",
    "66010002": "น.ส.สมศรี เรียนเก่ง",
    "66010003": "ชิอิเนะ มาฮิรุ",
    "12345": "แอดมิน ทดสอบระบบ"
}

is_scan_triggered = False

def on_touch(event, x, y, flags, param):
    global is_scan_triggered
    if event == cv2.EVENT_LBUTTONDOWN: 
        is_scan_triggered = True

def put_thai_text(img, text, position, color, font_size):
    """ฟังก์ชันวาดตัวหนังสือภาษาไทยลงบนภาพ OpenCV"""
    # 1. แปลงภาพจาก OpenCV (BGR) เป็น PIL (RGB)
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 2. โหลดฟอนต์ (ถ้าหาไม่เจอจะใช้ฟอนต์ default)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        # ถ้าหาไฟล์ฟอนต์ไม่เจอ ให้ใช้ default (แต่จะไม่โชว์ภาษาไทยนะ)
        font = ImageFont.load_default()
        print(f"⚠️ หาไฟล์ฟอนต์ {FONT_PATH} ไม่เจอ! ภาษาไทยอาจไม่ขึ้นนะ")

    # 3. วาดตัวหนังสือ
    draw.text(position, text, font=font, fill=color)
    
    # 4. แปลงกลับเป็น OpenCV (BGR)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ==========================================
# โหลดข้อมูลและเตรียมระบบ (เหมือนเดิม)
# ==========================================
print("กำลังโหลด Database...")
try:
    with open(DATABASE_PATH, 'rb') as f:
        data = pickle.load(f)
        known_embeds = np.array(data['embeddings'])
        known_names = data['names']
    print(f"✅ โหลดเรียบร้อย: {len(known_names)} คน")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

print(f"กำลังเตรียมโมเดล {MODEL_NAME}...")
app = FaceAnalysis(name=MODEL_NAME, providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(1) # หรือ 0 ตามกล้องเธอ
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

window_name = 'Touch to Check-In (Thai Supported)'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(window_name, on_touch)

print("🚀 ระบบพร้อม! (รองรับภาษาไทย)")

while True:
    ret, frame = cap.read()
    if not ret: break

    # --- สถานะปกติ ---
    if not is_scan_triggered:
        h, w = frame.shape[:2]
        cv2.ellipse(frame, (w // 2, h // 2), (120, 160), 0, 0, 360, (255, 255, 255), 2)
        
        if int(time.time() * 2) % 2 == 0: 
            # ตรงนี้ใช้ cv2.putText ภาษาอังกฤษเหมือนเดิมได้ (มันเร็วกว่านิดหน่อย)
            cv2.putText(frame, "TAP SCREEN TO SCAN", (w//2 - 140, h - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        cv2.imshow(window_name, frame)

    # --- สถานะทำงาน (Scan) ---
    else:
        # Feedback (ภาษาอังกฤษ)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame) 
        cv2.putText(frame, "Processing...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.imshow(window_name, frame)
        cv2.waitKey(1) 

        faces = app.get(frame)
        
        for face in faces:
            current_emb = face.embedding
            current_emb = current_emb / np.linalg.norm(current_emb)
            scores = np.dot(known_embeds, current_emb)
            best_idx = np.argmax(scores)
            best_score = scores[best_idx]
            box = face.bbox.astype(int)
            
            if best_score > SIMILARITY_THRESHOLD:
                student_id = known_names[best_idx]
                
                # ดึงชื่อไทยจาก Dict
                real_name = STUDENT_DB.get(student_id, student_id) 
                
                # สีเขียว (RGB สำหรับ PIL คือ (0, 255, 0) แต่ BGR คือ (0, 255, 0) เหมือนกันถ้าเขียวล้วน)
                # แต่ PIL รับสีเป็น (R, G, B) นะ
                text_color = (0, 255, 0) 
                display_text = f"{real_name}"
                print(f"✅ เจอตัว: {real_name}")
                
            else:
                real_name = "ไม่รู้จัก"
                text_color = (255, 0, 0) # แดง
                display_text = "ไม่พบข้อมูลในระบบ"

            # วาดกรอบสี่เหลี่ยม (ใช้ OpenCV วาดกรอบได้เลย เร็วกว่า)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), text_color[::-1], 3) # กลับสีเป็น BGR
            
            # วาดพื้นหลังป้ายชื่อ
            cv2.rectangle(frame, (box[0], box[1]-50), (box[0]+300, box[1]), text_color[::-1], -1)
            
            # 🔥 เรียกใช้ฟังก์ชันภาษาไทยของเรา!
            # สังเกตว่าเราส่ง frame เข้าไป แล้วรับ frame ใหม่กลับมา
            frame = put_thai_text(frame, display_text, (box[0]+10, box[1]-45), (255, 255, 255), 30)

        if not faces:
             frame = put_thai_text(frame, "ไม่พบใบหน้า", (50, 100), (255, 0, 0), 40)

        cv2.imshow(window_name, frame)
        cv2.waitKey(SHOW_RESULT_TIME * 1000) 

        is_scan_triggered = False
        while cv2.waitKey(1) != -1: pass

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()