# excel_make.py
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from config.settings import LOGIN_URL, MAIN_URL, USERNAME, PASSWORD
from rotationAuto.driver.driver_init import setup_driver


# zsm 로그인 함수
def login(driver, login_url, username, password):
    driver.get(login_url)  # 로그인 페이지로 이동
    # time.sleep(2)  # 페이지 로드 대기

    #명시적 대기: 최대 10초 동안 username 필드가 로드될 때까지 기다림
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "id")))  # "id" 필드 대기
    
    # ID 입력 필드와 비밀번호 입력 필드 선택
    username_field = driver.find_element(By.NAME, "id")  # NAME이 "id"로 변경됨
    password_field = driver.find_element(By.NAME, "passwd")  # NAME 확인 필요

    # 로그인 정보 입력
    username_field.send_keys(username)
    password_field.send_keys(password)

    # 로그인 버튼 클릭
    password_field.send_keys(Keys.RETURN)
    # time.sleep(2)  # 로그인 처리 대기



    print("로그인 성공, 메인 페이지로 이동합니다.")

# 로그인 세션이 있으면 메인 페이지로 이동
def check_and_go_to_main_page(driver, main_url):
    driver.get(main_url)
    time.sleep(2)
    
    if driver.current_url == main_url:
        print("로그인 성공, 메인 페이지로 이동합니다.")
    else:
        print("로그인 실패 또는 세션 없음.")

# 로그인 후 메인 페이지로 이동
def login_and_navigate():
    driver = setup_driver()  # 드라이버 초기화
    login(driver, LOGIN_URL, USERNAME, PASSWORD)
    check_and_go_to_main_page(driver, MAIN_URL)
    
    return driver  # 로그인 후 드라이버 반환

# 메인 작업 후 드라이버 종료
def close_driver(driver):
    print("작업 완료 후 드라이버를 종료합니다.")
    driver.quit()
