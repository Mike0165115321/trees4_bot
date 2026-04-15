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

        pct3 = float(raw.get("health_3", 80))
        pct2 = float(raw.get("health_2", 15))
        pct1 = float(raw.get("health_1", 5))
        self.headless = False  # บังคับเปิดหน้าจอให้เห็น

        t = pct3 + pct2 + pct1
        self.weights = {
            "3 สุขภาพดี": pct3 / t,
            "2 ปานกลาง":  pct2 / t,
            "1 แย่":       pct1 / t,
        }

        print("\n" + "= " * 55)
        print("  (Tree)  Trees4All Bot V1.0.0 (Class-Based Architecture)")
        print("= " * 55)
        print(f"  [Config] สุขภาพ: 3={pct3:.0f}%  2={pct2:.0f}%  1={pct1:.0f}%")
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
        await self.page.wait_for_load_state("networkidle")

        await self.page.locator(
            "input[type='tel'], input[type='text'], "
            "input[placeholder*='เบอร์'], input[name*='phone'], input[name*='username']"
        ).first.fill(self.phone)
        await asyncio.sleep(random.uniform(0.6, 1.2))

        await self.page.locator("input[type='password']").first.fill(self.password)
        await asyncio.sleep(random.uniform(0.5, 1.0))

        await self.helper.click_btn(["เข้าสู่ระบบ", "Login"])
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.0)

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
        await asyncio.sleep(0.3)
        inp = self.page.locator(f".v-input:has(.v-label:has-text('{label_text}')) input").first
        await inp.fill(value)
        await asyncio.sleep(0.5)
        opt = self.page.locator(".v-list-item:visible, .v-list__tile:visible").first
        if await opt.count() > 0:
            await opt.click()
        await asyncio.sleep(0.3)

    async def execute(self):
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        if not await self.page.locator("text=ผู้จดบันทึก").count():
            return  # ไม่มีหน้านี้

        await self._fill_chip_autocomplete("ผู้จดบันทึก", self.recorder)
        await self._fill_chip_autocomplete("ผู้สำรวจ", self.surveyor)

        try:
            await self.page.locator("text=ใส่รายละเอียดผู้บันทึก").first.click(timeout=2000)
        except:
            await self.page.mouse.click(10, 10)

        await self.helper.click_btn(["ต่อไป", "Next", "ยืนยัน", "บันทึก"], force=True)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)


class TreeCodeFlow:
    """Phase 3a: เลือกรหัสต้นไม้จากลิสต์"""

    def __init__(self, helper: PageHelper):
        self.helper = helper
        self.page = helper.page

    async def execute(self) -> tuple:
        """คืนค่า (code_text, is_last)"""
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)

        list_tab = self.page.locator("text=/ยังไม่ได้(กรอก|บันทึก)/").first
        if await list_tab.count() > 0:
            try:
                await list_tab.scroll_into_view_if_needed()
                await list_tab.click(force=True, timeout=3000)
                await asyncio.sleep(0.6)
            except:
                pass

        all_chips = self.page.locator(".v-chip:visible, .v-btn--chip:visible")
        count = await all_chips.count()
        code_pattern = re.compile(r"^\d{5,}$")

        valid_data = []
        for i in range(count):
            try:
                chip = all_chips.nth(i)
                raw = (await chip.inner_text()).strip().replace("\n", "").replace(" ", "")
                if code_pattern.match(raw):
                    valid_data.append({"chip": chip, "code": raw})
            except:
                continue

        if not valid_data:
            return "", False

        is_last = (len(valid_data) == 1)
        target = valid_data[0]

        try:
            await target["chip"].scroll_into_view_if_needed()
            await target["chip"].click(force=True)
            await asyncio.sleep(0.5)
            await self.helper.click_btn(["ต่อไป", "Next", "ยืนยัน", "ตกลง"], force=True)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)
            return target["code"], is_last
        except:
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
                    await asyncio.sleep(0.4)
                    first_opt = self.page.locator(".v-list-item:visible").first
                    if await first_opt.count() > 0:
                        try:
                            opt_name = (await first_opt.inner_text()).strip().split('\n')[0]
                            await first_opt.click(force=True)
                            await asyncio.sleep(0.3)
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
            await asyncio.sleep(0.4)
            opt = self.page.locator(f".v-list-item:has-text('{score.split()[0]}'):visible").first
            if await opt.count() > 0:
                await opt.click(force=True)
                await asyncio.sleep(0.3)
            return f"สุขภาพ={score}"
        return None

    async def execute(self) -> bool:
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)

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
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.8)
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        if is_last:
            await self.helper.click_btn(["เสร็จสิ้น", "Finish"], force=True)
        else:
            await self.helper.click_btn(["บันทึกและไปต้นต่อไป", "บันทึกและไปต้นถัดไป"], force=True)

        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.4)
        return True


