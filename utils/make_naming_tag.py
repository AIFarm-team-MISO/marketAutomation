import json
import random
import sys
import os
import requests
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# 현재 스크립트의 경로를 기준으로 utils 폴더 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.global_logger import logger

from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary
from keywordOptimization.keyword_combination import load_category_dict, filter_gpt_keywords_by_category, remove_redundant_keywords
from keywordOptimization.keyword_combination import clean_fixed_keywords
from config.settings import FILTER_KEYWORDS, FILTER_UNIT_KEYWORDS, COUPANG_FILTER_KEYWORDS
from config.settings import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, API_KEY, SECRET_KEY,CUSTOMER_ID

from keywordOptimization.naver_api import get_header

def generate_params_and_headers(source_type, main_keyword, display=10):
    """
    API 요청에 필요한 URL, 헤더, 파라미터 생성.

    Parameters:
    - source_type (str): API 종류 선택 ("상위판매자" 또는 "연관검색어").
    - main_keyword (str): 메인 키워드.
    - display (int): 검색 결과 개수 (기본값: 10).

    Returns:
    - url (str): 요청할 URL.
    - headers (dict): 요청 헤더.
    - params (dict): 요청 파라미터.
    """
    if source_type == "상위판매자":
        url = "https://openapi.naver.com/v1/search/shop.json"
        params = {
            "query": main_keyword,
            "display": display,
            "sort": "sim" # rec(추천), sell(판매량), recent(최신성) 
        }
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
    elif source_type == "연관검색어":
        BASE_URL = "https://api.naver.com"
        uri = "/keywordstool"
        url = BASE_URL + uri
        headers = get_header(
            method="GET",
            uri=uri,
            api_key=API_KEY,
            secret_key=SECRET_KEY,
            customer_id=CUSTOMER_ID
        )
        params = {
            "hintKeywords": main_keyword,
            "showDetail": "1"
        }
    else:
        raise ValueError(f"Invalid source_type: {source_type}. Must be '상위판매자' or '연관검색어'.")

    return url, headers, params


# ✅ 여러 개의 User-Agent 중 랜덤 선택
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
]
USER_AGENT = random.choice(USER_AGENTS)

def search_naver_shopping(keyword: str) -> list:
    """
    네이버 쇼핑에서 키워드를 검색하고, 검색 결과에서 상품 URL을 가져옴.
    """
    logger.log(f"🌐 네이버 쇼핑에서 '{keyword}' 검색 실행", level="INFO")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 브라우저 창 숨김 (테스트 시 비활성화 가능)
    options.add_argument("--disable-gpu")  # GPU 사용 안 함
    options.add_argument("--no-sandbox")  # 샌드박스 모드 해제
    options.add_argument("--ignore-certificate-errors")  # SSL 인증서 오류 무시
    options.add_argument("--disable-blink-features=AutomationControlled")  # ✅ Selenium 탐지 방지
    options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
    options.add_argument("--disable-infobars")  # "자동화된 테스트 소프트웨어" 메시지 제거
    options.add_argument(f"user-agent={USER_AGENT}")  # ✅ User-Agent 랜덤 변경
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 불필요한 로그 제거

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # ✅ 네이버 쇼핑 검색 페이지 접속
        search_url = f"https://search.shopping.naver.com/search/all?query={keyword}"
        driver.get(search_url)
        logger.log(f"✅ 검색 실행: {search_url}", level="INFO")
        time.sleep(5)  # ✅ JavaScript 실행을 기다림

        # ✅ 검색 결과가 로드될 때까지 대기
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.compositeCardList_product_list__Ih4JR"))
            )
            logger.log("✅ 상품 목록 로딩 완료.", level="INFO")
        except:
            logger.log("⚠ 상품 목록을 찾지 못함. HTML을 확인하세요.", level="WARNING")

        # ✅ HTML 가져오기
        page_source = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(page_source, "html.parser")

        # ✅ 상품 리스트 찾기
        product_list = soup.select("ul.compositeCardList_product_list__Ih4JR a")

        # ✅ 상품 링크 추출
        product_links = [link["href"] for link in product_list if "href" in link.attrs]
        logger.log(f"✅ 검색된 상품 개수: {len(product_links)}", level="INFO")

        return product_links[:10]  # 상위 10개 상품만 가져옴옴

    except Exception as e:
        logger.log(f"🚨 네이버 쇼핑 검색 실패: {e}", level="ERROR")
        return []

    finally:
        driver.quit()


