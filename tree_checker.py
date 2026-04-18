import sys
import asyncio
import argparse
import random
import time
import re
from playwright.async_api import async_playwright
import os
import database

"""
Tree Checker V4.0.0 — EXACT MATCH PORT from trees_bot.py
============================================================
Logic is 100% mirrored from trees_bot.py for maximum compatibility.
Only arrows (→) are replaced with (->) for terminal safety.
"""

# --- 1:1 COPY from trees_bot.py (Section 2: PageHelper) ---

class PageHelper:
    def __init__(self, page):
        self.page = page

    async def click_btn(self, texts: list, timeout=5000, force=False):
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
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except:
            pass

    @staticmethod
    def pick_health(weights: dict) -> str:
        r = random.random()
        cum = 0.0
        for label, w in weights.items():
            cum += w
            if r <= cum:
                return label
        return list(weights.keys())[1]

# --- 1:1 COPY from trees_bot.py (Section 3: LoginFlow) ---

class LoginFlow:
    def __init__(self, helper: PageHelper, phone: str, password: str):
        self.helper = helper
        self.page = helper.page
        self.phone = phone
        self.password = password

    async def execute(self):
        print(f"    -> Login {self.phone} ...")
        await self.page.goto("https://trees4allthailand.org/login")
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass

        await self.page.locator(
            "input[type='tel'], input[type='text'], "
            "input[placeholder*='เบอร์'], input[name*='phone'], input[name*='username']"
        ).first.fill(self.phone)
        await asyncio.sleep(0.5)

        await self.page.locator("input[type='password']").first.fill(self.password)
        await asyncio.sleep(0.3)

        await self.helper.click_btn(["เข้าสู่ระบบ", "Login"])
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(0.5)

        if "login" in self.page.url.lower():
            raise Exception("Login ไม่สำเร็จ — ตรวจสอบเบอร์/รหัสผ่าน")

# --- 1:1 COPY from trees_bot.py (Section 3: RecorderFlow) ---

class RecorderFlow:
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
        await asyncio.sleep(0.4)
        opt = self.page.locator(".v-list-item:visible, .v-list__tile:visible").first
        if await opt.count() > 0:
            await opt.click()
        await asyncio.sleep(0.2)

    async def execute(self):
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(0.5)

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
        await asyncio.sleep(0.5)

# --- End of Adaptation ---

class CheckerOrchestrator:
    def __init__(self, page, account: dict):
        self.helper = PageHelper(page)
        self.page = page
        self.account = account

    async def run(self):
        phone = self.account["phone"]
        print(f"\n[Check] Account: {phone}...")
        
        # 1. Login
        await LoginFlow(self.helper, phone, self.account["password"]).execute()

        # 2. Hard Navigation to Start Page
        await self.page.goto("https://trees4allthailand.org/farmer")
        await self.page.wait_for_load_state("networkidle")

        start_btn = self.page.locator("text=เริ่มบันทึกผลต้นไม้").first
        if await start_btn.count() > 0:
            await start_btn.click()
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
            except: pass
        else:
            await self.page.goto("https://trees4allthailand.org/farmer/tracking")

        # 3. Recorder Flow (EXACT COPY)
        await RecorderFlow(self.helper, self.account['recorder'], self.account['surveyor']).execute()

        # 4. Final Verification and Navigation
        if "tracking" not in self.page.url:
            await self.page.goto("https://trees4allthailand.org/farmer/tracking")

        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=4000)
        except: pass
        await asyncio.sleep(1)

        content = await self.page.content()
        saved_match = re.search(r"บันทึกข้อมูลไปแล้ว.*?(\d+)\s*ต้น", content, re.DOTALL)
        tree_count = int(saved_match.group(1)) if saved_match else 0
        
        try:
            target_el = self.page.locator(".v-list-item:has-text('บันทึกข้อมูลไปแล้ว')").first
            if await target_el.count() > 0:
                inner = await target_el.inner_text()
                num_match = re.search(r"(\d+)\s+ต้น", inner)
                if num_match: tree_count = int(num_match.group(1))
        except: pass

        images = database.get_images(self.account["id"])
        image_count = len(images)

        database.update_status(phone, self.account["status"], trees_filled=tree_count, images_uploaded=image_count)
        print(f"[Done] {phone}: Trees={tree_count} | Images={image_count}")


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


class CheckerRunner:
    async def start(self, target_phones=None):
        if target_phones:
            accounts = []
            for p in target_phones:
                conn = database.get_db_connection()
                acc = conn.execute("SELECT * FROM accounts WHERE phone = ?", (p,)).fetchone()
                if acc: accounts.append(dict(acc))
                conn.close()
        else:
            accounts = database.get_all_accounts()

        if not accounts: return

        print(f"[Checker] Sequential port started for {len(accounts)} accounts.")

        browser_path = _find_browser_executable()

        async with async_playwright() as p:
            for acc in accounts:
                browser = None
                try:
                    launch_options = {"headless": False}
                    if browser_path:
                        launch_options["executable_path"] = browser_path

                    browser = await p.chromium.launch(**launch_options)
                    page = await browser.new_page()
                    orchestrator = CheckerOrchestrator(page, acc)
                    await orchestrator.run()
                    await browser.close()
                except Exception as e:
                    print(f"[Error] {acc['phone']} failed: {e}")
                    if browser: await browser.close()
                await asyncio.sleep(1)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phones", nargs="+", help="Specific phone numbers to check")
    args, unknown = parser.parse_known_args()
    runner = CheckerRunner()
    await runner.start(target_phones=args.phones)

if __name__ == "__main__":
    asyncio.run(main())
