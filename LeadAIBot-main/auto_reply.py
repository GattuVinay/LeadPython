import asyncio
from playwright.async_api import async_playwright
from db import save_message
import time

async def monitor_and_reply():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://web.whatsapp.com")
        print("🔒 Waiting for login...")
        await page.wait_for_selector("._3z5Nh", timeout=120000)

        print("🔁 Monitoring every 5 minutes...")
        while True:
            try:
                chats = await page.query_selector_all("div._2aBzC")  # all chat rows
                for chat in chats:
                    unread = await chat.query_selector("span[aria-label*='unread message']")
                    if unread:
                        await chat.click()
                        await page.wait_for_selector("div.message-in span.selectable-text", timeout=5000)

                        messages = await page.query_selector_all("div.message-in span.selectable-text")
                        if messages:
                            last_msg = await messages[-1].inner_text()
                            print(f"👤 Incoming from lead: {last_msg}")

                            auto_reply = "Thank you for your message! We’ll get in touch shortly. 🤝"
                            await page.locator("div._2A8P4").click()
                            await page.keyboard.type(auto_reply)
                            await page.keyboard.press("Enter")

                            # Extract phone number
                            phone_element = await page.query_selector("header span[title]")
                            phone_number = await phone_element.inner_text()

                            save_message(phone_number, last_msg, auto_reply)
                            print(f"✅ Replied and saved message from {phone_number}")

                await asyncio.sleep(300)  # wait 5 minutes
            except Exception as e:
                print(f"⚠️ Error: {e}")
                await asyncio.sleep(60)  # wait 1 min before retrying
