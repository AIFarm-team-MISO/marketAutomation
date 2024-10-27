from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys  # Keys를 임포트

# 페이지 이동 후, 라디오 버튼 클릭 함수
def select_radio_button(driver, title_text):
    try:
        # 주어진 타이틀을 포함하는 <td> 요소를 찾음
        radio_td = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{title_text}')]"))
        )

        # 라디오 버튼을 찾음
        radio_input = radio_td.find_element(By.XPATH, "./preceding-sibling::td/input[@type='radio']")

        # 라디오 버튼 HTML 출력
        print("라디오 버튼 HTML:")
        print(driver.execute_script("return arguments[0].outerHTML;", radio_input))

        # 라디오 버튼 클릭
        driver.execute_script("arguments[0].scrollIntoView(true);", radio_input)
        driver.execute_script("arguments[0].click();", radio_input)

        print(f"'{title_text}' 라디오 버튼을 클릭했습니다.")
        
        # 라디오 버튼 클릭 후 페이지 변화를 기다림 (예: 특정 요소가 나타나는지)
        # WebDriverWait(driver, 5).until(
        #     EC.presence_of_element_located((By.XPATH, "//특정_요소_확인_할_XPATH"))
        # )
    
    except Exception as e:
        print(f"라디오 버튼 선택 후 오류 발생: {e}")



# 페이지 하단으로 키보드를 사용해 이동하는 함수
def scroll_to_bottom_with_keyboard(driver):
    try:
        # 페이지 전체가 로드될 때까지 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # BODY 태그에 키보드 입력을 보냄 (END 키 또는 PAGE_DOWN 키)
        body = driver.find_element(By.TAG_NAME, "body")
        
        # 여러 번 PAGE_DOWN 키를 눌러 아래로 스크롤
        for _ in range(10):  # 필요한 만큼 조정 가능
            body.send_keys(Keys.PAGE_DOWN)
        
        print("키보드로 페이지 하단까지 스크롤했습니다.")
    
    except Exception as e:
        print(f"스크롤 중 오류 발생: {e}")

# 버튼 클릭 함수
def click_element(driver, xpath):
    try:
        # 요소가 로드될 때까지 기다림 (최대 10초)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        # 요소 클릭
        element.click()
        print("요소를 성공적으로 클릭했습니다.")
    except Exception as e:
        print(f"요소 클릭 중 오류 발생: {e}")

# 다운로드 버튼 클릭 함수
def click_download_button(driver):
    try:
        # 페이지 하단으로 스크롤
        scroll_to_bottom_with_keyboard(driver)

        # 다운로드 버튼을 찾는 XPATH
        xpath = "//img[@src='http://www.zsms.co.kr/images/prdtdn_esellers_excel.jpg']"
        
        # 해당 요소가 나타날 때까지 기다렸다가 클릭 (최대 30초 대기)
        download_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        

        # 다운로드 버튼을 JavaScript로 클릭
        download_button = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", download_button)
        print("다운로드 버튼을 성공적으로 클릭했습니다.")

        # time.sleep(10)
        

         # 팝업창에서 확인 버튼 클릭
        WebDriverWait(driver, 10).until(EC.alert_is_present())  # 팝업이 나타날 때까지 기다림
        alert = driver.switch_to.alert  # 팝업창으로 전환
        alert.accept()  # 확인 버튼 클릭
        print("팝업창의 확인 버튼을 클릭했습니다.")

        


        time.sleep(30)



        
    except Exception as e:
        print(f"다운로드 버튼 클릭 중 오류 발생: {e}")



# 페이지 이동 및 버튼 클릭 함수
def navigate_to_download_page(driver):
    try:
        # 명시적 대기: 버튼이 나타날 때까지 대기 (버튼을 클릭 가능한 상태로 기다림)
        download_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//b[text()='상품DB 다운로드']"))
        )

        # 버튼 클릭
        download_button.click()

        print("상품DB 다운로드 버튼을 클릭하고 다음 페이지로 이동했습니다.")
    
    except Exception as e:
        print(f"페이지 이동 중 오류 발생: {e}")
