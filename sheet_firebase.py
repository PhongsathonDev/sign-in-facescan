import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# --- 1. ตั้งค่าการเชื่อมต่อ Firebase ---
# ใส่ชื่อไฟล์ JSON กุญแจของเธอตรงนี้
SERVICE_ACCOUNT_KEY = 'firebasekey.json'
DATABASE_URL = 'https://ant-facescan-default-rtdb.asia-southeast1.firebasedatabase.app/'

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })

# ไฟล์สำหรับบันทึกว่าส่งไปถึงบรรทัดไหนแล้ว (กันส่งซ้ำเหมือนใน sheet.py)
HISTORY_FILE = 'firebase_sent_history.json'

def get_sent_count(filename):
    if not os.path.exists(HISTORY_FILE): return 0
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(filename, 0)
    except: return 0

def update_sent_count(filename, count):
    data = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: data = {}
    data[filename] = count
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def upload_to_firebase(file_path):
    if not os.path.exists(file_path):
        print(f"❌ ไม่พบไฟล์ {file_path}")
        return

    try:
        # อ่านไฟล์ CSV
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        total_rows = len(df)
        sent_rows = get_sent_count(file_path)

        if total_rows <= sent_rows:
            print("✅ ข้อมูลล่าสุดถูกส่งไปหมดแล้วค่ะ")
            return

        # เลือกเฉพาะข้อมูลใหม่ที่ยังไม่ได้ส่ง
        new_data = df.iloc[sent_rows:]
        print(f"🚀 กำลังส่งข้อมูลใหม่ {len(new_data)} รายการ...")

        for index, row in new_data.iterrows():
            student_id = str(row['Student ID'])
            date_str = row['Date']  # ดึงวันที่จาก CSV (เช่น 2026-01-15)
            
            # 📁 ตั้งค่า Path ให้แยกเป็นวันที่: attendance/YYYY-MM-DD/StudentID
            # การทำแบบนี้จะทำให้ข้อมูลถูกแยกกลุ่มตามวันที่โดยอัตโนมัติค่ะ
            ref = db.reference(f'attendance/{date_str}/{student_id}')
            
            ref.set({
                'name': row['Name'],
                'class': row['Class'],
                'time': row['Time']
            })

        update_sent_count(file_path, total_rows)
        print("✅ อัปเดตข้อมูลขึ้น Firebase เรียบร้อยแล้วค่ะ!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # ระบุชื่อไฟล์ CSV ของเธอ
    file_name = "attendance_2026-01-14.csv"
    upload_to_firebase(file_name)