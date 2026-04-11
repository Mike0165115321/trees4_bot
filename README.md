# Trees4All Command Center 🌳🚀
**The Ultimate Scale-Up Automation Dashboard**

ระบบบอทกรอกข้อมูล Trees4All เวอร์ชัน 6 ที่เปลี่ยนจาก Script ธรรมดาไปเป็น **Professional Command Center** เต็มรูปแบบ จัดการทุกอย่างผ่านฐานข้อมูล SQLite และหน้าเว็บ UI ที่สวยงาม

## 🌟 ฟีเจอร์เด่น
- **All-in-One Dashboard**: จัดการรายชื่อเกษตรกรและค่าตั้งค่าทั้งหมดผ่านหน้าจอเดียว
- **Start/Stop Bot UI**: สั่งรันบอทและหยุดบอทได้จากหน้าเว็บ ไม่ต้องใช้ Terminal
- **Global Settings Management**: ปรับสัดส่วนคะแนนสุขภาพ (80/15/5) และเปิด-ปิดโหมดเบื้องหลัง (Headless) ได้ทันที
- **Single Source of Truth**: ข้อมูลทุกอย่างถูกเก็บไว้ใน `trees_bot.db` เพื่อความปลอดภัยและเสถียรภาพสูงสุด
- **Real-time Monitoring**: ดูจำนวนต้นที่กรอกสำเร็จและข้อผิดพลาดได้แบบสดๆ

## 🛠️ โครงสร้างไฟล์ใหม่
- `app.py`: Backend (FastAPI) สำหรับเสิร์ฟหน้าเว็บและควบคุมบอท
- `trees_bot.py`: ตัวบอทหลัก (Playwright) ที่เชื่อมต่อกับฐานข้อมูล
- `database.py`: ตัวจัดการฐานข้อมูล SQLite (Table accounts และ settings)
- `static/`: ไฟล์ Frontend (HTML, CSS, JS)
- `trees_bot.db`: หัวใจหลักของระบบที่เก็บข้อมูลทุกอย่าง

## 🚀 วิธีเริ่มต้นใช้งาน
1. **รันเซิร์ฟเวอร์หลัก**:
   ```bash
   python app.py
   ```
2. **เข้าใช้งาน**: เปิด Browser ไปที่ `http://localhost:8000`
3. **จัดการคิว**: เพิ่มรายชื่อเกษตรกรในหน้า Queue Management
4. **ตั้งค่า**: ปรับค่าสุขภาพที่ต้องการในเมนู Global Settings และกด Save
5. **เริ่มงาน**: กดปุ่ม **"Start Bot 🚀"** แล้วไปจิบกาแฟรอได้เลยครับ!

---
*Developed with ❤️ and AI for a Greener World.*
