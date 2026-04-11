import sys
import asyncio
import random
import time
import re
from playwright.async_api import async_playwright

"""
Trees4All Bot v6 — Final Complete Flow
========================================
Flow จริง (จาก screenshots):
  1. Login
  2. หน้าผู้จดบันทึก + ผู้สำรวจ (ครั้งแรกครั้งเดียว)
  3. LOOP:
     a. หน้ากรอกรหัสต้นไม้ (prefix 3 ตัว + running 001-240)
     b. หน้าบันทึกรายละเอียด (ชนิด + สุขภาพ + เพิ่มเติม)
     c. หน้าตรวจสอบข้อมูล → กด "บันทึกและไปต้นต่อไป"
"""
CONFIG_FILE = "config.txt"

def load_config_file() -> dict:
    """อ่านค่าจาก config.txt — คืน dict หรือ None ถ้าไม่มีไฟล์"""
    try:
        cfg = {}
        with open(CONFIG_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    cfg[key.strip()] = val.strip()
        return cfg
    except FileNotFoundError:
        return None

def ask_config():
    print("\n" + "= "*55)
    print("  (Tree)  Trees4All Bot v6 (Ultra-Autonomous)")
    print("= "*55)

    raw = load_config_file()

    if raw:
        # -- โหลดจากไฟล์ config.txt --
        print(f"\n  (Config) โหลดตั้งค่าจาก {CONFIG_FILE} สำเร็จ")
        phone    = raw.get("phone", "")
        password = raw.get("password", "")
        recorder = raw.get("recorder", "ชยพล พรมสะวะนา")
        surveyor = raw.get("surveyor", "กรรณิการ์ คำนาน")
        pct3 = float(raw.get("health_3", 80))
        pct2 = float(raw.get("health_2", 15))
        pct1 = float(raw.get("health_1", 5))
    else:
        # -- ถามแบบ interactive เหมือนเดิม ถ้าไม่มีไฟล์ --
        print(f"\n  (!)  ไม่พบ {CONFIG_FILE} — ถามแบบ interactive แทน")
        phone    = input("\n  เบอร์โทร / รหัสเกษตรกร     : ").strip()
        password = input("  รหัสผ่าน                   : ").strip()

        print("\n  -- ข้อมูลผู้บันทึก (ถามครั้งแรกครั้งเดียว) --")
        recorder = input("  ชื่อผู้จดบันทึก (ชยพล พรมสะวะนา) : ").strip() or "ชยพล พรมสะวะนา"
        surveyor = input("  ชื่อผู้สำรวจ (กรรณิการ์ คำนาน) : ").strip() or "กรรณิการ์ คำนาน"

        print("\n  -- สัดส่วนคะแนนสุขภาพ (รวม = 100) --")
        pct3 = _float("  คะแนน 3 (สุขภาพดี)   %    : ", 80)
        pct2 = _float("  คะแนน 2 (ปานกลาง)   %    : ", 15)
        pct1 = _float("  คะแนน 1 (แย่)        %    : ",  5)

    t = pct3 + pct2 + pct1
    weights = {
        "3 สุขภาพดี": pct3 / t,
        "2 ปานกลาง":  pct2 / t,
        "1 แย่":       pct1 / t,
    }

    print("\n-------------------------------------------------------")
    print(f"  ผู้จดบันทึก  : {recorder}")
    print(f"  ผู้สำรวจ     : {surveyor}")
    print(f"  สุขภาพ       : 3={pct3:.0f}%  2={pct2:.0f}%  1={pct1:.0f}%")
    print("  เป้าหมาย     : ทุกต้นในรายการ (Process All Mode)")
    print("-------------------------------------------------------")

    ok = input("  ยืนยันเริ่มรัน? (y/n)        : ").strip().lower()
    if ok != "y":
        print("  ยกเลิก")
        exit()

    return dict(
        phone=phone, password=password,
        recorder=recorder, surveyor=surveyor,
        weights=weights,
        headless=(raw.get("headless", "false").lower() == "true")
    )

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
    print(f"\n  → Login {phone} ...")
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
    print("  [OK] Login สำเร็จ")


async def step_recorder_page(page, recorder, surveyor):
    """
    หน้า 'ใส่รายละเอียดผู้บันทึก' — ทำครั้งแรกครั้งเดียว
    ถ้าไม่มีหน้านี้ → ข้ามทันที
    """
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    if not await page.locator("text=ผู้จดบันทึก").count():
        return  # ไม่มีหน้านี้

    print("    → กรอกผู้จดบันทึก/ผู้สำรวจ")

    async def fill_chip_autocomplete(label_text: str, value: str):
        # คลิก slot เพื่อ activate
        slot = page.locator(
            f".v-input:has(.v-label:has-text('{label_text}')) .v-input__slot"
        ).first
        await slot.click()
        await asyncio.sleep(0.6)
        # พิมพ์ชื่อ
        inp = page.locator(
            f".v-input:has(.v-label:has-text('{label_text}')) input"
        ).first
        await inp.fill(value)
        await asyncio.sleep(0.8)
        # เลือก option แรกที่ขึ้นมา
        opt = page.locator(".v-list-item:visible, .v-list__tile:visible").first
        if await opt.count() > 0:
            await opt.click()
        await asyncio.sleep(0.5)

    await fill_chip_autocomplete("ผู้จดบันทึก", recorder)
    await fill_chip_autocomplete("ผู้สำรวจ", surveyor)

    # คลิกที่ว่างเพื่อให้ปุ่ม ต่อไป ทำงาน (แก้ปัญหาปุ่มกดไม่ได้ถ้าไม่คลิกที่อื่นก่อน)
    try:
        await page.locator("text=ใส่รายละเอียดผู้บันทึก").first.click(timeout=2000)
    except:
        await page.mouse.click(10, 10) # fallback คลิกมุมบนซ้าย

    await click_btn(page, ["ต่อไป", "Next", "ยืนยัน", "บันทึก"], force=True)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1.5)
    print("    [OK] ผ่านหน้าผู้บันทึก")


