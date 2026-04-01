import os
import requests
from seleniumbase import SB

EMAIL = os.environ["B4A_EMAIL"]
PASSWORD = os.environ["B4A_PASSWORD"]
TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

APP_ID = "90148b3e-2353-459f-a1f8-e34377e389bc"
APP_URL = f"https://containers.back4app.com/apps/{APP_ID}"
LOGIN_URL = f"https://www.back4app.com/login?return-url=https%3A%2F%2Fcontainers.back4app.com%2Fapps%2F{APP_ID}"
PROXY = "http://127.0.0.1:8080"

def notify(msg):
    if TG_TOKEN and TG_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT_ID, "text": f"[B4A] {msg}"},
                timeout=10
            )
        except Exception as e:
            print(f"TG notify failed: {e}")

def find_button_by_text(sb, keyword):
    """遍历所有 button，小写匹配关键字"""
    buttons = sb.find_elements("button")
    for btn in buttons:
        if keyword.lower() in btn.text.lower():
            return btn
    return None

def find_button_xpath(sb, keyword):
    """XPath 兜底匹配"""
    try:
        return sb.find_element(
            f'//button[contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"{keyword.lower()}")]'
        )
    except:
        return None

def run():
    with SB(uc=True, headless=True, proxy=PROXY) as sb:

        # ── 直接打开带 return-url 的登录页 ──
        print(f"Navigating to login page: {LOGIN_URL}")
        sb.open(LOGIN_URL)
        sb.sleep(3)
        sb.save_screenshot("login_page.png")
        print("Screenshot saved: login_page.png")

        # ── 填写邮箱和密码 ──
        sb.wait_for_element("input[placeholder='Email']", timeout=20)
        sb.type("input[placeholder='Email']", EMAIL)
        sb.type("input[placeholder='Password']", PASSWORD)

        # ── 点击 Continue 按钮 ──
        continue_btn = find_button_by_text(sb, "continue")
        if continue_btn is None:
            continue_btn = find_button_xpath(sb, "continue")

        if continue_btn is None:
            sb.save_screenshot("login_failed.png")
            msg = "❌ 未找到 Continue 登录按钮，请查看截图"
            print(msg)
            notify(msg)
            raise Exception(msg)

        print(f"Clicking login button: '{continue_btn.text.strip()}'")
        continue_btn.click()
        sb.sleep(5)

        # ── 登录结果判断 ──
        current_url = sb.get_current_url()
        print(f"Post-login URL: {current_url}")

        if "login" in current_url.lower():
            sb.save_screenshot("login_failed.png")
            msg = "❌ 登录失败，仍停留在登录页，请检查邮箱和密码"
            print(msg)
            notify(msg)
            raise Exception(msg)

        # ── 判断是否已自动跳转到目标 App 页面 ──
        if APP_ID not in current_url:
            # 未自动跳转，手动导航
            print(f"Not redirected automatically, navigating to: {APP_URL}")
            sb.open(APP_URL)
            sb.sleep(5)
            current_url = sb.get_current_url()

        if APP_ID not in current_url:
            sb.save_screenshot("wrong_page.png")
            msg = f"❌ 未到达目标 App 页面，当前 URL: {current_url}"
            print(msg)
            notify(msg)
            raise Exception(msg)

        print("Successfully reached target app page.")

        # 滚动到底部确保左下角按钮渲染
        sb.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        sb.sleep(2)

        # 截图留档
        sb.save_screenshot("before_click.png")
        print("Screenshot saved: before_click.png")

        # ── 查找 Redeploy App 按钮 ──
        redeploy_btn = find_button_by_text(sb, "redeploy")
        if redeploy_btn is None:
            print("Text match failed, trying XPath fallback...")
            redeploy_btn = find_button_xpath(sb, "redeploy")

        if redeploy_btn is None:
            msg = "❌ 未找到 Redeploy App 按钮，可能当前无需部署或页面结构已变化"
            print(msg)
            notify(msg)
            raise Exception(msg)

        # ── 滚动到按钮位置并点击 ──
        print(f"Found button: '{redeploy_btn.text}', clicking...")
        sb.execute_script("arguments[0].scrollIntoView(true);", redeploy_btn)
        sb.sleep(1)
        redeploy_btn.click()

        # ── 点击后确认：等待 Redeploy 按钮消失 ──
        click_confirmed = False
        for i in range(5):
            sb.sleep(3)
            print(f"Checking if button disappeared... attempt {i+1}/5")
            btn_check = find_button_by_text(sb, "redeploy")
            if btn_check is None:
                click_confirmed = True
                break

        # 截图确认点击后状态
        sb.save_screenshot("after_click.png")
        print("Screenshot saved: after_click.png")

        if click_confirmed:
            msg = "✅ Redeploy 成功，部署按钮已消失，Console 正在显示部署日志"
        else:
            msg = "⚠️ 已点击 Redeploy 按钮，但按钮未消失，请查看截图手动核对"

        print(msg)
        notify(msg)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = f"❌ 脚本出错: {e}"
        print(err)
        notify(err)
        raise
