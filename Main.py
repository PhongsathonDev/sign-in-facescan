import cv2
import sys
import datetime # เรียกใช้ไลบรารีสำหรับจัดการเวลา

# 1. ระบุชื่อไฟล์รูปภาพ
image_path = 'D:\\Work\\FaceScan\\Main\\bg.jpg'

# 2. อ่านไฟล์รูปภาพเข้าสู่ตัวแปร img (โหลดเข้าเมมโมรี่ครั้งเดียว)
img = cv2.imread(image_path)

# ตรวจสอบว่าอ่านรูปภาพได้หรือไม่
if img is None:
    print(f"ไม่สามารถเปิดไฟล์รูปภาพ: {image_path} ได้ครับ")
    sys.exit()

# ตั้งค่าฟอนต์ที่จะใช้แสดงข้อความ
font = cv2.FONT_HERSHEY_SIMPLEX
org = (985, 195)          # ตำแหน่งข้อความ (x, y) จากมุมซ้ายบน
fontScale = 1.5           # ขนาดตัวอักษร
color = (255, 255, 255)      # สีตัวอักษร BGR (0, 255, 0) คือสีเขียว
thickness = 4            # ความหนาของเส้นตัวอักษร
print("กดปุ่ม 'q' หรือ 'Esc' ที่คีย์บอร์ดเพื่อปิดโปรแกรม...")

# 3. เริ่ม Loop เพื่อแสดงผลและอัปเดตเวลาตลอดเวลา
while True:
    # 3.1 สร้างสำเนาภาพขึ้นมาใหม่ในทุกๆ รอบ
    # เหตุผล: ถ้าเราวาดเวลาลงบน 'img' ต้นฉบับโดยตรง ตัวเลขจะเขียนทับกันจนอ่านไม่ออก
    # เราจึงต้องวาดลงบนกระดาษแผ่นใหม่ (frame_display) ทุกครั้งที่เวลาเปลี่ยน
    frame_display = img.copy()

    # 3.2 ดึงเวลาปัจจุบัน
    now = datetime.datetime.now()
    # จัดรูปแบบเวลาเป็น ชั่วโมง:นาที:วินาที
    time_str = now.strftime("%H:%M:%S")

    # 3.3 เขียนข้อความเวลาลงบนภาพสำเนา
    # cv2.putText(ภาพ, ข้อความ, ตำแหน่ง, ฟอนต์, ขนาด, สี, ความหนา, รูปแบบเส้น)
    cv2.putText(frame_display, time_str, org, font, fontScale, color, thickness, cv2.LINE_AA)

    # 3.4 แสดงผลภาพ
    cv2.imshow('My Image Display', frame_display)

    # 4. รอการกดปุ่ม (Delay)
    # ใช้ waitKey(1) เพื่อรอ 1 มิลลิวินาที แล้ววนลูปต่อ ทำให้ภาพดูเหมือนเคลื่อนไหว
    key = cv2.waitKey(1) & 0xFF

    # ถ้ากดปุ่ม 'q' หรือปุ่ม Esc (ASCII 27) ให้หลุดจากลูปเพื่อปิดโปรแกรม
    if key == ord('q') or key == 27:
        break

# 5. คืนทรัพยากรระบบ
cv2.destroyAllWindows()