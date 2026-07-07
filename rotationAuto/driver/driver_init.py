import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.web_automation_settings import CHROME_PROFILE_ROOT, CHROME_OPTIONS


def setup_driver(profile_name=None, download_dir=None, headless=None):
    """
    Selenium Chrome Driver 생성 함수
    """

    if download_dir is None:
        download_dir = CHROME_OPTIONS.get("download_dir", r"C:\download")

    os.makedirs(download_dir, exist_ok=True)

    chrome_options = webdriver.ChromeOptions()

    if headless is None:
        headless = CHROME_OPTIONS.get("headless", False)

    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=2000,1600")

    # 브라우저 창 크기 설정
    if CHROME_OPTIONS.get("start_maximized"):
        chrome_options.add_argument("--start-maximized")
    else:
        window_width = CHROME_OPTIONS["window_width"]
        window_height = CHROME_OPTIONS["window_height"]
        window_x = CHROME_OPTIONS.get("window_position_x", 0)
        window_y = CHROME_OPTIONS.get("window_position_y", 0)

        chrome_options.add_argument(f"--window-size={window_width},{window_height}")
        chrome_options.add_argument(f"--window-position={window_x},{window_y}")

    if CHROME_OPTIONS.get("enable_logging", True):
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--v=1")

    if CHROME_OPTIONS.get("disable_gpu", True):
        chrome_options.add_argument("--disable-gpu")

    if CHROME_OPTIONS.get("allow_running_insecure_content", True):
        chrome_options.add_argument("--allow-running-insecure-content")

    if CHROME_OPTIONS.get("disable_automation_controlled", True):
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    if CHROME_OPTIONS.get("headless", False):
        chrome_options.add_argument("--headless=new")

    if profile_name and CHROME_OPTIONS.get("use_chrome_profile", True):
        profile_root = os.path.join(CHROME_PROFILE_ROOT, profile_name)
        os.makedirs(profile_root, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_root}")

    prefs = {
        "profile.default_content_settings.popups": 0,
        "download.default_directory": download_dir,
        "download.prompt_for_download": CHROME_OPTIONS.get("download_prompt", False),
        "safebrowsing.enabled": CHROME_OPTIONS.get("safe_browsing", False),
        "safebrowsing.disable_download_protection": True,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
    }

    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )

    # 브라우저 생성 후 창 크기 강제 적용
    # 크롬 프로필이 이전 최대화 상태를 기억하는 경우를 방지
    if not CHROME_OPTIONS.get("start_maximized"):
        window_width = CHROME_OPTIONS["window_width"]
        window_height = CHROME_OPTIONS["window_height"]
        window_x = CHROME_OPTIONS.get("window_position_x", 0)
        window_y = CHROME_OPTIONS.get("window_position_y", 0)
        driver.set_window_position(window_x, window_y)
        driver.set_window_size(window_width, window_height)

    return driver