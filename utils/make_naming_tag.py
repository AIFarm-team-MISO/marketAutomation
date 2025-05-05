import json
import random
import sys
import os
from typing import List
import requests
import json
import time
import re
from collections import Counter
import random

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



def clean_html(text):
    """HTML 태그 제거"""
    return re.sub(r'<.*?>', '', text)

from g2pk import G2p
g2p = G2p()

def remove_brand_from_title_only(title, brand):
    """타이틀에서 브랜드 제거"""
    if brand and brand in title:
        cleaned_title = title.replace(brand, '').strip()
        return cleaned_title, brand
    return title, None

BRAND_MAPPING = {
    "3M": "쓰리엠",
    "TESA": "테사",
    "SCOTCH": "스카치",
    "MONSTER": "몬스터",
    "UHU": "유후"
}

def remove_brand_from_title(title: str, brand: str) -> tuple[str, list]:
    removed = []

    if brand:
        brand_upper = brand.upper()

        # 1. 영문 브랜드 직접 제거
        if brand in title:
            title = title.replace(brand, "")
            removed.append(brand)

        # 2. 맵핑된 한글 브랜드 제거
        if brand_upper in BRAND_MAPPING:
            brand_kor = BRAND_MAPPING[brand_upper]
            if brand_kor in title:
                title = title.replace(brand_kor, "")
                removed.append(brand_kor)

        # 3. g2pk 한글 변환 후 제거 (맵핑 후에도 남은 경우)
        brand_kor_auto = g2p(brand)
        if brand_kor_auto in title:
            title = title.replace(brand_kor_auto, "")
            removed.append(brand_kor_auto)

    return title.strip(), removed



def get_naver_nobrand_names(main_keyword: str) -> list:
    '''
    네이버의 '네이버쇼핑' 의 결과를 가져오는 함수

    '''
    logger.log(f"네이버 연관검색 수행: 메인키워드 '{main_keyword}'", level="INFO")

    source_type = "상위판매자"

    display = 20
    brands = set()  # 브랜드명을 중복 없이 저장하기 위한 집합
    url, headers, params = generate_params_and_headers(source_type, main_keyword, display)
    
    # 각 검색 타입에 따른 API 요청 및 결과 수신
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        full_response = response.json()
        items = full_response.get("items", [])
        cleaned_titles = []
        full_categories = []

        logger.log_separator(title=f"{main_keyword} - 상위 {display}개 상품명 처리 시작", char="=", also_to_report=True)

        for idx, item in enumerate(items):
            title_raw = item.get("title", "")
            brand = item.get("brand", "")
            category1 = item.get("category1", "")
            category2 = item.get("category2", "")
            category3 = item.get("category3", "")
            category4 = item.get("category4", "")

            
            # 1. HTML 태그 제거 → 원본상품명으로 간주
            base_title = clean_html(title_raw)

            # 2. 브랜드 제거
            final_title, removed_brand = remove_brand_from_title(base_title, brand)

            # 3. 로깅
            logger.log(f"{idx+1}. 원본상품명: '{base_title}'", level="INFO", also_to_report=True)
            if removed_brand:
                logger.log(f"   └ ❌ 제거된 브랜드명: '{removed_brand}'", level="INFO", also_to_report=True)
            else:
                logger.log(f"   └ 제거된 브랜드명: 없음", level="INFO", also_to_report=True)
            logger.log(f"   └ 최종 상품명: '{final_title}'", level="INFO", also_to_report=True)

            # 4. 카테고리 정보 출력
            full_category = " > ".join([c for c in [category1, category2, category3, category4] if c])
            logger.log(f"   └ 📚 카테고리: {full_category}", level="INFO", also_to_report=True)


            cleaned_titles.append(final_title)
            full_categories.append(full_category)




        logger.log_separator(char="=", also_to_report=True)
        return cleaned_titles, full_categories
    else:
        logger.log(f"❌ API 호출 실패 - status code: {response.status_code}", level="ERROR")
        return []
    
def safe_int(value, default=0):
    try:
        # '< 10' 형태를 처리
        if isinstance(value, str) and '<' in value:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
    
