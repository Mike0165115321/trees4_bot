from fastapi import FastAPI, HTTPException, BackgroundTasks, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import subprocess
import os
import signal
import shutil
import uuid
import database

app = FastAPI(title="Trees4All Command Center")

# สร้างโฟลเดอร์สำหรับ Static Files (HTML/CSS)
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ตัวแปรเก็บ Process ของบอท
bot_process = None

class AccountSchema(BaseModel):
    phone: str
    password: str
    recorder: str
    surveyor: str

class SettingsSchema(BaseModel):
    health_3: int
    health_2: int
    health_1: int
    headless: bool

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/accounts")
async def get_accounts():
    return database.get_all_accounts()

@app.post("/api/accounts")
async def add_account(
    phone: str = Form(...),
    password: str = Form(...),
    recorder: str = Form(""),
    surveyor: str = Form(""),
    images: List[UploadFile] = File([])
):
    account_id = database.add_account(phone, password, recorder, surveyor)
    if not account_id:
        raise HTTPException(status_code=400, detail="Phone number already exists")
    
    # Save images
    for img in images:
        if img.filename:
            ext = os.path.splitext(img.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            file_path = f"static/uploads/{unique_filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            database.add_image(account_id, file_path)

    return {"message": "Account added successfully"}

@app.delete("/api/accounts/{acc_id}")
async def delete_account(acc_id: int):
    database.delete_account(acc_id)
    return {"message": "Account deleted"}

@app.get("/api/accounts/{acc_id}/images")
async def get_account_images(acc_id: int):
    images = database.get_images(acc_id)
    # The file paths in DB are like "static/uploads/file.png". We can return as is.
    return images

@app.post("/api/accounts/{acc_id}/images")
async def add_more_images(acc_id: int, images: List[UploadFile] = File(...)):
    for img in images:
        if img.filename:
            ext = os.path.splitext(img.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            file_path = f"static/uploads/{unique_filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            database.add_image(acc_id, file_path)
    return {"message": "Images added successfully"}

@app.delete("/api/images/{img_id}")
async def delete_image(img_id: int):
    file_path = database.delete_image_by_id(img_id)
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass
    return {"message": "Image deleted"}

@app.get("/api/settings")
async def get_settings():
    return database.get_settings()

@app.post("/api/settings")
async def update_settings(sett: SettingsSchema):
    database.update_setting("health_3", sett.health_3)
    database.update_setting("health_2", sett.health_2)
    database.update_setting("health_1", sett.health_1)
    database.update_setting("headless", "true" if sett.headless else "false")
    return {"message": "Settings updated"}

@app.post("/api/bot/start")
async def start_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        return {"status": "already_running", "message": "Bot is already running"}
    
    # รันบอทผ่าน subprocess
    try:
        # ใช้ python (หรือ python3 ตามระบบ)
        bot_process = subprocess.Popen(
            ["python", "trees_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        return {"status": "started", "message": "Bot started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        if os.name == 'nt':
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(bot_process.pid)])
        else:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        bot_process = None
        return {"message": "Bot stopped"}
    return {"message": "Bot is not running"}

@app.get("/api/bot/status")
async def get_bot_status():
    global bot_process
    is_running = bot_process and bot_process.poll() is None
    return {"is_running": is_running}

@app.post("/api/bot/reset")
async def reset_statuses():
    database.reset_all_status()
    return {"message": "All statuses reset to pending"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
