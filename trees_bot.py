import sys
import asyncio
import random
import time
import re
import csv
import os
from playwright.async_api import async_playwright

"""
Trees4All Bot v6 — Final Complete Flow (Queue System Edition)
============================================================
Flow:
  1. โหลดคิวจาก queue.csv
  2. วนลูปรายบัญชี (pending):
     a. Login
     b. เลือกต้นไม้ในลิสต์
     c. บันทึกข้อมูล
     d. ยืนยัน
  3. อัปเดตสถานะใน queue.csv เป็น done
"""
from database import get_pending_accounts, update_status, get_settings

def load_bot_settings():
    """โหลดตั้งค่าจาก Database"""
    raw = get_settings()
    
    pct3 = float(raw.get("health_3", 80))
    pct2 = float(raw.get("health_2", 15))
    pct1 = float(raw.get("health_1", 5))
    headless = raw.get("headless", "false").lower() == "true"

    t = pct3 + pct2 + pct1
    weights = {
        "3 สุขภาพดี": pct3 / t,
        "2 ปานกลาง":  pct2 / t,
        "1 แย่":       pct1 / t,
    }
    
    print("\n" + "= "*55)
    print("  (Tree)  Trees4All Bot v6 (Full Database Mode)")
    print("= "*55)
    print(f"  [Config] โหลดค่าสุขภาพ: 3={pct3:.0f}%  2={pct2:.0f}%  1={pct1:.0f}%")
    print(f"  [Config] Headless: {headless}")
    print("-------------------------------------------------------")
    
    return dict(weights=weights, headless=headless)

def _float(prompt, default):
    try:
        return float(input(prompt).strip())
    except:
        return float(default)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
#  Helpers
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

def pick_health(weights: dict) -> str:
    r = random.random()
    cum = 0.0
    for label, w in weights.items():
        cum += w
        if r <= cum:
            return label
    return list(weights.keys())[1]

async def inter_tree_delay():
    """ซูเปอร์สปีด ระหว่างต้น → จัดเต็มตามความเร็วเว็บ"""
    await asyncio.sleep(random.uniform(0.3, 0.5))

async def batch_pause(filled: int):
    # ปิดการพักถาวรตามคำขอ
    pass

