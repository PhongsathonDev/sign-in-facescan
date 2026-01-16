import pandas as pd
import requests
import json
import datetime
import os

# --- ตั้งค่า ---
GAS_WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbyCIgLPVQPEFQhtNYu8eRsyU624ERuMO4jqvBGU1iyUUU9eI_LjE01uIDNqQf4iDoU_cg/exec'

# สร้างชื่อไฟล์ตามวันที่ปัจจุบัน (เช่น attendance_2026-01-14.csv)
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
CSV_FILE_PATH = f'attendance_{today_str}.csv'
HISTORY_FILE = 'sent_history.json'

def get_sent_count(filename):
    """อ่านค่าว่าไฟล์นี้เคยส่งไปกี่แถวแล้ว"""
    if not os.path.exists(HISTORY_FILE):
        return 0
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(filename, 0)
    except:
        return 0

def update_sent_count(filename, count):
    """บันทึกค่าจำนวนแถวล่าสุดที่ส่งไป"""
    data = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    
    data[filename] = count
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def send_csv_to_gas():
    # 1. เช็คไฟล์ CSV
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ ไม่พบไฟล์ {CSV_FILE_PATH} (ยังไม่มีการสแกนวันนี้)")
        return

    try:
        print(f"📂 กำลังอ่านไฟล์: {CSV_FILE_PATH}")
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
        df = df.fillna('')
        
        total_rows = len(df)
        sent_rows = get_sent_count(CSV_FILE_PATH)

        # 2. เช็คว่ามีข้อมูลใหม่ไหม
        if total_rows <= sent_rows:
            print(f"✅ ข้อมูลล่าสุด {total_rows} แถว ถูกส่งไปหมดแล้ว (ไม่ต้องส่งซ้ำ)")
            return

        # 3. ตัดเอาเฉพาะแถวใหม่ (Slicing)
        new_data = df.iloc[sent_rows:]
        print(f"🚀 พบข้อมูลใหม่ {len(new_data)} แถว (จากเดิม {sent_rows})")

        # เตรียมข้อมูลส่ง
        # - ถ้าส่งครั้งแรก (sent_rows == 0) ให้ส่ง Header ไปด้วย
        # - ถ้าส่งรอบเก็บตก (sent_rows > 0) ไม่ต้องส่ง Header (เดี๋ยวไปโผล่กลางตาราง)
        data_list = []
        if sent_rows == 0:
            data_list = [df.columns.values.tolist()] + new_data.values.tolist()
        else:
            data_list = new_data.values.tolist()

        print(f"📡 กำลังส่งข้อมูลไปยัง Google Sheet...")
        response = requests.post(GAS_WEBAPP_URL, json=data_list)

        if response.status_code == 200:
            print("✅ สำเร็จ! Google ตอบกลับ:", response.text)
            # บันทึกสถานะว่าส่งถึงแถวไหนแล้ว
            update_sent_count(CSV_FILE_PATH, total_rows)
        else:
            print(f"❌ มีปัญหา: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_csv_to_gas()