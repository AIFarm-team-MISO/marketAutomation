# driver_init.py
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from config.settings import CHROME_DRIVER_PATH
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    # Chrome 옵션 설정
    chrome_options = webdriver.ChromeOptions()
    
    # 브라우저 창을 최대화
    chrome_options.add_argument("--start-maximized")

    # 브라우저 로깅을 활성화
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    chrome_options.add_argument("--disable-gpu")  # GPU 가속 끄기

    #"download.default_directory": r"f:\work\쇼핑몰\대량등록\상품순환 엑셀파일\상품순환필터링",  # 원하는 다운로드 경로
    
    # # 팝업 차단 해제 및 안전하지 않은 다운로드 허용 설정
    prefs = {
        "profile.default_content_settings.popups": 0,
        "download.default_directory": r"C:\download",  # 다운로드 경로
        "download.prompt_for_download": False,  # 다운로드 시 확인창 비활성화
        "safebrowsing.enabled": False,  # 안전 브라우징 비활성화
        "safebrowsing.disable_download_protection": True,  # 다운로드 보호 비활성화
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,  # 자동 다운로드 허용
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")


    # Headless 모드로 실행하려면 주석 해제
    # chrome_options.add_argument("--headless")

    # 크롬 드라이버 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    return driver