async def step_enter_tree_code(page) -> str:
    """
    หน้า 'เลือกต้นไม้'
    - วิธีออโต้: กด 'ยังไม่ได้...' (ถ้าปิดอยู่) แล้วจิ้มต้นบนสุด (Chip รหัส 6+ หลัก)
    Return: รหัสต้นไม้ (string) หรือ "" ถ้าไม่มีของให้ทำแล้ว
    """
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # 1. กด/กางแถบ "ยังไม่ได้..." ถ้ามี
    list_tab = page.locator("text=/ยังไม่ได้(กรอก|บันทึก)/").first
    if await list_tab.count() > 0:
        try:
            await list_tab.scroll_into_view_if_needed()
            await list_tab.click(force=True, timeout=3000)
            await asyncio.sleep(1.0)
        except:
            pass

    # 2. หา Chip ที่มีรหัสต้นไม้
    # รหัสต้นไม้ มักเป็นตัวเลขล้วน ≥ 5 หลัก (เช่น 104005)
    # กรองออกโดยใช้ regex ตรวจสอบ text ของแต่ละ chip
    all_chips = page.locator(".v-chip:visible, .v-btn--chip:visible")
    count = await all_chips.count()

    code_text = ""
    first_item = None

    # วน loop หาอันแรกที่ text เป็นตัวเลขล้วน ≥ 5 หลัก
    code_pattern = re.compile(r"^\d{5,}$")
    for i in range(count):
        chip = all_chips.nth(i)
        try:
            raw = (await chip.inner_text()).strip().replace("\n", "").replace(" ", "")
            if code_pattern.match(raw):
                first_item = chip
                code_text = raw
                break
        except:
            continue

    if first_item:
        print(f"    → เลือกต้นที่พบ: {code_text}")
        await first_item.scroll_into_view_if_needed()
        await first_item.click(force=True)
        await asyncio.sleep(0.5)

        # กด 'ต่อไป' เพื่อเข้าหน้ากรอกข้อมูล
        await click_btn(page, ["ต่อไป", "Next", "ยืนยัน", "ตกลง"], force=True)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        return code_text

    print("    (!)  ไม่พบ Chip รหัสต้นไม้ — อาจเสร็จแล้วหรือโหลดไม่ทัน")
    return ""


