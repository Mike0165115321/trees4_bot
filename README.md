# 🌳 Trees4All Command Center [Private Edition] 🚀
### **Version 1.0.0 | High-Performance Automation Suite**

![TreesBot Banner](https://img.shields.io/badge/Status-Deployed-success?style=for-the-badge&logo=github)
![Build](https://img.shields.io/badge/Build-Professional_EXE-blue?style=for-the-badge&logo=windows)
![Developer](https://img.shields.io/badge/Developer-Chayapol_Promsavana-orange?style=for-the-badge)

---

## 🌟 Mission Statement
> "Solving complex, large-scale automation challenges with surgical precision and premium user experience."

**Trees4All Command Center** คือโซลูชันการจัดการและปลูกต้นไม้อัตโนมัติระดับมืออาชีพ ที่ถูกออกแบบมาเพื่อรองรับการทำงานกับบัญชีจำนวนมหาศาล (Scalability) โดยเน้นความง่ายในการใช้งานผ่านระบบ GUI ที่ทันสมัย และความเสถียรสูงสุดในทุกขั้นตอนการรัน

---

## ✨ Key Features (ความสามารถหลัก)

### 📊 **1. Modern Dashboard UI**
- อินเทอร์เฟซสไตล์ Dark Mode ที่ใช้งานง่ายและดูพรีเมียม
- แสดงผลสถิติแบบ Real-time (Total Runs, Success Rate, Progress)
- ระบบจัดการบัญชีที่ยืดหยุ่น (เพิ่ม/ลบ/แก้ไข) ได้ทันทีจากหน้าเว็บ

### 🤖 **2. Intelligent Bot Engine**
- **Automated Planting**: ระบบปลูกต้นไม้อัตโนมัติที่แม่นยำด้วยฐานข้อมุลที่มีประสิทธิภาพ
- **Sequence Management**: รองรับการรันแบบลำดับเลำดับขั้น เพื่อลดความเสี่ยงในการถูกตรวจสอบ
- **Error Handling**: ระบบตรวจจับและแก้ไขปัญหาขณะรันเบื้องต้นโดยอัตโนมัติ

### 🔍 **3. Automatic Tree Checker**
- ระบบตรวจสอบสถานะต้นไม้แบบอัตโนมัติ (Verification Mode)
- สรุปผลลัพธ์ลงฐานข้อมูล เพื่อให้คุณทราบสถานะของทุกบัญชีได้อย่างแม่นยำ

### 📦 **4. Professional Standalone Application**
- **No Console Mode**: รันแอปแบบไร้หน้าต่าง Terminal กวนใจ
- **App Mode**: บราวเซอร์ Dashboard เปิดในหน้าต่างแยกแบบแอปดั้งเดิม (Chromeless Window)
- **One-File Delivery**: ตัวแอปถูกรวมอยู่ในไฟล์ EXE เดียว พกพาและติดตั้งง่าย

---

## 🚀 Quick Start (วิธีใช้งานเบื้องต้น)

### สำหรับผู้ใช้งานทั่วไป (User Mode)
1. เข้าไปที่โฟลเดอร์ `dist/TreesBot_App_v1.0.0`
2. ดับเบิลคลิกไฟล์ **`Create_Shortcut.bat`** เพื่อสร้างทางลัดบนหน้าจอ Desktop
3. เปิดแอปผ่าน Shortcut ที่สร้างขึ้น แดชบอร์ดจะเด้งขึ้นมาในบราวเซอร์ของคุณโดยอัตโนมัติ

---

## 🛠️ Developer Guide (สำหรับนักพัฒนา)

### **การตั้งค่าสภาพแวดล้อม (Environment Setup)**
โปรเจกต์นี้พัฒนาด้วย Python 3.11+ แนะนำให้ใช้ Virtual Environment:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### **ระบบการ Build (Professional Build System)**
เรามีสคริปต์การบิวต์ที่ชาญฉลาดเตรียมไว้ให้แล้ว:
- รันไฟล์ **`build_app.bat`**
- เลือก **Mode 1 (DEV)**: หากต้องการเปิดหน้าต่าง Console เพื่อดู Log
- เลือก **Mode 2 (RELEASE)**: หากต้องการสร้างแอปเวอร์ชันสมบูรณ์ที่ไม่มีหน้าต่าง Console

---

## 📂 Project Structure (โครงสร้างไฟล์)
- `app.py`: ตัวควบคุมระบบ (Master Controller / API Server)
- `trees_bot.py`: สมองกลในการปลูกต้นไม้ (Core Engine)
- `tree_checker.py`: ระบบตรวจสอบสถานะ
- `database.py`: การจัดการฐานข้อมูล SQLite
- `static/`: ไฟล์หน้าเว็บ (HTML, CSS, JS, Assets)
- `TreesBot_Dashboard.spec`: ไฟล์ข้อกำหนดสำหรับการ Bundle แอป

---

## 🛡️ Technology Stack
- **Backend**: FastAPI & Uvicorn
- **Automation**: Playwright (Python)
- **Database**: SQLite 3
- **Frontend**: Vanilla CSS / JavaScript (Premium UI Design)
- **Bundler**: PyInstaller (Dynamic Spec Configuration)

---

## 🏆 Credits
- **Lead Developer**: Chayapol Promsavana (Mike Developer)
- **AI Specialist**: Antigravity (Advanced Coding Agent) 
- **Project Version**: 1.0.0 [Private Edition]

---
*Generated with ❤️ for the TreesBot Community.*
