# naver_api.py

import json
import re
import requests
import hashlib
import hmac
import base64
import time
from .related_keywords_filter import filter_related_keywords
from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary


# 이후 이곳을 모듈로서 불러오게 되면 아래의 경로를 지우고 이것을 주석 해제하자. 
# from config.settings import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET  # settings.py에서 직접 가져오기 


import sys
sys.path.append('F:/marketAutomation')
from config.settings import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, API_KEY, SECRET_KEY,CUSTOMER_ID
from keywordOptimization.keyword_combination import analyze_patterns,analyze_related_patterns, combine_keywords

from keywordOptimization.product_info import ProductInfo,ProcessedProductInfo

from utils.log_utils import Logger

# logs 디렉터리에 로그 파일이 생성됩니다.
logger = Logger(log_file="logs/debug.log", enable_console=True)

class Signature:
    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)
        return base64.b64encode(hash.digest()).decode("utf-8")


def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, method, uri, secret_key)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": str(customer_id),
        "X-Signature": signature,
    }

def clean_text(text):
    """
    HTML 태그 제거 및 공백을 정리하여 텍스트를 깔끔하게 출력하는 함수

    Parameters:
    - text (str): HTML 태그가 포함된 원본 텍스트
    
    Returns:
    - clean_text (str): HTML 태그와 공백이 제거된 깨끗한 텍스트
    """
    # 정규식을 사용해 HTML 태그를 모두 제거
    clean_text = re.sub(r'<.*?>', '', text).strip()
    return clean_text

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
            "sort": "sim"
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


def extract_brands_from_patterns(patterns, main_keyword, dictionary, display=10):
    """
    상위판매자 API를 이용하여 패턴 키워드로 검색된 상품의 브랜드명을 추출하고,
    패턴과 동일한 브랜드명을 기준으로 패턴 리스트에서 제거.
    결과로 메인 키워드 데이터에 '네이버연관검색패턴브랜드'를 추가.

    Parameters:
    - patterns (list): 패턴 키워드 리스트.
    - main_keyword (str): 메인 키워드.
    - dictionary (dict): 메인 키워드 데이터를 포함하는 사전.
    - display (int): 검색 결과 개수 (기본값: 10).

    Returns:
    - valid_patterns (list): 브랜드명이 제거된 최종 패턴 리스트.
    """
    brands = set()  # 브랜드명을 중복 없이 저장하기 위한 집합
    valid_patterns = patterns.copy()  # 원본 패턴 리스트를 복사하여 수정 가능하도록 준비

    # 각 패턴을 순회하며 상위판매자 API를 호출
    for pattern in patterns:
        # API 요청에 필요한 URL, 헤더, 파라미터 생성
        url, headers, params = generate_params_and_headers("상위판매자", pattern, display)

        # API 호출
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:  # API 요청 성공 시
            full_response = response.json()  # JSON 응답 데이터를 파싱
            items = full_response.get("items", [])  # 검색 결과에서 'items' 리스트 가져오기

            # 각 검색 결과에서 브랜드명을 추출
            for item in items:
                brand = item.get("brand")  # 'brand' 필드에서 브랜드명 가져오기

                # 유효한 브랜드명만 집합에 추가
                if brand:  # 브랜드명이 None이 아니어야 함
                    brands.add(brand)  # 브랜드명을 집합에 추가 (자동으로 중복 제거)

        else:  # API 요청 실패 시
            # 에러 로그 기록
            logger.log(f"Error fetching brands for pattern '{pattern}' with status {response.status_code}: {response.text}", level="ERROR")

    # 브랜드명과 동일한 패턴을 제거
    for pattern in patterns:
        # 대소문자를 구분하지 않고 브랜드명과 패턴을 비교
        if pattern.lower() in {brand.lower() for brand in brands}:
            valid_patterns.remove(pattern)  # 동일한 패턴명을 valid_patterns에서 제거

    # 메인 키워드 데이터에 '네이버연관검색패턴브랜드' 필드 업데이트
    if main_keyword in dictionary:
        # 기존 데이터가 있으면 '네이버연관검색패턴브랜드' 필드에 새로운 브랜드를 병합
        existing_brands = set(dictionary[main_keyword].get("네이버연관검색패턴브랜드", []))  # 기존 브랜드 가져오기
        dictionary[main_keyword]["네이버연관검색패턴브랜드"] = list(existing_brands | brands)  # 기존 브랜드와 새 브랜드 병합 후 리스트로 저장
    else:
        # 기존 데이터가 없으면 새로운 데이터로 추가
        dictionary[main_keyword] = {"네이버연관검색패턴브랜드": list(brands)}  # 새 브랜드 리스트 추가

    # 변경된 사전을 저장 (파일 등 외부 저장소에 저장)
    logger.log(f"🛑메인키워드 '{main_keyword}'에 '네이버연관검색패턴브랜드' 데이터 사전 업데이트", level="INFO") # 사전 업데이트 로그 기록
    save_dictionary(dictionary)

    

    # 유효한 패턴 리스트 반환 (브랜드명과 중복되지 않는 패턴만 포함)
    return valid_patterns