async def step_tree_detail(page, weights: dict, seq: int) -> bool:
    """
    หน้า 'บันทึกรายละเอียดต้นไม้'
    - ชนิดต้นไม้: ถ้ามีอยู่แล้วให้ใช้เลย ถ้าว่างให้เลือกอันแรกสุดจากลิส
    - สุขภาพ: สุ่มตามน้ำหนัก
    """
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.5)

    # เช็คว่าอยู่หน้ากรอกรายละเอียด
    heading = page.locator("h1:has-text('บันทึกรายละเอียด'), h2:has-text('บันทึกรายละเอียด')")
    if await heading.count() == 0:
        print(f"    [Error] ต้น {seq}: ไม่พบหน้าบันทึกรายละเอียด (URL={page.url})")
        return False

    filled = []

    # -- ชนิดต้นไม้ --
    species_input = page.locator(".v-input:has(.v-label:has-text('ชนิด'))").first
    if await species_input.count() > 0:
        chip = species_input.locator(".v-chip")
        
        if await chip.count() > 0:
            val = (await chip.first.inner_text()).strip()
            print(f"    [OK] ใช้ชนิดต้นไม้เดิม: {val}")
            filled.append(f"ชนิด={val}")
        else:
            # ถ้าว่าง ให้เปิดลิสแล้วจิ้มอันแรก (retry 3 รอบเผื่อ dropdown ช้า)
            print("    → ช่องชนิดต้นไม้วางอยู่ กำลังเลือกอันแรกสุดในระบบ...")
            opted = False
            for _try in range(3):
                await species_input.locator(".v-input__slot").click(force=True)
                await asyncio.sleep(0.5)  # รอ dropdown โหลด
                # หา parent .v-list-item ที่ visible จริง แล้วค่อย click
                first_opt = page.locator(".v-list-item:visible").first
                if await first_opt.count() > 0:
                    try:
                        opt_name = (await first_opt.inner_text()).strip().split('\n')[0]
                        await first_opt.click(force=True)
                        print(f"    [OK] เลือกชนิด: {opt_name}")
                        filled.append(f"ชนิด={opt_name}")
                        opted = True
                        break
                    except:
                        await asyncio.sleep(0.5)
                        continue
            if not opted:
                print("    (!)  เลือกชนิดต้นไม้ไม่ได้ — ข้ามไปก่อนครับ")
            await asyncio.sleep(0.3)

    # -- สุขภาพต้นกล้า --
    health = page.locator(".v-input:has(.v-label:has-text('สุขภาพ'))").first
    if await health.count() > 0:
        score = pick_health(weights)
        await health.scroll_into_view_if_needed()
        await health.locator(".v-input__slot").click()
        await asyncio.sleep(0.5)

        opt = None
        for pattern in [score, score.split()[0]]:
            candidate = page.locator(
                f".v-list-item:has-text('{pattern}'):visible, "
                f".v-list__tile:has-text('{pattern}'):visible"
            ).first
            if await candidate.count() > 0:
                opt = candidate
                break

        if opt:
            try:
                await opt.click(timeout=3000)
            except:
                await opt.click(force=True)
        filled.append(f"สุขภาพ={score}")
        await asyncio.sleep(0.3)

    # -- กด ต่อไป --
    await click_btn(page, ["ต่อไป", "Next"], force=True)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.5)

    print(f"    → {', '.join(filled)}")
    return True


