import pywhatkit
import time
import pyautogui


def send_whatsapp_message(phone_number: str, message: str):
    try:
        print(f"📨 Opening WhatsApp chat for {phone_number}")
        pywhatkit.sendwh
        atmsg_instantly(    
            phone_no=phone_number,
            message=message,
            wait_time=20,
            tab_close=True
        )

        # ✅ Wait a bit to ensure message box is ready
        time.sleep(8)

        # ✅ Press Enter to send the message
        pyautogui.press('enter')

        print(f"✅ Message sent to {phone_number}")
        return True
    except Exception as e:
        print(f"❌ Error sending to {phone_number}: {e}")
        return False
    