class ImageUploadFlow:
    """Phase 4: อัปโหลดรูปภาพทีละใบไปยังเว็บ"""

    UPLOAD_URL = "https://trees4allthailand.org/farmer/takepicture"

    def __init__(self, helper: PageHelper, account_id: int):
        self.helper = helper
        self.page = helper.page
        self.account_id = account_id

    async def execute(self):
        images = get_images(self.account_id)
        pending = [img for img in images if img["status"] == "pending"]

        if not pending:
            print("    📸 ไม่มีรูปที่ต้องอัปโหลด")
            return

        print(f"    📸 พบรูปที่ต้องอัปโหลด {len(pending)} ใบ")

        for i, img in enumerate(pending, 1):
            try:
                # 1. ไปหน้าอัปโหลด
                await self.page.goto(self.UPLOAD_URL)
                await self.helper.safe_wait()
                await asyncio.sleep(0.5)

                # 2. หา hidden file input แล้วอัปโหลดรูป
                file_input = self.page.locator("input[type='file']").first
                abs_path = os.path.abspath(img["file_path"])
                await file_input.set_input_files(abs_path)
                await asyncio.sleep(1.5)  # รอ Preview ขึ้น

                # 3. กดเสร็จสิ้น (ปุ่มจะ active หลังอัปรูป)
                await self.helper.click_btn(["เสร็จสิ้น", "ตกลง", "บันทึก"], force=True)
                await self.helper.safe_wait()
                await asyncio.sleep(0.5)

                # 4. อัปเดต DB
                update_image_status(img["id"], "done")
                print(f"    📸 [{i}/{len(pending)}] อัปโหลดสำเร็จ")

            except Exception as e:
                update_image_status(img["id"], "error")
                print(f"    📸 [{i}/{len(pending)}] ล้มเหลว: {e}")


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
        tree_code = TreeCodeFlow(self.helper)
        tree_detail = TreeDetailFlow(self.helper, self.config.weights)
        confirm = ConfirmFlow(self.helper)

        while True:
            tree_start_time = time.time()
            code_text, is_last = await tree_code.execute()
            if not code_text:
                break

            if await tree_detail.execute():
                await confirm.execute(is_last)
                stats["filled"] += 1

                duration = round(time.time() - tree_start_time, 2)

                try:
                    add_speed_log(acc["id"], duration)
                except Exception as e:
                    print(f"    [Warn] Cannot save speed log: {e}")

                print(f"    [OK] ต้นที่ {stats['filled']}: {code_text} | "
                      f"ใช้เวลา {duration} วิ {'(Last!)' if is_last else ''}")

                if is_last:
                    break

                await asyncio.sleep(random.uniform(0.3, 0.5))
            else:
                stats["error"] += 1
                await self.page.goto("https://trees4allthailand.org/farmer/tracking")

        # ── Phase 4: Image Upload ──
        await ImageUploadFlow(self.helper, acc["id"]).execute()

        update_status(phone, "done")
        update_setting("bot_current_phone", "")  # เคลียร์สถานะ
        print(f"\n  [Done] บัญชี {phone} สำเร็จ: {stats['filled']} ต้น")

        return stats


class BotRunner:
    """Entry point: โหลดคิว วนลูปแต่ละ account"""

    def __init__(self):
        self.config = BotConfig()

    async def start(self):
        accounts = get_pending_accounts()

        if not accounts:
            print("\n  (!) ไม่พบคิวผู้ใช้ที่ต้องทำงาน (สถานะ pending)")
            return

        print(f"\n  [Bot] พบคิวที่รอดำเนินการ {len(accounts)} คน")

        async with async_playwright() as p:
            for acc in accounts:
                browser = await p.chromium.launch(headless=self.config.headless)
                page = await (await browser.new_context()).new_page()

                try:
                    orchestrator = BotOrchestrator(page, acc, self.config)
                    await orchestrator.run()
                except Exception as e:
                    print(f"    [Error] {acc['phone']} ล้มเหลว: {e}")
                    update_status(acc["phone"], "error")
                finally:
                    await browser.close()

                await asyncio.sleep(2)


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    runner = BotRunner()
    asyncio.run(runner.start())


if __name__ == "__main__":
    main()