def filter_related_keywords_by_score(related_keywords_data: list, min_total_search: int = 1000, min_ctr: float = 1.0, max_depth: int = 5) -> list:
    """
    조회수 + CTR + 검색깊이를 기준으로 연관 검색어를 필터링하는 함수.

    Parameters:
    ----------
    related_keywords_data : list
        네이버 API에서 반환된 'keywordList' 원본 데이터 리스트

    min_total_search : int, optional (default=1000)
        PC + 모바일 합산 조회수가 이 값 이상인 키워드만 필터링

    min_ctr : float, optional (default=1.0)
        PC 또는 모바일 CTR이 이 값 이상인 키워드만 필터링

    max_depth : int, optional (default=5)
        평균 검색 깊이가 이 값 이하인 키워드만 필터링

    Returns:
    -------
    list
        필터링된 relKeyword 리스트 (연관도가 높은 키워드)
    """
    filtered_keywords = []

    for item in related_keywords_data:
        pc_qc = safe_int(item.get("monthlyPcQcCnt", 0))
        mobile_qc = safe_int(item.get("monthlyMobileQcCnt", 0))
        pc_ctr = safe_float(item.get("monthlyAvePcCtr", 0.0))
        mobile_ctr = safe_float(item.get("monthlyAveMobileCtr", 0.0))
        depth = safe_int(item.get("plAvgDepth", 10))

        total_search = pc_qc + mobile_qc

        if (
            total_search >= min_total_search and
            (pc_ctr >= min_ctr or mobile_ctr >= min_ctr) and
            depth <= max_depth
        ):
            filtered_keywords.append(item)  # relKeyword만이 아닌 전체 dict 반환

    return filtered_keywords