from keywordOptimization.keyword_filter_never import filter_length

def process_name_filter(basic_product_name, main_keyword, optimized_name):
    """
    상품명을 필터링하고 사전에 저장하며, 고정 키워드를 동적으로 생성하는 함수.

    Parameters:
    - basic_product_name (str): 기본 상품명.
    - main_keyword (str): 메인 키워드.
    - optimized_name (str): 최적화된 상품명.
    
    Returns:
    - str: 필터링된 최종 상품명.
    """
    logger.log_separator()
    logger.log(f"🌀 필터링 시작: '{optimized_name}'", level="INFO")

    # 고정 키워드 생성: 기본 상품명에서 메인 키워드를 제외한 나머지
    basic_keywords = basic_product_name.split()  # 기본 상품명을 단어 단위로 분리
    fixed_keywords = [kw for kw in basic_keywords if kw != main_keyword]  # 메인 키워드를 제외한 나머지 키워드

    # 필터링 수행
    filtered_name = filter_length(
        name=optimized_name,
        max_length=49,
        main_keyword=main_keyword,
        fixed_keywords=fixed_keywords,
        low_priority_keywords=["스타일", "st"]
    )

    logger.log(f"🌀 필터링 완료: '{filtered_name}'  (글자 수: {len(filtered_name)})", level="INFO")

    return filtered_name


def find_main_keyword_by_basic_name(dictionary, basic_product_name):
    for main_keyword, value in dictionary.items():
        # "기본상품명"이 key로 존재하고, 리스트 내에 basic_product_name이 포함되어 있는지 확인
        if "기본상품명" in value and isinstance(value["기본상품명"], list):
            if basic_product_name in value["기본상품명"]:
                return main_keyword
    return None  # 찾지 못한 경우

def generate_optimized_names(basic_product_name, source_type, dictionary, display=10):
    """
    네이버 API를 통해 최적화된 상품명을 생성.
    
    Parameters:
    - naming_item : 상품 정보 객체.
    - source_type (str): API 종류 선택 ("상위판매자" 또는 "연관검색어").
        상위판매자(shopping) : 판매자의 상품등의 정보
        연관검색어(ads) : 연관검색어등의 정보 
    - display (int): 검색 결과 개수 (기본값: 10).
    
    Returns:
    - optimized_name: 네이버검색을 통한 키워드조합후 최종상품명
    """

    # 1. 기본상품명을 통해 그데이터의 메인키워드 추출
    main_keyword = find_main_keyword_by_basic_name(dictionary, basic_product_name)

    # 2. 메인키워드를 통해 메인키워드의 모든 데이터를 사전에서 가져오기
    existing_data = dictionary.get(main_keyword, {})


# =====================  이미 검색을 마친경우 ==========================
    # 이미 연관검색을 마쳤지만 존재하지 않은 경우 ('없음'으로 기록된 경우)
    if (
        existing_data.get("네이버연관검색어") == ["없음"] or
        existing_data.get("패턴") == ["없음"]
    ):
        logger.log(f"✅기존 데이터 사용: 메인키워드 '{main_keyword}' 검색내용이 '없음'으로 기록되어 있으므로 검색 패스!", level="INFO")
        
        # 가공상품명 생성 
        optimized_name = combine_keywords(existing_data, basic_product_name)  # 최적화된 상품명 생성

        #가공상품명 필터링
        filtered_final_name = process_name_filter(basic_product_name, main_keyword, optimized_name)

        return filtered_final_name

    # 이미 연관검색을 마쳐 네이버연관검색어와 패턴이 존해하는 경우
    elif ( "네이버연관검색어" in existing_data and "패턴" in existing_data and # 두가지가 존재하고 
            existing_data["네이버연관검색어"] != [] and  existing_data["패턴"] != [] # 비어있지 않은경우
        ): 
        logger.log(f"✅기존 데이터 사용: 메인키워드 '{main_keyword}' 검색내용이 존재하여 검색 패스!", level="INFO")

        # 가공상품명 생성 
        optimized_name = combine_keywords(existing_data, basic_product_name)  # 최적화된 상품명 생성
        
        #가공상품명 필터링
        filtered_final_name = process_name_filter(basic_product_name, main_keyword, optimized_name)

        return filtered_final_name
    
# =====================  이미 검색을 마친경우 끝 ==========================
    