'''
    네이버의 '네이버쇼핑', '네이버연관검색' 의 결과를 가져오는 함수

'''
def get_naver_tags(main_keyword: str, max_tags: int = 10) -> list:
    # 3. 기존 데이터가 없는 경우 네이버 API 호출 및 데이터 처리
    logger.log(f"기존데이터가 없으므로 네이버 연관검색 수행: 메인키워드 '{main_keyword}'", level="INFO")

    source_type = "상위판매자"
    # source_type = "연관검색어"

    display = 10
    url, headers, params = generate_params_and_headers(source_type, main_keyword, display)
    
    # 각 검색 타입에 따른 API 요청 및 결과 수신
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        full_response = response.json()

        logger.log_separator()
        logger.log("🔍 전체 검색 응답 데이터:")
        logger.log(json.dumps(full_response, indent=4, ensure_ascii=False))
        logger.log_separator()

        response = requests.get(url, headers=headers, params=params)
        data = response.json() # logger.log(f"반환전체 : {data} ")  
            
        
        product_links = [product.get("link") for product in data.get('items', []) if product.get("link")]
        
        logger.log(f"✅ 네이버 쇼핑에서 수집한 상품 링크: {product_links}", level="INFO")

        all_tags = []
        # for product_url in product_links:
        #     tags = get_naver_product_tags(product_url)
        #     all_tags.extend(tags)
        
        
        # tags = get_naver_product_tags(product_links[0])
        tags = get_naver_product_tags("https://smartstore.naver.com/main/products/4252911571")
        all_tags.extend(tags)
        
        final_tags = sorted(set(all_tags))
        logger.log(f"🔍 '{main_keyword}' 최종 태그 리스트: {final_tags}", level="INFO")
        
        return final_tags
    else:
        logger.log(f"🚨 네이버 쇼핑 API 요청 실패: {response.status_code}", level="ERROR")
        return []







def make_keyword(basic_product_name, main_keywords, fixed_keywords, gpt_related_keywords):

    max_length=49

    # 메인키워드 추출
    main_keywords = main_keywords
    logger.log(f"💬 main_keywords : {main_keywords}", level="INFO")

    # 기본 상품명 정리 : 필터링된 고정키워드
    fixed_keywords, processed_fixed_keywords = clean_fixed_keywords(basic_product_name, main_keywords)

    # 🔥 기본 상품명 & 연관 키워드 필터링 (쿠팡 브랜드 네임 및 금지어 제거)
    gpt_related_keywords = [word for word in gpt_related_keywords if word not in COUPANG_FILTER_KEYWORDS + FILTER_KEYWORDS + FILTER_UNIT_KEYWORDS]
    processed_fixed_keywords = [word for word in processed_fixed_keywords if word not in COUPANG_FILTER_KEYWORDS + FILTER_KEYWORDS +FILTER_UNIT_KEYWORDS]
    
    # 카테고리 데이터 로드
    category_dict = load_category_dict()
    

    # 🔥 카테고리 키워드 및 중복문자 필터링
    category_keywords = category_dict.get("모든키워드", [])

    # 필터링 전 GPT 연관 키워드 출력
    logger.log(f"💬 [Before] GPT 연관 키워드 (카테고리 필터 적용 전): {gpt_related_keywords}", level="INFO", also_to_report=True)

    logger.log(f"✅ 카테고리제거, 중복제거" , level="INFO", also_to_report=True)
    # GPT 연관 키워드에서 카테고리 키워드 개수 제한
    gpt_related_keywords = filter_gpt_keywords_by_category(gpt_related_keywords, category_keywords)
    # gpt_related_keywords = remove_redundant_keywords(gpt_related_keywords, prefer_compound=False) #하나씩 가공이므로 중복단어필터링은 제외 

    # 필터링 후 GPT 연관 키워드 출력
    logger.log(f"💬 [After] GPT 연관 키워드 (카테고리 필터 적용 후): {gpt_related_keywords}", level="INFO", also_to_report=True)

    
    # 4️⃣ 글자 수 제한 계산 : 메인 키워드 + 고정 키워드가 차지하는 길이를 먼저 계산하고, 남은 길이(remaining_length)를 구함!
    protected_length = len(main_keywords) + len(" ".join(processed_fixed_keywords)) + 1  # 공백 1개만 고려
    remaining_length = max_length - protected_length

    # 5️⃣ 연관 키워드 랜덤화 후 글자 수 제한 내에서 선택
    random.shuffle(gpt_related_keywords)
    random.shuffle(processed_fixed_keywords)

    # 글자 수 제한 내에서 연관검색어의 키워드 필터링
    filtered_keywords = []
    current_length = 0
    for keyword in gpt_related_keywords:
        if current_length + len(keyword) + 1 > remaining_length:  # +1은 공백 고려
            break
        filtered_keywords.append(keyword)
        current_length += len(keyword) + 1

    # 5️⃣ 최종 조합 (연관 키워드 + 고정 키워드 + 메인 키워드)
    filtered_part = " ".join(filtered_keywords)
    fixed_keywords_part = " ".join(processed_fixed_keywords)
    
    final_keywords = f"{filtered_part} {fixed_keywords_part} {main_keywords}".split()
    final_keywords_unique = list(dict.fromkeys(final_keywords)) # 완전히 동일한 키워드만 중복 제거

    # 최적화된 상품명 생성
    optimized_name = " ".join(final_keywords_unique).strip()

    # 디버깅 정보 출력
    logger.log(f"💬 기본상품명 : {basic_product_name}", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 메인키워드 : {main_keywords}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 고정키워드 : ", fixed_keywords, level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 필터 및 랜덤화된 고정키워드 : ", processed_fixed_keywords, level="INFO", also_to_report=True, separator="none")

    # 최대 3개만 출력
    display_related_keywords = gpt_related_keywords[:3]
    # 로그에 출력
    logger.log(f"💬 연관검색어(3개만출력): {display_related_keywords}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 조합키워드 리스트", final_keywords_unique, level="INFO", also_to_report=True, separator="none")
    logger.log(f"🚀 최적화된 상품명: '{optimized_name}' (글자 수: {len(optimized_name)})", level="INFO", also_to_report=True, separator="dash-2line")
    

    return optimized_name