async def step_confirm_page(page, seq: int, is_last: bool) -> bool:
    """
    หน้า 'ตรวจสอบข้อมูล'
    - ถ้าไม่ใช่ต้นสุดท้าย → กด 'บันทึกและไปต้นต่อไป'
    - ถ้าเป็นต้นสุดท้าย → กด 'เสร็จสิ้น'
    """
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.8)

    # เลื่อนลงมาให้เห็นปุ่ม
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(0.5)

    heading = page.locator("h1:has-text('ตรวจสอบ'), h2:has-text('ตรวจสอบ')")
    if await heading.count() == 0:
        # อาจ submit ผ่านไปแล้ว ถือว่าสำเร็จ
        print(f"    [OK] ต้น {seq}: บันทึกแล้ว")
        return True

    if is_last:
        clicked = await click_btn(page, ["เสร็จสิ้น", "Finish"], force=True)
    else:
        # เน้นปุ่มนี้ตามภาพที่คุณส่งมา
        clicked = await click_btn(page, ["บันทึกและไปต้นต่อไป", "บันทึกและไปต้นถัดไป"], force=True)

    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.2)
    print(f"    [OK] ต้น {seq}: บันทึกสำเร็จ {'(เสร็จสิ้น)' if is_last else ''}")
    return True


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
#  Main Loop
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

async def run_bot(cfg: dict):
    stats = {"filled": 0, "skipped": 0, "error": 0}
    start = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=cfg.get("headless", False))
        page    = await (await browser.new_context()).new_page()

        try:
            # -- 1. Login --
            await step_login(page, cfg["phone"], cfg["password"])

            # -- 2. ไปหน้า farmer → กด "เริ่มบันทึกผลต้นไม้" --
            await page.goto("https://trees4allthailand.org/farmer")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # กดปุ่ม "เริ่มบันทึกผลต้นไม้" เพื่อเข้าหน้า tracking
            start_btn = page.locator("text=เริ่มบันทึกผลต้นไม้").first
            if await start_btn.count() > 0:
                await start_btn.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                print("  [OK] เข้าหน้าบันทึกผลต้นไม้")
            else:
                # fallback: ไปตรงที่ URL เลย
                await page.goto("https://trees4allthailand.org/farmer/tracking")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                print("  [OK] ไปหน้า tracking โดยตรง")

            # -- 3. หน้าผู้บันทึก (ครั้งแรกครั้งเดียว) --
            await step_recorder_page(page, cfg["recorder"], cfg["surveyor"])

            print("  [OK] เริ่มรันแบบ Autonomous Mode")
            print("-" * 55)

            # -- 4. LOOP (Process All) --
            while True:
                seq = stats["filled"] + 1

                try:
                    # a. เลือกต้นไม้ต้นบนสุดที่ยังไม่กรอก
                    code_text = await step_enter_tree_code(page)
                    if not code_text:
                        print("\n  (Done) เรียบร้อย! ไม่เหลือต้นไม้ที่ยังไม่ได้กรอกในลิสแล้ว")
                        break
                    
                    print(f"\n  [{seq}] กำลังบันทึก: {code_text}")

                    # b. บันทึกรายละเอียด
                    ok_detail = await step_tree_detail(page, cfg["weights"], seq)
                    if not ok_detail:
                        stats["error"] += 1
                        # กลับหน้าหลักใหม่เผื่อค้าง
                        await page.goto("https://trees4allthailand.org/farmer/tracking")
                        await asyncio.sleep(1.5)
                        continue

                    # c. ตรวจสอบและยืนยัน
                    await step_confirm_page(page, seq, is_last=False)

                    stats["filled"] += 1
                    await inter_tree_delay()

                except Exception as e:
                    print(f"    [Error] error: {e}")
                    stats["error"] += 1
                    try:
                        await page.goto("https://trees4allthailand.org/farmer/tracking")
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)  # รอให้หน้าโหลดพร้อม + Chip ขึ้นมา
                    except:
                        pass

            # -- สรุป --
            elapsed = time.time() - start
            rate = stats["filled"] / (elapsed / 60) if elapsed > 0 else 0
            print("\n" + "= " * 55)
            print(f"  [OK] กรอกสำเร็จ  : {stats['filled']} ต้น")
            print(f"  [Error] error        : {stats['error']} ต้น")
            print(f"  (Time) เวลา         : {elapsed/60:.1f} นาที ({rate:.1f} ต้น/นาที)")
            print("= " * 55)

        finally:
            input("\n  กด Enter เพื่อปิด browser...")
            await browser.close()


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
#  Entry Point
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass
    cfg = ask_config()
    asyncio.run(run_bot(cfg))