async def safe_wait(page, timeout=10000):
    """wait_for_load_state('networkidle') พร้อม timeout fallback"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        pass  # ถ้า timeout → ไปต่อเลย ไม่ค้าง

async def click_btn(page, texts: list, timeout=5000, force=False):
    """คลิกปุ่มจาก list ข้อความ — ลองทีละอัน"""
    for text in texts:
        btn = page.locator(f"button:has-text('{text}')").first
        try:
            await btn.wait_for(state="visible", timeout=timeout)
            await btn.click(force=force)
            return True
        except:
            continue
    return False

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
#  Steps
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

async def step_login(page, phone, password):
    print(f"    → Login {phone} ...")
    await page.goto("https://trees4allthailand.org/login")
    await page.wait_for_load_state("networkidle")

    await page.locator(
        "input[type='tel'], input[type='text'], "
        "input[placeholder*='เบอร์'], input[name*='phone'], input[name*='username']"
    ).first.fill(phone)
    await asyncio.sleep(random.uniform(0.6, 1.2))

    await page.locator("input[type='password']").first.fill(password)
    await asyncio.sleep(random.uniform(0.5, 1.0))

    await click_btn(page, ["เข้าสู่ระบบ", "Login"])
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    if "login" in page.url.lower():
        raise Exception("Login ไม่สำเร็จ — ตรวจสอบเบอร์/รหัสผ่าน")

async def step_recorder_page(page, recorder, surveyor):
    """หน้า 'ใส่รายละเอียดผู้บันทึก'"""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    if not await page.locator("text=ผู้จดบันทึก").count():
        return  # ไม่มีหน้านี้

    async def fill_chip_autocomplete(label_text: str, value: str):
        slot = page.locator(f".v-input:has(.v-label:has-text('{label_text}')) .v-input__slot").first
        await slot.click()
        await asyncio.sleep(0.6)
        inp = page.locator(f".v-input:has(.v-label:has-text('{label_text}')) input").first
        await inp.fill(value)
        await asyncio.sleep(0.8)
        opt = page.locator(".v-list-item:visible, .v-list__tile:visible").first
        if await opt.count() > 0:
            await opt.click()
        await asyncio.sleep(0.5)

    await fill_chip_autocomplete("ผู้จดบันทึก", recorder)
    await fill_chip_autocomplete("ผู้สำรวจ", surveyor)

    try:
        await page.locator("text=ใส่รายละเอียดผู้บันทึก").first.click(timeout=2000)
    except:
        await page.mouse.click(10, 10)

    await click_btn(page, ["ต่อไป", "Next", "ยืนยัน", "บันทึก"], force=True)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1.5)

async def step_enter_tree_code(page) -> str:
    """หน้า 'เลือกต้นไม้'"""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    list_tab = page.locator("text=/ยังไม่ได้(กรอก|บันทึก)/").first
    if await list_tab.count() > 0:
        try:
            await list_tab.scroll_into_view_if_needed()
            await list_tab.click(force=True, timeout=3000)
            await asyncio.sleep(1.0)
        except:
            pass

    all_chips = page.locator(".v-chip:visible, .v-btn--chip:visible")
    count = await all_chips.count()
    code_pattern = re.compile(r"^\d{5,}$")
    
    for i in range(count):
        chip = all_chips.nth(i)
        try:
            raw = (await chip.inner_text()).strip().replace("\n", "").replace(" ", "")
            if code_pattern.match(raw):
                await chip.scroll_into_view_if_needed()
                await chip.click(force=True)
                await asyncio.sleep(0.5)
                await click_btn(page, ["ต่อไป", "Next", "ยืนยัน", "ตกลง"], force=True)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)
                return raw
        except:
            continue
    return ""

async def step_tree_detail(page, weights: dict, seq: int) -> bool:
    """หน้า 'บันทึกรายละเอียดต้นไม้'"""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.5)

    heading = page.locator("h1:has-text('บันทึกรายละเอียด'), h2:has-text('บันทึกรายละเอียด')")
    if await heading.count() == 0:
        return False

    filled = []
    # -- ชนิด --
    species_input = page.locator(".v-input:has(.v-label:has-text('ชนิด'))").first
    if await species_input.count() > 0:
        chip = species_input.locator(".v-chip")
        if await chip.count() > 0:
            val = (await chip.first.inner_text()).strip()
            filled.append(f"ชนิด={val}")
        else:
            for _try in range(3):
                await species_input.locator(".v-input__slot").click(force=True)
                await asyncio.sleep(0.5)
                first_opt = page.locator(".v-list-item:visible").first
                if await first_opt.count() > 0:
                    try:
                        opt_name = (await first_opt.inner_text()).strip().split('\n')[0]
                        await first_opt.click(force=True)
                        filled.append(f"ชนิด={opt_name}")
                        break
                    except:
                        continue
    # -- สุขภาพ --
    health = page.locator(".v-input:has(.v-label:has-text('สุขภาพ'))").first
    if await health.count() > 0:
        score = pick_health(weights)
        await health.scroll_into_view_if_needed()
        await health.locator(".v-input__slot").click()
        await asyncio.sleep(0.5)
        opt = page.locator(f".v-list-item:has-text('{score.split()[0]}'):visible").first
        if await opt.count() > 0:
            await opt.click(force=True)
        filled.append(f"สุขภาพ={score}")

    await click_btn(page, ["ต่อไป", "Next"], force=True)
    await page.wait_for_load_state("networkidle")
    return True

async def step_confirm_page(page, seq: int, is_last: bool) -> bool:
    """หน้า 'ตรวจสอบข้อมูล'"""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.8)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    if is_last:
        await click_btn(page, ["เสร็จสิ้น", "Finish"], force=True)
    else:
        await click_btn(page, ["บันทึกและไปต้นต่อไป", "บันทึกและไปต้นถัดไป"], force=True)

    await page.wait_for_load_state("networkidle")
    return True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
#  Main Queue Processor
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

async def process_single_account(p, acc: dict, global_cfg: dict):
    stats = {"filled": 0, "error": 0}
    start = time.time()
    phone = acc['phone']

    print(f"\n" + "═"*55)
    print(f" [Queue] กำลังทำ: {phone} | {acc['recorder']}")
    print("═"*55)

    browser = await p.chromium.launch(headless=global_cfg["headless"])
    page = await (await browser.new_context()).new_page()

    try:
        await step_login(page, acc["phone"], acc["password"])
        await page.goto("https://trees4allthailand.org/farmer")
        await page.wait_for_load_state("networkidle")
        
        start_btn = page.locator("text=เริ่มบันทึกผลต้นไม้").first
        if await start_btn.count() > 0:
            await start_btn.click()
        else:
            await page.goto("https://trees4allthailand.org/farmer/tracking")
        
        await step_recorder_page(page, acc["recorder"], acc["surveyor"])

        while True:
            code_text = await step_enter_tree_code(page)
            if not code_text: break
            
            if await step_tree_detail(page, global_cfg["weights"], stats["filled"]+1):
                await step_confirm_page(page, stats["filled"]+1, is_last=False)
                stats["filled"] += 1
                print(f"    [OK] ต้นที่ {stats['filled']}: {code_text}")
                await inter_tree_delay()
            else:
                stats["error"] += 1
                await page.goto("https://trees4allthailand.org/farmer/tracking")

        update_status(phone, "done")
        print(f"\n  (Check) บัญชี {phone} สำเร็จ: {stats['filled']} ต้น")

    except Exception as e:
        print(f"    [Error] {phone} ล้มเหลว: {e}")
        update_status(phone, "error")
    finally:
        await browser.close()
    
    return stats

async def run_bot(global_cfg: dict):
    accounts = get_pending_accounts()
    
    if not accounts:
        print("\n  (!) ไม่พบคิวผู้ใช้ที่ต้องทำงาน (สถานะ pending)")
        return

    print(f"\n  [Bot] พบคิวที่รอดำเนินการ {len(accounts)} คน")
    
    async with async_playwright() as p:
        for acc in accounts:
            await process_single_account(p, acc, global_cfg)
            await asyncio.sleep(2)

def main():
    if sys.stdout.encoding != 'utf-8':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass
    
    global_cfg = load_bot_settings()
    asyncio.run(run_bot(global_cfg))

if __name__ == "__main__":
    main()
