import sys
import asyncio
import random
import time
import re
import os
from playwright.async_api import async_playwright

"""
Trees4All Bot V1.0.0 — Class-Based Architecture
============================================================
System Controller: Chayapol Promsavana
Specialized Assistant: Antigravity AI
------------------------------------------------------------
Flow:
  1. โหลดคิวจาก SQLite (pending)
  2. วนลูปรายบัญชี:
     Phase 1: Login
     Phase 2: Recorder (ผู้บันทึก/ผู้สำรวจ)
     Phase 3: Tree Loop (เลือกต้น → กรอกข้อมูล → ยืนยัน)
     Phase 4: Image Upload (อัปโหลดรูปภาพ)
  3. อัปเดตสถานะเป็น done
"""

from database import (
    get_pending_accounts, update_status, get_settings, update_setting,
    add_speed_log, get_images, update_image_status
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Section 1: BotConfig
# ═══════════════════════════════════════════════════════════════════════════════

class BotConfig:
    """โหลดและเก็บค่า Settings ทั้งหมดจาก Database"""

    def __init__(self):
        raw = get_settings()
        self.headless = raw.get("headless") == "true"

        print("\n" + "= " * 55)
        print("  (Tree)  Trees4All Bot V1.0.0 (Class-Based Architecture)")
        print("= " * 55)
        print(f"  [Config] Headless: {self.headless}")
        print("-" * 55)


# ═══════════════════════════════════════════════════════════════════════════════
#  Section 2: PageHelper (Shared Utilities)
# ═══════════════════════════════════════════════════════════════════════════════

class PageHelper:
    """Utility methods ที่ทุก Flow ใช้ร่วมกัน"""

    def __init__(self, page):
        self.page = page

    async def click_btn(self, texts: list, timeout=5000, force=False):
        """คลิกปุ่มจาก list ข้อความ — ลองทีละอัน"""
        for text in texts:
            btn = self.page.locator(f"button:has-text('{text}')").first
            try:
                await btn.wait_for(state="visible", timeout=timeout)
                await btn.click(force=force)
                return True
            except:
                continue
        return False

    async def safe_wait(self, timeout=10000):
        """wait_for_load_state('networkidle') พร้อม timeout fallback"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            pass  # ถ้า timeout → ไปต่อเลย ไม่ค้าง

    @staticmethod
    def pick_health(weights: dict) -> str:
        r = random.random()
        cum = 0.0
        for label, w in weights.items():
            cum += w
            if r <= cum:
                return label
        return list(weights.keys())[1]


# ═══════════════════════════════════════════════════════════════════════════════
#  Section 3: Flow Classes
# ═══════════════════════════════════════════════════════════════════════════════

class LoginFlow:
    """Phase 1: ล็อกอินเข้าเว็บ"""

    def __init__(self, helper: PageHelper, phone: str, password: str):
        self.helper = helper
        self.page = helper.page
        self.phone = phone
        self.password = password

    async def execute(self):
        print(f"    → Login {self.phone} ...")
        await self.page.goto("https://trees4allthailand.org/login")
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass

        await self.page.locator(
            "input[type='tel'], input[type='text'], "
            "input[placeholder*='เบอร์'], input[name*='phone'], input[name*='username']"
        ).first.fill(self.phone)
        await asyncio.sleep(random.uniform(0.4, 0.8)) # Quick burst

        await self.page.locator("input[type='password']").first.fill(self.password)
        await asyncio.sleep(random.uniform(0.3, 0.6)) # Quick burst

        await self.helper.click_btn(["เข้าสู่ระบบ", "Login"])
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(random.uniform(1.0, 2.0)) # Scanning/Loading

        if "login" in self.page.url.lower():
            raise Exception("Login ไม่สำเร็จ — ตรวจสอบเบอร์/รหัสผ่าน")


class RecorderFlow:
    """Phase 2: กรอกผู้บันทึก/ผู้สำรวจ"""

    def __init__(self, helper: PageHelper, recorder: str, surveyor: str):
        self.helper = helper
        self.page = helper.page
        self.recorder = recorder
        self.surveyor = surveyor

    async def _fill_chip_autocomplete(self, label_text: str, value: str):
        slot = self.page.locator(f".v-input:has(.v-label:has-text('{label_text}')) .v-input__slot").first
        await slot.click()
        await asyncio.sleep(random.uniform(0.4, 1.2)) # Scanning for item
        inp = self.page.locator(f".v-input:has(.v-label:has-text('{label_text}')) input").first
        await inp.fill(value)
        await asyncio.sleep(random.uniform(0.6, 1.5)) # Waiting for results
        opt = self.page.locator(".v-list-item:visible, .v-list__tile:visible").first
        if await opt.count() > 0:
            await opt.click()
        await asyncio.sleep(random.uniform(0.3, 0.7)) # Mechanical click

    async def execute(self):
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(random.uniform(0.8, 1.2))

        if not await self.page.locator("text=ผู้จดบันทึก").count():
            return  # ไม่มีหน้านี้

        await self._fill_chip_autocomplete("ผู้จดบันทึก", self.recorder)
        await self._fill_chip_autocomplete("ผู้สำรวจ", self.surveyor)

        try:
            await self.page.locator("text=ใส่รายละเอียดผู้บันทึก").first.click(timeout=1500)
        except:
            await self.page.mouse.click(10, 10)

        await self.helper.click_btn(["ต่อไป", "Next", "ยืนยัน", "บันทึก"], force=True)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(random.uniform(0.8, 1.2))


class TreeCodeFlow:
    """Phase 3a: เลือกรหัสต้นไม้จากลิสต์ (Fallback: พิมพ์ 001 ถ้าเป็นครั้งแรก)"""

    def __init__(self, helper: PageHelper):
        self.helper = helper
        self.page = helper.page

    async def execute(self, filled_count: int = 0) -> tuple:
        """คืนค่า (code_text, is_last)"""
        
        # ── วนลูปพยายามหา Chip (Retry สูงสุด 3 ครั้ง) ──
        for attempt in range(3):
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
            except: pass
            await asyncio.sleep(random.uniform(0.5, 2.0)) # Scanning for chips

            # พยายามกด Tab "ยังไม่ได้กรอก" เพื่อรีเฟรชลิสต์
            list_tab = self.page.locator("text=/ยังไม่ได้(กรอก|บันทึก)/").first
            if await list_tab.count() > 0:
                try:
                    await list_tab.click(timeout=1500)
                    await asyncio.sleep(random.uniform(0.4, 0.8)) # Burst
                except: pass

            all_chips = self.page.locator(".v-chip:visible, .v-btn--chip:visible")
            count = await all_chips.count()
            
            if count > 0:
                texts = await all_chips.all_inner_texts()
                code_pattern = re.compile(r"^\d{5,}$")
                
                valid_indices = []
                for i, txt in enumerate(texts):
                    raw = txt.strip().replace("\n", "").replace(" ", "")
                    if code_pattern.match(raw):
                        valid_indices.append((i, raw))
                
                if valid_indices:
                    idx, code = valid_indices[0]
                    # ถ้าในลิสต์สีเขียว/เหลือง เหลือแค่ต้นเดียว ให้ถือว่าเป็นต้นสุดท้ายของรอบนี้
                    is_last = (len(valid_indices) == 1) 
                    try:
                        target = all_chips.nth(idx)
                        await target.scroll_into_view_if_needed()
                        await target.click(force=True)
                        await asyncio.sleep(random.uniform(0.4, 0.9)) # Burst after selection
                        await self.helper.click_btn(["ต่อไป", "Next", "ยืนยัน", "ตกลง"], force=True)
                        return code, is_last
                    except: pass
            
            if attempt < 2:
                pass

        # ── Fallback 001 (ใช้กรณีหา Chip ไม่เจอจริงๆ) ──
        if filled_count == 0:
            # งมหาช่องกรอกทุกแบบที่เป็นไปได้
            manual_inputs = self.page.locator("input:visible, .v-otp-input input, .v-otp-input__content input")
            try:
                await manual_inputs.first.wait_for(timeout=3000)
            except: pass
            
            input_count = await manual_inputs.count()
            
            # ถ้ายังไม่เจอ ลองหาผ่าน Class ที่ลึกขึ้น
            if input_count == 0:
                manual_inputs = self.page.locator(".v-otp-input [class*='input'], .v-otp-input [role='textbox']")
                input_count = await manual_inputs.count()

            if input_count >= 6:
                try:
                    start_idx = input_count - 3
                    for i, char in enumerate("001"):
                        target_input = manual_inputs.nth(start_idx + i)
                        await target_input.scroll_into_view_if_needed()
                        await target_input.click()
                        await target_input.fill("") 
                        # Variable typing with occasional hesitation
                        for char in "001":
                            await target_input.type(char, delay=random.randint(50, 150))
                            if random.random() < 0.15: # 15% chance to hesitate
                                await asyncio.sleep(random.uniform(0.3, 0.6))
                    
                    await asyncio.sleep(random.uniform(0.4, 0.8)) # Burst to next
                    await self.helper.click_btn(["ต่อไป", "Next", "ยืนยัน", "ตกลง"], force=True)
                    return "001 (Manual)", False
                except Exception as e:
                    pass

        return "", False


class TreeDetailFlow:
    """Phase 3b: กรอกชนิด + สุขภาพ"""

    def __init__(self, helper: PageHelper, weights: dict):
        self.helper = helper
        self.page = helper.page
        self.weights = weights

    async def _fill_species(self):
        species_input = self.page.locator(".v-input:has(.v-label:has-text('ชนิด'))").first
        if await species_input.count() > 0:
            chip = species_input.locator(".v-chip")
            if await chip.count() > 0:
                val = (await chip.first.inner_text()).strip()
                return f"ชนิด={val}"
            else:
                for _try in range(3):
                    await species_input.locator(".v-input__slot").click(force=True)
                    await asyncio.sleep(random.uniform(0.5, 2.0)) # Scanning for species
                    first_opt = self.page.locator(".v-list-item:visible").first
                    if await first_opt.count() > 0:
                        try:
                            opt_name = (await first_opt.inner_text()).strip().split('\n')[0]
                            await first_opt.click(force=True)
                            await asyncio.sleep(random.uniform(0.3, 0.7)) # Burst after select
                            return f"ชนิด={opt_name}"
                        except:
                            continue
        return None

    async def _fill_health(self):
        health = self.page.locator(".v-input:has(.v-label:has-text('สุขภาพ'))").first
        if await health.count() > 0:
            score = PageHelper.pick_health(self.weights)
            await health.scroll_into_view_if_needed()
            await health.locator(".v-input__slot").click()
            await asyncio.sleep(random.uniform(0.6, 1.0))
            opt = self.page.locator(f".v-list-item:has-text('{score.split()[0]}'):visible").first
            if await opt.count() > 0:
                await opt.click(force=True)
                await asyncio.sleep(random.uniform(0.3, 0.6)) # Burst after select
            return f"สุขภาพ={score}"
        return None

    async def execute(self) -> bool:
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
        except: pass
        await asyncio.sleep(random.uniform(0.4, 1.0))

        heading = self.page.locator("h1:has-text('บันทึกรายละเอียด'), h2:has-text('บันทึกรายละเอียด')")
        if await heading.count() == 0:
            return False

        await self._fill_species()
        await self._fill_health()

        await self.helper.click_btn(["ต่อไป", "Next"], force=True)
        await self.page.wait_for_load_state("networkidle")
        return True


class ConfirmFlow:
    """Phase 3c: ยืนยันข้อมูล"""

    def __init__(self, helper: PageHelper):
        self.helper = helper
        self.page = helper.page

    async def execute(self, is_last: bool) -> bool:
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
        except: pass
        await asyncio.sleep(random.uniform(0.5, 1.5)) # Reviewing form before confirm
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # ลำดับการกดปุ่ม: พยายามบันทึกข้อมูลก่อนเสมอ (Priority 1)
        next_btns = [
            "บันทึกและไปต้นต่อไป", "บันทึกและไปต้นถัดไป", "บันทึกและเสร็จสิ้น", 
            "บันทึกข้อมูล", "บันทึก", "ต่อไป", "ตกลง", "ยืนยัน"
        ]
        # ปุ่มที่จะกดเมื่อมั่นใจว่าไม่มีอะไรให้ไปต่อแล้ว (Priority 2)
        finish_btns = ["เสร็จสิ้น", "Finish", "ปิดหน้าต่าง", "ปิด"]

        if is_last:
            # กรณีเป็นต้นสุดท้าย: พยายามหาปุ่ม "เสร็จสิ้น" หรือ "บันทึกและเสร็จสิ้น" ก่อน
            if not await self.helper.click_btn(finish_btns, force=True):
                # ถ้าไม่มีปุ่มเสร็จสิ้นจริงๆ ค่อยลองกดปุ่มบันทึกปกติ
                await self.helper.click_btn(next_btns, force=True)
        else:
            # กรณีที่มีต้นอื่นเหลืออยู่ในลิสต์: พยายามกดกลุ่ม "บันทึกและไปต่อ" ก่อนเสมอ
            if not await self.helper.click_btn(next_btns, force=True):
                 # Fallback ถ้าหาปุ่มถัดไปไม่เจอจริงๆ ค่อยกดเสร็จสิ้น
                 await self.helper.click_btn(finish_btns, force=True)
        
        await asyncio.sleep(random.uniform(0.4, 0.8)) # Burst after final click
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except: pass
        await asyncio.sleep(random.uniform(0.4, 0.8))
        return True


class ImageUploadFlow:
    """Phase 4: อัปโหลดรูปภาพทีละใบไปยังเว็บ"""

    UPLOAD_URL = "https://trees4allthailand.org/farmer/takepicture"

    def __init__(self, helper: PageHelper, account_id: int):
        self.helper = helper
        self.page = helper.page
        self.account_id = account_id

    async def execute(self) -> int:
        images = get_images(self.account_id)
        pending = [img for img in images if img["status"] == "pending"]
        success_count = 0

        if not pending:
            print("    📸 ไม่มีรูปที่ต้องอัปโหลด")
            return 0

        print(f"    📸 พบรูปที่ต้องอัปโหลด {len(pending)} ใบ")

        for i, img in enumerate(pending, 1):
            try:
                # 1. ไปหน้าอัปโหลด
                await self.page.goto(self.UPLOAD_URL)
                await self.helper.safe_wait()
                await asyncio.sleep(random.uniform(1.0, 1.5))

                # 2. หา hidden file input แล้วอัปโหลดรูป
                file_input = self.page.locator("input[type='file']").first
                abs_path = os.path.abspath(img["file_path"])
                await file_input.set_input_files(abs_path)
                await asyncio.sleep(random.uniform(1.5, 2.5))  # รอ Preview ขึ้น

                # 3. กดเสร็จสิ้น (ปุ่มจะ active หลังอัปรูป)
                await self.helper.click_btn(["เสร็จสิ้น", "ตกลง", "บันทึก"], force=True)
                try:
                    await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
                except: pass
                await asyncio.sleep(random.uniform(1.0, 1.8))

                # 4. อัปเดต DB
                update_image_status(img["id"], "done")
                success_count += 1
                print(f"    📸 [{i}/{len(pending)}] อัปโหลดสำเร็จ")

            except Exception as e:
                update_image_status(img["id"], "error")
                print(f"    📸 [{i}/{len(pending)}] ล้มเหลว: {e}")
        
        return success_count


# ═══════════════════════════════════════════════════════════════════════════════
#  Section 4: Orchestrator + Runner
# ═══════════════════════════════════════════════════════════════════════════════

class BotOrchestrator:
    """ควบคุมลำดับ Flow ทั้งหมดสำหรับ 1 บัญชี"""

    def __init__(self, page, account: dict, config: BotConfig):
        self.helper = PageHelper(page)
        self.page = page
        self.account = account
        self.config = config

    async def run(self) -> dict:
        acc = self.account
        stats = {"filled": 0, "error": 0}
        phone = acc["phone"]

        print(f"\n" + "=" * 55)
        print(f" [Queue] กำลังทำ: {phone} | {acc['recorder']}")
        print("=" * 55)

        # บอก Dashboard ว่ากำลังทำบัญชีไหน
        update_setting("bot_current_phone", phone)

        # ── Phase 1: Login ──
        await LoginFlow(self.helper, phone, acc["password"]).execute()

        # ── Phase 2: Navigate + Recorder ──
        await self.page.goto("https://trees4allthailand.org/farmer")
        await self.page.wait_for_load_state("networkidle")

        start_btn = self.page.locator("text=เริ่มบันทึกผลต้นไม้").first
        if await start_btn.count() > 0:
            await start_btn.click()
        else:
            await self.page.goto("https://trees4allthailand.org/farmer/tracking")

        await RecorderFlow(self.helper, acc["recorder"], acc["surveyor"]).execute()

        # ── Phase 3: Tree Loop ──
        # Calculate health weights from account-specific settings
        h3 = float(acc.get("health_3", 80))
        h2 = float(acc.get("health_2", 15))
        h1 = float(acc.get("health_1", 5))
        total = h3 + h2 + h1
        account_weights = {
            "3 สุขภาพดี": h3 / total,
            "2 ปานกลาง":  h2 / total,
            "1 แย่":       h1 / total,
        }

        tree_code = TreeCodeFlow(self.helper)
        tree_detail = TreeDetailFlow(self.helper, account_weights)
        confirm = ConfirmFlow(self.helper)

        while True:
            tree_start_time = time.time()
            code_text, is_last = await tree_code.execute(stats["filled"])
            if not code_text:
                break

            if await tree_detail.execute():
                await confirm.execute(is_last)
                stats["filled"] += 1

                duration = round(time.time() - tree_start_time, 2)

                try:
                    add_speed_log(acc["id"], duration)
                except Exception as e:
                    pass

                print(f"    [OK] ต้นที่ {stats['filled']}: {code_text} | "
                      f"ใช้เวลา {duration} วิ {'(Last!)' if is_last else ''}")

                if is_last:
                    break

                await asyncio.sleep(random.uniform(1.0, 5.0)) # Wide-range inter-tree pause
            else:
                stats["error"] += 1
                await self.page.goto("https://trees4allthailand.org/farmer/tracking")

        # ── Phase 4: Image Upload ──
        uploaded_count = await ImageUploadFlow(self.helper, acc["id"]).execute()

        update_status(phone, "done", trees_filled=stats["filled"], images_uploaded=uploaded_count)
        update_setting("bot_current_phone", "")  # เคลียร์สถานะ
        print(f"\n  [Done] บัญชี {phone} สำเร็จ: {stats['filled']} ต้น / {uploaded_count} รูป")

        return stats


def _find_browser_executable() -> str | None:
    """หา Chrome หรือ Edge ที่ติดตั้งในเครื่อง"""
    candidates = [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",  # Chrome x86
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",         # Chrome x64
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",  # Edge x86
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",        # Edge x64
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"  [Config] ใช้ Browser: {path}")
            return path
    return None  # ถ้าไม่เจอเลย ปล่อยให้ Playwright หาเอง


class BotRunner:
    """Entry point: โหลดคิว วนลูปแต่ละ account"""

    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()

    async def start(self):
        accounts = get_pending_accounts()

        if not accounts:
            print("\n  (!) ไม่พบคิวผู้ใช้ที่ต้องทำงาน (สถานะ pending)")
            return

        print(f"\n  [Bot] พบคิวที่รอดำเนินการ {len(accounts)} คน")

        # ── หา browser ก่อน launch ──
        browser_path = _find_browser_executable()

        async with async_playwright() as p:
            for acc in accounts:
                launch_options = {"headless": self.config.headless}
                if browser_path:
                    launch_options["executable_path"] = browser_path

                browser = await p.chromium.launch(**launch_options)
                page = await (await browser.new_context()).new_page()

                try:
                    orchestrator = BotOrchestrator(page, acc, self.config)
                    await orchestrator.run()
                except Exception as e:
                    print(f"    [Error] {acc['phone']} ล้มเหลว: {e}")
                    update_status(acc["phone"], "error")
                finally:
                    await browser.close()

                # พักระหว่างบัญชี (10 - 20 นาที) ตามคำขอ
                rest_seconds = random.randint(600, 1200)
                print(f"\n  [Rest] พักเบรกระหว่างบัญชี {round(rest_seconds/60, 1)} นาที...")
                await asyncio.sleep(rest_seconds)


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    config = BotConfig()
    runner = BotRunner(config)
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
