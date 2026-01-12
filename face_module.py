import cv2
import numpy as np
import pickle
from insightface.app import FaceAnalysis
from PIL import ImageFont, ImageDraw, Image

class FaceScanner:
    def __init__(self):
        # --- ตั้งค่า Configuration ---
        self.DATABASE_PATH = 'database/faces_data.pkl'
        self.MODEL_NAME = 'buffalo_l'
        self.SIMILARITY_THRESHOLD = 0.40
        self.FONT_PATH = "c:\\WINDOWS\\Fonts\\UPCJB.TTF"
        
        # ข้อมูลจำลอง (Mockup)
        self.STUDENT_DB = {
            "61": "นายพงศธร ชาลีโสม",
            "66010002": "น.ส.สมศรี เรียนเก่ง",
            "66010003": "ชิอิเนะ มาฮิรุ",
            "12345": "แอดมิน ทดสอบระบบ"
        }

        self.known_embeds = []
        self.known_names = []
        self.app = None
        
        # เริ่มโหลดระบบทันทีที่สร้าง Class
        self.load_resources()

    def load_resources(self):
        print("⚙️ กำลังโหลด Database...")
        try:
            with open(self.DATABASE_PATH, 'rb') as f:
                data = pickle.load(f)
                self.known_embeds = np.array(data['embeddings'])
                self.known_names = data['names']
            print(f"✅ โหลด Database เรียบร้อย: {len(self.known_names)} คน")
        except Exception as e:
            print(f"⚠️ Warning: โหลด Database ไม่ได้ ({e}) ระบบจะทำงานแต่จำหน้าไม่ได้")

        print(f"⚙️ กำลังเตรียมโมเดล {self.MODEL_NAME}...")
        self.app = FaceAnalysis(name=self.MODEL_NAME, providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        print("🚀 ระบบ AI พร้อมทำงาน!")

    def put_thai_text(self, img, text, position, color, font_size):
        """วาดภาษาไทยลงบนภาพ"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        try:
            font = ImageFont.truetype(self.FONT_PATH, font_size)
        except IOError:
            font = ImageFont.load_default()
        
        draw.text(position, text, font=font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def process_frame(self, frame):
        """รับภาพเข้ามา -> สแกนหน้า -> วาดกรอบ -> ส่งภาพกลับ"""
        faces = self.app.get(frame)
        
        for face in faces:
            # 1. เปรียบเทียบหน้า
            current_emb = face.embedding
            current_emb = current_emb / np.linalg.norm(current_emb)
            scores = np.dot(self.known_embeds, current_emb)
            best_idx = np.argmax(scores)
            best_score = scores[best_idx]
            
            # 2. ตัดสินใจว่าเป็นใคร
            if best_score > self.SIMILARITY_THRESHOLD:
                student_id = self.known_names[best_idx]
                real_name = self.STUDENT_DB.get(student_id, student_id)
                text_color = (0, 255, 0) # เขียว
                display_text = real_name
            else:
                text_color = (255, 0, 0) # แดง
                display_text = "ไม่พบข้อมูล"

            # 3. วาดกรอบและชื่อ
            box = face.bbox.astype(int)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), text_color[::-1], 3)
            
            # พื้นหลังป้ายชื่อ
            cv2.rectangle(frame, (box[0], box[1]-50), (box[0]+250, box[1]), text_color[::-1], -1)
            
            # เขียนชื่อไทย
            frame = self.put_thai_text(frame, display_text, (box[0]+10, box[1]-45), (255, 255, 255), 30)

        return frame