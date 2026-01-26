import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // เพิ่มบรรทัดนี้ลงไปครับ (สำคัญมาก!)
  // เปลี่ยน 'ชื่อ-repository-ของคุณ' เป็นชื่อ repo ที่คุณจะตั้งใน GitHub นะครับ 
  // เช่น ถ้าตั้งชื่อ repo ว่า attendance-web ก็ใส่ '/attendance-web/'
  base: '/sign-in-facescan/',
})