def split_and_log_keywords(related_keywords_data: list, max_tags: int = 10):
    """
    연관검색어 데이터를 CTR 기준 & 조회수 기준으로 각각 정렬하여
    5개씩 줄바꿈하여 출력하는 함수.

    Parameters:
    ----------
    related_keywords_data : list
        네이버 API에서 반환된 연관검색어 'keywordList' 데이터 (dict 리스트)
    
    max_tags : int, optional (default=10)
        CTR / 조회수 각각 최대 몇 개의 키워드를 출력할지 설정
    """
    # CTR 기준 정렬
    ctr_sorted = sorted(related_keywords_data, key=lambda x: max(
        float(x.get("monthlyAvePcCtr", 0) or 0),
        float(x.get("monthlyAveMobileCtr", 0) or 0)
    ), reverse=True)

    # 조회수 기준 정렬
    view_sorted = sorted(related_keywords_data, key=lambda x: (
        int(x.get("monthlyPcQcCnt", 0) or 0) + int(x.get("monthlyMobileQcCnt", 0) or 0)
    ), reverse=True)

    # CTR 높은 순
    logger.log("🔵 CTR 높은 순 추천 키워드:", level="INFO")
    for i in range(0, min(max_tags, len(ctr_sorted)), 3):
        chunk = ctr_sorted[i:i+3]
        formatted = ', '.join([f"{x['relKeyword']} (CTR: {x.get('monthlyAveMobileCtr', '-')})" for x in chunk])
        logger.log(f"    {formatted}", level="INFO")

    # 조회수 높은 순
    logger.log("🟣 조회수 높은 순 추천 키워드:", level="INFO")
    for i in range(0, min(max_tags, len(view_sorted)), 3):
        chunk = view_sorted[i:i+3]
        formatted = ', '.join([
            f"{x['relKeyword']} (조회수: {int(x.get('monthlyPcQcCnt', 0) or 0) + int(x.get('monthlyMobileQcCnt', 0) or 0)})"
            for x in chunk
        ])
        logger.log(f"    {formatted}", level="INFO")









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
    # logger.log(f"💬 [Before] GPT 연관 키워드 (카테고리 필터 적용 전): {gpt_related_keywords}", level="INFO", also_to_report=True)

    logger.log(f"✅ 카테고리제거, 중복제거" , level="INFO", also_to_report=True)
    # GPT 연관 키워드에서 카테고리 키워드 개수 제한
    gpt_related_keywords = filter_gpt_keywords_by_category(gpt_related_keywords, category_keywords)
    # gpt_related_keywords = remove_redundant_keywords(gpt_related_keywords, prefer_compound=False) #하나씩 가공이므로 중복단어필터링은 제외 

    # 필터링 후 GPT 연관 키워드 출력
    # logger.log(f"💬 [After] GPT 연관 키워드 (카테고리 필터 적용 후): {gpt_related_keywords}", level="INFO", also_to_report=True)

    
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
    logger.log(f"✅ 메인키워드 : {main_keywords}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 고정키워드 : ", fixed_keywords, level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 필터 및 랜덤화된 고정키워드 : ", processed_fixed_keywords, level="INFO", also_to_report=True, separator="dash-1line")

    # 최대 3개만 출력
    display_related_keywords = gpt_related_keywords[:5]
    # 로그에 출력
    logger.log(f"💬 연관검색어(5개만): {display_related_keywords}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 조합키워드 리스트", final_keywords_unique, level="INFO", also_to_report=True, separator="none")
    logger.log(f"✅ 최적화된 상품명: '{optimized_name}' (글자수: {len(optimized_name)})", level="INFO", also_to_report=True, separator="dash-2line")
    

    return optimized_name

def remove_numbers_english_special(titles):
    """
    숫자, 영문, 특수문자 제거 및 공백 정리 함수

    :param titles: 상품명 리스트
    :return: 정제된 상품명 리스트
    """
    cleaned_list = []
    for title in titles:
        # 1. 숫자 + 영문 + 특수문자 제거 (한글 + 공백만 남김)
        cleaned_title = re.sub(r'[^가-힣\s]', '', title)
        
        # 2. 여러 공백을 하나로 축소
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
        
        # 3. 양쪽 공백 제거
        cleaned_title = cleaned_title.strip()

        logger.log(f"🔵정리된 상품명: '{cleaned_title}'", level="INFO", also_to_report=True)
        cleaned_list.append(cleaned_title)
    return cleaned_list

from collections import Counter
from utils.global_logger import logger

def analyze_keyword_frequencies(keyword_list: list[str], main_keyword: str, top_n: int = 5) -> dict:
    """
    상품명 리스트에서 키워드를 추출하고, 메인 키워드를 제외한 빈도 분석을 수행하는 함수

    Parameters:
    ----------
    keyword_list : list of str
        상위판매자 상품명 리스트 (예: ["초강력 실리콘 테이프", "양면테이프 투명 나노"])

    main_keyword : str
        분석에서 제외할 대표 키워드 (예: "양면테이프")

    top_n : int (default: 5)
        빈도우위 키워드에서 몇 개까지 상위 키워드로 구분할지

    Returns:
    -------
    dict:
        {
            '빈도우위': [...],   # 상위 빈도 키워드
            '빈도하위': [...],   # 하위 빈도 키워드
            '전체빈도': Counter 객체
        }
    """
    all_keywords = []
    for title in keyword_list:
        all_keywords.extend(title.split())

    filtered_keywords = [kw for kw in all_keywords if kw != main_keyword]
    counter = Counter(filtered_keywords)
    sorted_keywords = counter.most_common()

    frequent_keywords = [kw for kw, _ in sorted_keywords[:top_n]]
    less_frequent_keywords = [kw for kw, _ in sorted_keywords[top_n:]]

    # 새로운 출력 형식
    def format_and_log_keywords(title: str, keywords: List[str]):
        if not keywords:
            logger.log(f"{title}: 없음")
            return

        lines = []
        line = []
        for i, kw in enumerate(keywords):
            freq = counter[kw]
            line.append(f"{kw}({freq})")
            if (i + 1) % 7 == 0:
                lines.append(", ".join(line))
                line = []
        if line:
            lines.append(", ".join(line))

        logger.log(title)
        for ln in lines:
            logger.log(ln)
    logger.log_separator(char="=", also_to_report=True)
    format_and_log_keywords("🔝 빈도우위 키워드 🔝 ", frequent_keywords)
    logger.log_separator(char="-", also_to_report=True)
    format_and_log_keywords("🧵 빈도하위 키워드 🧵 ", less_frequent_keywords)
    logger.log_separator(char="=", also_to_report=True)

    return {
        '빈도우위': frequent_keywords,
        '빈도하위': less_frequent_keywords,
        '전체빈도': counter
    }






def finalize_product_names(
    main_keyword: str,
    fixed_keywords: list,
    max_length: int,
    naver_product_combi: dict,
    include_fixed: bool = True
):
    """
    메인키워드 + 혼합형/롱테일형 + (선택적으로) 고정키워드를 조합하여
    최종 상품명을 생성하는 함수. 고정키워드는 항상 마지막에 위치.

    Parameters:
    ----------
    main_keyword : str
        필수로 포함할 메인 키워드 (ex: "양면테이프")

    fixed_keywords : list
        고정 키워드 리스트 (ex: ['무지', '크라프트', '종이'])
        - 고정키워드는 항상 상품명의 마지막에 위치함.

    max_length : int
        최종 상품명의 최대 글자 수 제한 (ex: 50)

    naver_product_combi : dict
        generate_keyword_combinations() 함수의 반환값

    include_fixed : bool, optional (default=True)
        고정 키워드 사용 여부

    Returns:
    -------
    dict
        {
            "혼합형_상품명": [...],     # 최종 혼합형 상품명 리스트
            "롱테일형_상품명": [...]    # 최종 롱테일형 상품명 리스트
        }
    """
    results = {"혼합형_상품명": [], "롱테일형_상품명": []}

    # 1) 혼합형 조합 생성
    for combo in naver_product_combi["혼합형"]:
        words = [main_keyword] + combo.split()
        if include_fixed:
            words.extend(fixed_keywords) # 고정키워드는 맨 뒤에 위치

        # 문자수 체크 및 자동 컷팅
        final_name = ""
        for word in words:
            if len(final_name + " " + word) <= max_length:
                final_name = (final_name + " " + word).strip()
            else:
                break

        results["혼합형_상품명"].append(final_name)

    # 2) 롱테일형 조합 생성
    for combo in naver_product_combi["롱테일형"]:
        words = [main_keyword] + combo.split()
        if include_fixed:
            words.extend(fixed_keywords)  # 수정!  # 고정키워드는 맨 뒤에 위치

        # 문자수 체크 및 자동 컷팅
        final_name = ""
        for word in words:
            if len(final_name + " " + word) <= max_length:
                final_name = (final_name + " " + word).strip()
            else:
                break

        results["롱테일형_상품명"].append(final_name)

    return results


def update_dictionary_with_naver_keywords(dictionary, processed_string, main_keywords, fixed_keywords, naver_product_combi):
    """
    기존 사전에서 '기본상품명' 위치를 찾고, 없으면 신규로 등록하며 네이버검색 키워드도 저장.

    Parameters:
    ----------
    dictionary : dict
        기존 키워드 사전

    processed_string : str
        입력된 기본상품명 (예: "풍선막대 풍선캡 6세트 1봉")

    main_keywords : str
        사용자가 입력한 메인 키워드 (예: "풍선막대")

    fixed_keywords : list
        고정키워드 리스트 (예: ['풍선캡', '6세트', '1봉'])

    naver_product_combi : dict
        generate_keyword_combinations() 함수의 반환값
    """
    found = False

    for category, data in dictionary.items():
        if "기본상품명" in data:
            if processed_string in data["기본상품명"]:
                # 기존 카테고리에 네이버 키워드만 업데이트
                dictionary[category]["네이버검색상위"] = naver_product_combi.get("빈도우위", [])
                dictionary[category]["네이버검색하위"] = naver_product_combi.get("빈도하위", [])
                
                logger.log(f"📚 사전에 네이버검색상위 키워드 저장: {dictionary[category]['네이버검색상위']}", level="INFO")
                logger.log(f"📚 사전에 네이버검색하위 키워드 저장: {dictionary[category]['네이버검색하위']}", level="INFO")
                
                found = True
                break

    if not found:
        # 신규 카테고리 생성 및 저장
        dictionary[main_keywords] = {
            "기본상품명": [processed_string],
            "제품군": main_keywords,
            "고정키워드": [fixed_keywords],
            "GPT연관검색어": [],
            "네이버검색상위": naver_product_combi.get("빈도우위", []),
            "네이버검색하위": naver_product_combi.get("빈도하위", []),
            "브랜드키워드": [],
            "용도": [],
            "사양": [],
            "스타일": [],
            "기타 카테고리": []
        }

        logger.log(f"✅ 신규 카테고리 '{main_keywords}'를 생성하고 기본상품명을 '{processed_string}'으로 등록했습니다.", level="INFO")

    save_dictionary(dictionary)
    logger.log("💾 사전이 성공적으로 업데이트 및 저장되었습니다.", level="INFO")


from collections import Counter

def log_top_categories(full_categories: list, top_n: int = 3):
    """
    중복 제거 후 가장 많이 사용된 카테고리 상위 N개를 출력하는 함수.

    Parameters:
    ----------
    full_categories : list
        네이버 API에서 가져온 카테고리 트리 리스트

    top_n : int
        출력할 카테고리 개수 (기본값 3개)
    """
    # 중복 제거 + 빈도수 집계
    counter = Counter(full_categories)
    most_common = counter.most_common(top_n)

    logger.log("📚 네이버 상위 카테고리 TOP 3:", level="INFO")
    for idx, (cat, count) in enumerate(most_common, start=1):
        logger.log(f"    {idx}. {cat} (빈도: {count})", level="INFO")

def get_process_naming(basic_product_name: str) -> tuple[str, list[str]]:
    """
    상품명을 입력받아 
    - 연관검색어 상품명 출력
    - 네이버 상위검색 키워드 상품명 출력
    
    Parameters:
    input_string (str): 원본 상품명
    
    Returns:
    tuple[str, list[str]]: (가공된 상품명, 태그 리스트)

    """

    optimized_name = ""
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
                # 연관검색어 조합 상품명 
                    optimized_name = make_keyword(processed_string, main_keywords, fixed_keywords, related_keywords)
    
    if not found:
        logger.log(f"입력된 상품명 '{processed_string}'이(가) 사전에 존재하지 않습니다.", level="WARNING")

        # 사용자로부터 메인키워드 수동 입력 받기
        user_input = input("📝 사전에 없는 상품입니다. 메인 키워드를 입력해주세요 (예: '풍선막대') 또는 Enter 입력 시 종료됩니다: ").strip()
        
        if not user_input:
            logger.log("⛔ 메인 키워드가 입력되지 않아 프로그램을 종료합니다.", level="ERROR")
            exit(0)
        
        # 입력된 메인 키워드를 할당
        main_keywords = user_input
        logger.log(f"✅ 사용자 입력 메인키워드: {main_keywords}", level="INFO")
        
           
    naver_product_combi, full_categories = get_naver_result(main_keywords)

    log_enriched_keyword_result(naver_product_combi)

    logger.log(f"💬 GPT상품명 : {optimized_name}", level="INFO")
    log_top_categories(full_categories)
    logger.log(f"✅ 네이버 메인키워드 : ' {main_keywords} '", level="INFO")
    logger.log_separator(char="-", also_to_report=True)



    # 👉 사전에 네이버 키워드 저장
    # update_dictionary_with_naver_keywords(dictionary, processed_string, main_keywords, fixed_keywords, naver_product_combi)
    

    
    return processed_string, fixed_keywords, related_keywords, optimized_name

def log_enriched_keyword_result(result: dict):
    """
    enrich_keyword_data_with_naver_stats 결과를 로깅 출력하는 함수

    Parameters:
    -----------
    result : dict
        {
            '빈도우위': [...],
            '빈도하위': [...],
            '연관키워드': [...],
            '혼합형': [...],           # (선택적)
            '롱테일형': [...]          # (선택적)
        }
    """
    logger.log_separator(char="=", also_to_report=True)
    

    # 🌀 롱테일형 조합 1️⃣, 2️⃣, 3️⃣
    # if "롱테일형" in result:
    #     logger.log_separator(title="🛑 네이버 상위 10개 롱테일형 조합🛑", char="=", also_to_report=True)
    #     for idx, combo in enumerate(result["롱테일형"][:10], start=1):
    #         logger.log(f"🌀롱테일형 {idx}: {combo}", level="INFO", also_to_report=True)

    if "연관키워드" in result:
        filtered_rel_keywords = [
            kw for kw in result['연관키워드'] if '(낮음)' in kw or '(중간)' in kw
        ]
        if filtered_rel_keywords:
            logger.log_list("🛑연관키워드(경쟁강도: 중간 이하)", filtered_rel_keywords, level="INFO", also_to_report=True)
        else:
            logger.log("ℹ️ 연관 키워드 중 '중간 이하' 경쟁강도 키워드는 없습니다.", level="INFO", also_to_report=True)

    logger.log_separator(char="=", also_to_report=True)



    # 🧵 롱테일형 키워드
    if "빈도하위" in result:
        low_keywords_preview = ', '.join(result["빈도하위"][:15])
        logger.log(f"🔥1️⃣ 빈도하위 : {low_keywords_preview}", level="INFO", also_to_report=True)
        logger.log_separator(char="-", also_to_report=True)


    # 🔝 혼합형 키워드
    if "빈도우위" in result:
        top_keywords_preview = ', '.join(result["빈도우위"][:13])
        logger.log(f"📚2️⃣ 빈도우위 : {top_keywords_preview}", level="INFO", also_to_report=True)
        logger.log_separator(char="-", also_to_report=True)

def safe_int(value):
    """네이버 API의 '< 10' 같은 값을 안전하게 정수로 변환하는 유틸 함수."""
    try:
        if isinstance(value, str) and "<" in value:
            return 0
        return int(value)
    except (ValueError, TypeError):
        return 0

def safe_float(value):
    """None, 빈 문자열 등도 안전하게 float 처리."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def enrich_keyword_data_with_naver_stats(main_keyword: str, keyword_dict: dict) -> dict:
    """
    빈도우위/하위 키워드에 대해, 연관검색어 API를 통해
    해당 키워드가 포함되어 있는지 여부 및 경쟁강도를 반환합니다.

    """

    combined_keywords = keyword_dict.get('빈도우위', []) + keyword_dict.get('빈도하위', [])
    filtered_keywords = [kw for kw in combined_keywords if main_keyword in kw]
    # logger.log_list(f"🔎 메인키워드 '{main_keyword}'가 포함된 키워드", filtered_keywords, level="INFO")

    enriched_related_keywords = []

    for kw in filtered_keywords:
        try:
            source_type = "연관검색어"
            display = 20
            url, headers, params = generate_params_and_headers(source_type, kw, display)

            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                logger.log(f"❌ '{kw}' 연관검색어 API 호출 실패 - status code: {response.status_code}", level="WARNING")
                continue

            result = response.json()
            related_keywords = result.get("keywordList", [])

            # 해당 키워드가 실제 연관검색 결과에 포함되었는지 확인
            found_comp = "없음"
            for item in related_keywords:
                if item.get("relKeyword") == kw:
                    found_comp = item.get("compIdx", "없음")
                    break

            enriched_related_keywords.append(f"{kw}({found_comp})")
            #  logger.log(f"✅ 키워드 '{kw}' → 경쟁강도: {found_comp}", level="INFO")

        except Exception as e:
            logger.log(f"❌ 키워드 '{kw}' 처리 중 예외 발생: {str(e)}", level="ERROR")

    # 기존 keyword_dict에 '연관키워드' 추가
    keyword_dict["연관키워드"] = enriched_related_keywords
    return keyword_dict


def get_naver_result(main_keywords):
    # 네이버 API를 통해 상위판매자 상품명 가져오기 
    nobrand_names, full_categories = get_naver_nobrand_names(main_keywords)

    # 숫자와 영문 제거
    clean_names = remove_numbers_english_special(nobrand_names)

    # 상위상품명중 키워드의 빈도수를 확인
    naver_top_keywords = analyze_keyword_frequencies(clean_names, main_keywords, top_n=5)

    # 빈도키워드중 연관검색어 확인 
    enriched_top_keywords = enrich_keyword_data_with_naver_stats(main_keywords, naver_top_keywords)

    return enriched_top_keywords, full_categories

def main():
    optimized_name = None

    while True:
    
        # 👉 키워드 기반 검색 모드
        main_keyword = input("🔍 메인 키워드를 입력해 주세요 :  ").strip()
        if not main_keyword:
            logger.log("빈 키워드가 입력되어 프로그램을 종료합니다.", level="ERROR")
            sys.exit(1)

        # 네이버 상품명 & 카테고리만 조회
        naver_product_combi, full_categories = get_naver_result(main_keyword)
        log_enriched_keyword_result(naver_product_combi)

        if optimized_name is not None:
            logger.log(f"💬 GPT상품명 : {optimized_name}", level="INFO")
        log_top_categories(full_categories)
        logger.log(f"✅ 네이버 메인키워드 : ' {main_keyword} '", level="INFO")
        logger.log_separator(char="-", also_to_report=True)


        # 상품명과 검색을 나누어 실행 

        # mode = input("🔵 검색 모드 선택: 상품명 검색(Enter) | 메인 키워드 검색 (0) > ").strip()

        # if mode == "0":
        #     # 👉 키워드 기반 검색 모드
        #     main_keyword = input("🔍 메인 키워드를 입력해 주세요 :  ").strip()
        #     if not main_keyword:
        #         logger.log("빈 키워드가 입력되어 프로그램을 종료합니다.", level="ERROR")
        #         sys.exit(1)

        #     # 네이버 상품명 & 카테고리만 조회
        #     naver_product_combi, full_categories = get_naver_result(main_keyword)
        #     log_enriched_keyword_result(naver_product_combi)

        #     if optimized_name is not None:
        #         logger.log(f"💬 GPT상품명 : {optimized_name}", level="INFO")
        #     log_top_categories(full_categories)
        #     logger.log(f"✅ 네이버 메인키워드 : ' {main_keyword} '", level="INFO")
        #     logger.log_separator(char="-", also_to_report=True)
    

        # else:
        #     # 👉 기본 상품명 검색 모드
        #     input_name = input("🔍 기본상품명을 입력해 주세요 :  ").strip()
        #     if not input_name:
        #         logger.log("빈 문자열이 입력되어 프로그램을 종료합니다.", level="ERROR")
        #         sys.exit(1)

        #     processed_name, fixed_keywords, related_keywords, optimized_name = get_process_naming(input_name)

import random      
from playwright.sync_api import sync_playwright

def get_product_tags(keyword="귀고무"):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()


        # 1. 검색 페이지 접속
        search_url = f"https://search.shopping.naver.com/ns/search?query={keyword}"
        page.goto(search_url)
        page.wait_for_timeout(3000)

        # 2. 첫 번째 상품 추출
        items = page.query_selector_all("ul[class*='compositeCardList_product_list'] > li")
        if not items:
            print("⚠️ 상품 리스트를 찾을 수 없습니다.")
            browser.close()
            return

        first_item = items[0]
        link_el = first_item.query_selector("a[class*='basicProductCard_link']")
        link = link_el.get_attribute("href") if link_el else None

        if not link:
            print("⚠️ 링크를 찾을 수 없습니다.")
            browser.close()
            return

        print(f"🔗 첫 번째 상품 링크: {link}")

        # 3. 상세 페이지 열기
        detail_page = context.new_page()
        detail_page.goto(link)
        detail_page.wait_for_load_state("networkidle")  # 로딩 완료까지 대기
        detail_page.wait_for_timeout(1000)

        # 스크롤로 태그를 로딩 시도
        print("🔽 스크롤 다운 중...")
        for i in range(5):
            print(f"🔽 스크롤 {i+1}회차")
            detail_page.evaluate("window.scrollBy(0, 1000)")
            detail_page.wait_for_timeout(1000)

        try:
            tag_elements = detail_page.query_selector_all("ul._3Vox1DKZiA > li > a")
            tags = [tag.inner_text().strip() for tag in tag_elements if tag.inner_text().strip()]
            if tags:
                print(f"\n🔖 추출된 태그 ({len(tags)}개): {tags}")
            else:
                print("⚠️ 태그 요소가 비어있습니다.")
        except Exception as e:
            print("⚠️ 태그 영역을 찾을 수 없습니다.", str(e))






        browser.close()
        return tags

if __name__ == "__main__":
    '''
        1. 상품명를 입력하면 사전를 조회하여 기존 상품명이 존재한다면 
        해당 사전내용의 메인키워드, 보조키워드, 연관검색어 를 가져온다. 
        그리고 조회된 메인키워드로 네이버검색 실행 

        2. 만약 상품명이 없다면 키워드를 다시 묻고 키워드를 입력하면 네이버조회
    
    '''

    # get_naver_tags("파일")

    # 네이버연결 - 테스트중
    # search_naver_shopping("핸드폰")

    # 네이버검색에서 태그가져오기
    # get_product_tags()


    main()












"""


    03/29일 이전의 함수 단순히 빈도만으로 조합하는 함수 

def generate_keyword_combinations(keyword_list, main_keyword, top_n=4, num_combinations=3, mix_count=6, longtail_count=6):
    
    상품명 키워드를 분석하여 혼합형/롱테일형 조합을 생성하는 함수

    

    1. 빈도 분석:
        - 입력된 keyword_list(상품명 리스트)에서 키워드를 모두 추출한 뒤,
          메인 키워드를 제외하고 빈도수를 분석합니다.
        - 분석된 키워드를 '빈도우위 키워드'와 '빈도하위 키워드'로 나눕니다.
    
    2. 혼합형 조합:
        - 빈도우위 키워드(top_n 개)를 고정으로 넣고,
          빈도하위 키워드에서 mix_count - top_n 개를 랜덤으로 추가해 조합합니다.
        - num_combinations 값에 따라 N개의 혼합형 조합을 생성합니다.

    3. 롱테일형 조합:
        - 빈도우위 키워드를 사용하지 않고,
          빈도하위 키워드에서 longtail_count 개를 랜덤으로 선택해 조합합니다.
        - num_combinations 값에 따라 N개의 롱테일형 조합을 생성합니다.
    
    Parameters:
    ----------
    keyword_list : list
        정제된 상품명 리스트 (각 항목은 띄어쓰기로 구분된 문자열)
        예: ["초강력 실리콘 테이프 양면테이프 투명 나노 젤"]

    main_keyword : str
        빈도 분석에서 제외할 메인 키워드
        예: "양면테이프"

    top_n : int, optional (default=3)
        혼합형 조합 시 고정으로 사용할 '빈도우위 키워드'의 개수

    num_combinations : int, optional (default=3)
        혼합형 및 롱테일형 각각 몇 개의 조합을 생성할지 결정

    mix_count : int, optional (default=5)
        혼합형 조합에서 최종적으로 사용될 키워드 개수 (ex. 빈도우위 3개 + 하위 2개)

    longtail_count : int, optional (default=5)
        롱테일형 조합에서 사용할 하위 키워드 개수
    
    Returns:
    -------
    dict
        {
            "혼합형": [...],           # 혼합형 조합 리스트
            "롱테일형": [...],         # 롱테일형 조합 리스트
            "빈도우위": [...],         # 빈도우위 키워드 리스트
            "빈도하위": [...]          # 빈도하위 키워드 리스트
        }

    Notes:
    ------
    - 혼합형은 SEO 노출에 유리한 **핵심 키워드**를 활용한 조합입니다.
    - 롱테일형은 틈새 타겟팅을 위한 **비교적 사용빈도가 낮은 키워드**를 활용한 조합입니다.
    - mix_count와 longtail_count 값을 조절하여 짧거나 긴 상품명 전략을 유동적으로 설정할 수 있습니다.
    
    
    all_keywords = []
    for title in keyword_list:
        all_keywords.extend(title.split())

    filtered_keywords = [kw for kw in all_keywords if kw != main_keyword]
    counter = Counter(filtered_keywords)
    sorted_keywords = counter.most_common()

    frequent_keywords = [kw for kw, _ in sorted_keywords[:top_n]]
    less_frequent_keywords = [kw for kw, _ in sorted_keywords[top_n:]]

    logger.log_list("빈도우위 키워드", frequent_keywords, level="INFO", also_to_report=True)
    logger.log_list("빈도하위 키워드", less_frequent_keywords, level="INFO", also_to_report=True)

    # 혼합형 조합 생성
    mixed_combinations = []
    for _ in range(num_combinations):
        remaining_count = max(0, mix_count - len(frequent_keywords))
        random_sample = random.sample(less_frequent_keywords, min(remaining_count, len(less_frequent_keywords)))
        combination = frequent_keywords + random_sample
        mixed_combinations.append(' '.join(combination))

    # 롱테일형 조합 생성
    longtail_combinations = []
    for _ in range(num_combinations):
        random_sample = random.sample(less_frequent_keywords, min(longtail_count, len(less_frequent_keywords)))
        longtail_combinations.append(' '.join(random_sample))

    return {
        "혼합형": mixed_combinations,
        "롱테일형": longtail_combinations,
        "빈도우위": frequent_keywords,
        "빈도하위": less_frequent_keywords
    }


    def log_combinations(result, main_keywords):
    logger.log(f"🔵메인키워드 : '{main_keywords}'", level="INFO", also_to_report=True, separator="2line")

    # 혼합형 조합
    logger.log_separator(title="✅ 네이버 상위 10개 혼합형 조합✅", char="=", also_to_report=True)
    for idx, combo in enumerate(result["혼합형"], start=1):
        logger.log(f"🔥혼합형 {idx}: {combo}", level="INFO", also_to_report=True)

    # 혼합형과 연관된 빈도우위 키워드 출력(최대 10개)
    frequent_keywords = ', '.join(result["빈도우위"][:13])
    logger.log(f"🔥📚빈도우위 키워드: {frequent_keywords}", level="INFO", also_to_report=True)
    logger.log_separator(char="-", also_to_report=True)

    # 롱테일형 조합
    logger.log_separator(title="🛑 네이버 상위 10개 롱테일형 조합🛑", char="=", also_to_report=True)
    for idx, combo in enumerate(result["롱테일형"], start=1):
        logger.log(f"🌀롱테일형 {idx}: {combo}", level="INFO", also_to_report=True)

    # 롱테일형과 연관된 빈도하위 키워드 출력(최대 10개)
    less_frequent_keywords = ', '.join(result["빈도하위"][:13])
    logger.log(f"🌀📚빈도하위 키워드: {less_frequent_keywords}", level="INFO", also_to_report=True)
    logger.log_separator(char="=", also_to_report=True)

def log_combinations_final(final_names, main_keywords):
    logger.log(f"🔵메인키워드 : '{main_keywords}'", level="INFO", also_to_report=True, separator="2line")

    # 💥 최종 상품명 출력 (final_names)
    logger.log_separator(title="🎯 최종 혼합형 상품명 🎯", char="=", also_to_report=True)
    for idx, name in enumerate(final_names["혼합형_상품명"], start=1):
        logger.log(f"✅혼합형 최종 {idx}: {name} ({len(name)})", level="INFO", also_to_report=True)
    logger.log_separator(char="-", also_to_report=True)

    logger.log_separator(title="🎯 최종 롱테일형 상품명 🎯", char="=", also_to_report=True)
    for idx, name in enumerate(final_names["롱테일형_상품명"], start=1):
        logger.log(f"🛑롱테일형 최종 {idx}: {name}({len(name)})", level="INFO", also_to_report=True)
    logger.log_separator(char="-", also_to_report=True)

def get_naver_relate_keywords(main_keyword: str, max_tags: int = 15) -> list:
    '''
    네이버의 '네이버쇼핑' API를 통해 연관검색어를 가져오고,
    조회수 + CTR + 검색깊이를 기준으로 필터링하는 함수.

    Parameters:
    ----------
    main_keyword : str
        연관검색어를 가져올 메인 키워드

    max_tags : int, optional (default=10)
        최대 가져올 연관검색어 개수

    Returns:
    -------
    list
        필터링된 연관검색어 리스트
    '''
    logger.log(f"🟢 네이버 연관검색 수행: 메인키워드 '{main_keyword}'", level="INFO")

    source_type = "연관검색어"
    display = 20  # API 최대 요청 수

    url, headers, params = generate_params_and_headers(source_type, main_keyword, display)
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        full_response = response.json()

        # API 원본 로그 출력
        # import json
        # logger.log("🔍 API 응답 전체 데이터:", level="DEBUG", also_to_report=True)
        # logger.log(json.dumps(full_response, indent=4, ensure_ascii=False), level="DEBUG", also_to_report=True)

        raw_related_keywords = full_response.get("keywordList", [])

        # 필터링 실행 기준값
        # filtered_keywords = filter_related_keywords_by_score(
        #     raw_related_keywords,
        #     min_total_search=1000,
        #     min_ctr=1.0,
        #     max_depth=5
        # )
        filtered_keywords = filter_related_keywords_by_score(
            raw_related_keywords,
            min_total_search=500,
            min_ctr=1.5,
            max_depth=1
        )


        # 최대 max_tags 제한
        selected_keywords = filtered_keywords[:max_tags]

        logger.log(f"🟢 최종 필터링된 연관검색어({len(selected_keywords)}개):", level="INFO")
        # ✨ CTR / 조회수 기준으로 나누어 출력
        split_and_log_keywords(filtered_keywords, max_tags=max_tags)

        # 실제 반환용으로는 키워드만 리스트 반환
        selected_keywords = [kw['relKeyword'] for kw in filtered_keywords[:max_tags]]
        return selected_keywords

    else:
        logger.log(f"❌ 네이버 API 호출 실패 - status code: {response.status_code}", level="ERROR")
        return []

"""