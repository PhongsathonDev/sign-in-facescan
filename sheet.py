import pandas as pd
import requests
import json

# --- ตั้งค่า ---
# 1. วาง URL ที่ได้จากการ Deploy Google Apps Script ตรงนี้
GAS_WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbzHi_d3eBsYvDEO0oyvhvcLFHzHjxC9PcIXCFNT_De_x_buFyUqB6tnCZ6tK79r-jhHdg/exec'

# 2. ไฟล์ CSV ของคุณ
CSV_FILE_PATH = 'attendance_2026-01-14.csv'

def send_csv_to_gas():
    try:
        print("1. กำลังอ่านไฟล์ CSV...")
        # อ่าน CSV
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
        
        # แปลง NaN (ค่าว่าง) เป็น string ว่างๆ (ไม่งั้น JSON จะ Error)
        df = df.fillna('')

        # แปลงเป็น List of Lists (รวม Header)
        data_list = [df.columns.values.tolist()] + df.values.tolist()

        print(f"2. กำลังส่งข้อมูล {len(data_list)} แถว ไปยัง Google Sheet...")
        
        # ส่ง Request แบบ POST
        response = requests.post(
            GAS_WEBAPP_URL, 
            json=data_list
        )

        # เช็คผลลัพธ์
        if response.status_code == 200:
            print("สำเร็จ! Google Script ตอบกลับว่า:", response.text)
        else:
            print(f"มีปัญหา: Status Code {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_csv_to_gas()