# =====================  검색을 하지않아 최초로 검색하는 경우 ==========================

    # 3. 기존 데이터가 없는 경우 네이버 API 호출 및 데이터 처리
    logger.log(f"기존데이터가 없으므로 네이버 연관검색 수행: 메인키워드 '{main_keyword}'", level="INFO")
    url, headers, params = generate_params_and_headers(source_type, main_keyword, display)
    
    # 각 검색 타입에 따른 API 요청 및 결과 수신
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        full_response = response.json()

        # logger.log_separator()
        # logger.log("🔍 전체 검색 응답 데이터:")
        # logger.log(json.dumps(full_response, indent=4, ensure_ascii=False))
        # logger.log_separator()


        if source_type == "상위판매자":
            # 상위 판매자 분석
            # 현재의 풀데이터를 보면 '브랜드명' 이 들어 있으니 나중에 만들때 브랜드 명을 제외하면됨. 이건 연관검색어 이후에 사용하자. 

            results = full_response["items"]
            keyword_list = [clean_text(item["title"]) for item in results]
            patterns = analyze_patterns(keyword_list)
            existing_data["패턴"] = patterns  # >> 패턴 저장
            # optimized_name = combine_keywords(naming_item["제품군"], naming_item["고정키워드"], naming_item, patterns)
            # return {"type": "상위판매자분석", "optimized_name": optimized_name}
        
        if source_type == "연관검색어":
            # 연관 검색어 추출
            related_keywords_data = full_response.get("keywordList", [])  # >> 수정: 키워드 데이터가 없을 경우 대비

            
            # 전체 연관 검색어 출력
            # all_related_keywords = [clean_text(keyword["relKeyword"]) for keyword in related_keywords_data]
            # logger.log_separator()
            # logger.log_list("전체 연관검색어 출력", all_related_keywords)


            # 네이버 검색결과 연관검색어가 없어 메인키워드인  자신만 반환된 경우
            if len(related_keywords_data) == 1 and related_keywords_data[0]["relKeyword"] == main_keyword:  

                # 이전 데이터에 데이터를 추가
                existing_data["네이버연관검색어"] = ["없음"]  # '없음'으로 기록
                existing_data["패턴"] = ["없음"]  # 리스트로 "없음" 설정
                existing_data["네이버연관검색패턴브랜드"] = ["없음"]  # 브랜드도 "없음"으로 설정

                logger.log(f"🛑네이버 검색결과 메인키워드의 연관검색어와 패턴이 없어 '[없음]'으로 기록: {main_keyword}", level="INFO")

            # 네이버 검색 후 연관검색어 존재 하는 경우 
            else:

                # 필터링(선별)된 연관 검색어
                filtered_keywords = filter_related_keywords(related_keywords_data)

                # 메인키워드데이터에 연관 키워드 추가 (문자열 키워드만 저장)
                existing_data["네이버연관검색어"] = [keyword["relKeyword"] for keyword in filtered_keywords]
            
                # 상위 연관키워드 및 키워드 랜덤화
                patterns = analyze_related_patterns(filtered_keywords)

                # 패턴키워드를 통한 브랜드 수집 및 패턴키워드 브랜드명 필터링
                # 필터링된 브랜드명 사전에 저장 
                brand_results = extract_brands_from_patterns(patterns, main_keyword, dictionary)
                logger.log_list('필터링된 패턴의 리스트', brand_results)
                logger.log_separator()

                # 브랜드필터링 후 메인키워드 데이터에 패턴 추가
                existing_data["패턴"] = patterns

                logger.log(f"🛑 키워드 '{main_keyword}' 에 '네이버연관검색어 + 패턴' 데이터 업데이트 완료", level="INFO")
            
            save_dictionary(dictionary)  # 네이버 검색관려 사전저장
        
            # 최종 상품명 생성 
            optimized_name = combine_keywords(existing_data, basic_product_name)

            #가공상품명 필터링
            filtered_final_name = process_name_filter(basic_product_name, main_keyword, optimized_name)

            return filtered_final_name

    else:
        error_message = f"Error fetching keywords for {main_keyword} with status {response.status_code}: {response.text}"
        logger.log(error_message, level="ERROR")
        return {"type": "오류처리", "original_name": basic_product_name, "error": error_message}

    

# 테스트용 메인 코드
if __name__ == "__main__":
    # 예시 상품명 리스트
    naming_list = ["9구 멀티옷걸이 블루", "만능 틈새청소솔 블랙", "3공 다이어리 오렌지" ]
    
    # 최적화된 상품명 리스트 가져오기
    optimized_naming_list = generate_optimized_names(naming_list)

    # 결과 출력
    print("최적화된 상품명 리스트:")
    for idx, optimized_name in enumerate(optimized_naming_list, start=1):
        print(f"{idx}. {optimized_name}")
