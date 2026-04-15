# Trees4All Command Center - System Controller: Chayapol Promsavana
# Specialized Assistant: Antigravity AI
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
import sys
import database
import threading
from collections import deque

app = FastAPI(title="Trees4All Command Center")

database.init_db()

# สร้างโฟลเดอร์สำหรับ Static Files (HTML/CSS)
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ตัวแปรเก็บ Process ของบอท
bot_process = None
bot_logs = deque(maxlen=200)

def read_bot_output(process):
    try:
        # read loop
        for line in iter(process.stdout.readline, ''):
            if line:
                bot_logs.append(line.strip())
    except Exception:
        pass

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

@app.post("/api/accounts/{acc_id}/requeue")
async def requeue_account(acc_id: int):
    database.requeue_account(acc_id)
    return {"message": "Account requeued to pending"}

@app.post("/api/accounts/{acc_id}/move_to_top")
async def move_account_to_top(acc_id: int):
    database.move_to_top(acc_id)
    return {"message": "Account moved to top of queue"}

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

@app.get("/api/accounts/{acc_id}/speed")
async def get_speed(acc_id: int):
    return database.get_speed_stats(acc_id)

@app.get("/api/global_speed")
async def get_global_speed_endpoint():
    return database.get_global_speed()

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
    
    database.update_setting("bot_stop_requested", "false")
    database.update_setting("bot_paused", "false")
    
    # รันบอทผ่าน subprocess (ใช้ -u เพื่อให้ Log แสดงผลแบบ Real-time)
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        bot_process = subprocess.Popen(
            [sys.executable, "-u", "trees_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        bot_logs.clear()
        threading.Thread(target=read_bot_output, args=(bot_process,), daemon=True).start()
        
        return {"status": "started", "message": "Bot started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        sett = database.get_settings()
        if sett.get("bot_stop_requested") == "true":
            # Force kill if clicked again
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(bot_process.pid)])
            else:
                os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
            bot_process = None
            database.update_setting("bot_stop_requested", "false")
            return {"message": "Bot force stopped!"}
        else:
            database.update_setting("bot_stop_requested", "true")
            # Unpause if paused so it can break the loop and exit
            if sett.get("bot_paused") == "true":
                database.update_setting("bot_paused", "false")
            return {"message": "Graceful Stop (รอจนจบต้นนี้) กดอีกครั้งถ้าต้องการบังคับปิด (Force)!"}
    return {"message": "Bot is not running"}

@app.get("/api/bot/status")
async def get_bot_status():
    global bot_process
    is_running = bot_process and bot_process.poll() is None
    sett = database.get_settings()
    is_paused = sett.get("bot_paused") == "true"
    return {
        "is_running": is_running,
        "is_paused": is_paused,
        "current_phone": sett.get("bot_current_phone", "")
    }

@app.post("/api/bot/pause")
async def pause_bot():
    database.update_setting("bot_paused", "true")
    return {"message": "Bot paused"}

@app.post("/api/bot/resume")
async def resume_bot():
    database.update_setting("bot_paused", "false")
    return {"message": "Bot resumed"}

@app.get("/api/bot/logs")
async def get_bot_logs():
    return {"logs": list(bot_logs)}

@app.post("/api/bot/retry")
async def retry_statuses():
    database.retry_error_status()
    return {"message": "Error accounts reset to pending"}



@app.post("/api/bot/check")
async def check_bot(phones: List[str] = Form(...)):
    global bot_process
    if bot_process and bot_process.poll() is None:
        return {"status": "already_running", "message": "Bot is already running"}
    
    database.update_setting("bot_stop_requested", "false")
    database.update_setting("bot_paused", "false")
    
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        
        cmd = [sys.executable, "-u", "tree_checker.py"]
        if phones:
            cmd.extend(["--phones"] + phones)

        bot_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        bot_logs.clear()
        threading.Thread(target=read_bot_output, args=(bot_process,), daemon=True).start()
        
        return {"status": "started", "message": "Checker started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