def process_naming_tag(basic_product_name: str) -> tuple[str, list[str]]:
    """
    상품명을 입력받아 가공된 상품명과 태그 리스트를 반환하는 함수.
    
    Parameters:
    input_string (str): 원본 상품명
    
    Returns:
    tuple[str, list[str]]: (가공된 상품명, 태그 리스트)
    """
    processed_string = basic_product_name  # 예제에서는 원본 그대로 반환

    # 상품명 키워드사전 로드
    dictionary = load_dictionary()

    fixed_keywords = []
    related_keywords = []
    main_keywords = []
    found = False

    for category, data in dictionary.items():
        if "기본상품명" in data:
            for idx, base_name in enumerate(data["기본상품명"]):
                if base_name == processed_string:
                    main_keywords = data.get("제품군", [])
                    fixed_keywords = data.get("고정키워드", [])[idx]
                    related_keywords = data.get("GPT연관검색어", [])
                    logger.log(f" ✅ 입력된 기본상품명 '{processed_string}'이(가) 사전에 존재합니다.", level="INFO")
                    logger.log(f" ✅ 메인키워드: {main_keywords}", level="INFO")
                    logger.log(f" ✅ 고정키워드: {fixed_keywords}", level="INFO")
                    logger.log(f" ✅ 연관키워드: {related_keywords}", level="INFO")
                    found = True
    
    if not found:
        logger.log(f"입력된 상품명 '{processed_string}'이(가) 사전에 존재하지 않습니다.", level="WARNING")

    optimized_name = make_keyword(processed_string, main_keywords, fixed_keywords, related_keywords)

    # 네이버 API를 통해 태그 가져오기

    # related_tags = get_related_tags(" ".join(main_keywords))

    related_tags = get_related_tags(" ".join("파일"))
    logger.log(f"🔍 네이버 API로 가져온 태그: {related_tags}", level="INFO")
    


    return processed_string, fixed_keywords, related_keywords, optimized_name

def main():
    while True:
        # 사용자에게 상품명 입력 요청
        input_name = input("상품명을 입력해 주세요 :  ").strip()
        
        if not input_name:
            logger.log("빈 문자열이 입력되어 프로그램을 종료합니다.", level="ERROR")
            sys.exit(1)
        
        processed_name, fixed_keywords, related_keywords, optimized_name = process_naming_tag(input_name)
        
        # logger.log(f"가공된 상품명: {processed_name}", also_to_report=True)
        # logger.log(f"고정키워드 리스트: {fixed_keywords}", also_to_report=True)
        # logger.log(f"연관키워드 리스트: {related_keywords}", also_to_report=True)
        # logger.log(f"최종상품명: {optimized_name}", also_to_report=True)


if __name__ == "__main__":

    # get_naver_tags("파일")
    search_naver_shopping("핸드폰")

    # main()

