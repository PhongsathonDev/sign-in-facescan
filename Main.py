import cv2
import sys
import datetime
from face_module import FaceScanner 

# =================ตั้งค่า=================
IMAGE_PATH = 'D:\\Work\\FaceScan\\Main\\bg.jpg'
CAM_WIDTH, CAM_HEIGHT = 320, 240
# ตำแหน่งที่จะเอากล้องไปวางบนภาพพื้นหลัง (x, y)
# ลองปรับค่านี้ดูเพื่อให้กล้องไม่บังนาฬิกา
CAMERA_POS = (0, 0) 
# ========================================

# 1. เตรียมระบบ AI (เรียกใช้ครั้งเดียว)
scanner = FaceScanner()

# 2. เปิดกล้อง
cap = cv2.VideoCapture(1) # หรือ 1 ตามกล้องของคุณ
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

# 3. โหลดภาพพื้นหลัง
bg_img = cv2.imread(IMAGE_PATH)
if bg_img is None:
    print(f"❌ ไม่เจอไฟล์พื้นหลัง: {IMAGE_PATH}")
    sys.exit()

# ตั้งค่านาฬิกา
font_clock = cv2.FONT_HERSHEY_SIMPLEX
pos_clock = (985, 195)
color_clock = (255, 255, 255)

print("กด 'q' เพื่อปิดโปรแกรม...")

while True:
    # 1. อ่านภาพจากกล้อง
    ret, frame = cap.read()
    if not ret:
        break
    
    # 2. ส่งภาพไปให้ AI สแกนหน้าและวาดกรอบ (ใช้ไฟล์ face_module)
    # ถ้าเครื่องช้า ให้เอาบรรทัดนี้ไปใส่ใน if เพื่อทำแค่บางเฟรมได้
    frame_scanned = scanner.process_frame(frame)

    # 3. เตรียมภาพพื้นหลัง (Copy ใหม่ทุกรอบ)
    ui_display = bg_img.copy()

    # 4. เอากล้อง (ที่สแกนแล้ว) มาแปะลงบนพื้นหลัง
    # ตรวจสอบขนาดเพื่อกัน Error กรณีภาพพื้นหลังเล็กกว่ากล้อง
    h, w, _ = frame_scanned.shape
    x_offset, y_offset = CAMERA_POS
    
    try:
        # ฝังภาพกล้องลงไปใน UI
        ui_display[y_offset:y_offset+h, x_offset:x_offset+w] = frame_scanned
        
        # วาดกรอบรอบกล้องเพื่อให้ดูสวยงาม
        cv2.rectangle(ui_display, (x_offset-5, y_offset-5), 
                      (x_offset+w+5, y_offset+h+5), (255, 255, 255), 3)
    except Exception as e:
        print(f"Error การวางภาพ: {e} (ลองเช็คขนาด bg.jpg ดูนะครับ)")

    # 5. วาดนาฬิกา
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")
    cv2.putText(ui_display, time_str, pos_clock, font_clock, 1.5, color_clock, 4, cv2.LINE_AA)

    # 6. แสดงผล UI ทั้งหมด
    # ปรับขนาดหน้าต่างให้พอดีจอคอม (Optional)
    cv2.namedWindow('Smart Face Scan UI', cv2.WINDOW_NORMAL)
    cv2.imshow('Smart Face Scan UI', ui_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()