# naver_api.py

import re
import requests

# 이후 이곳을 모듈로서 불러오게 되면 아래의 경로를 지우고 이것을 주석 해제하자. 
# from config.settings import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET  # settings.py에서 직접 가져오기 


import sys
sys.path.append('F:/marketAutomation')
from config.settings import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from keywordOptimization.keyword_combination import analyze_patterns,combine_keywords

from keywordOptimization.product_info import ProductInfo,ProcessedProductInfo

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

def generate_optimized_names(naming_item: ProductInfo, display=10) -> ProcessedProductInfo:
    """
    네이버 쇼핑 API를 통해 최적화된 상품명을 생성하여 ProcessedProductInfo 객체로 반환합니다.
    
    Parameters:
    - naming_item (ProductInfo): 개별 상품의 기본 정보와 키워드를 포함하는 객체.
    - display (int): API 요청 시 반환할 상위 검색 결과 개수 (기본값: 10)
    
    Returns:
    - ProcessedProductInfo: 최적화된 이름을 포함하는 ProcessedProductInfo 객체.
    """
    
    # 네이버 쇼핑 API 엔드포인트 URL 설정
    url = "https://openapi.naver.com/v1/search/shop.json"
    
    # API 호출 시 필요한 인증 헤더 설정
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,        # 네이버 API Client ID
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET # 네이버 API Client Secret
    }

    # `ProcessedProductInfo` 객체 생성
    processed_product = ProcessedProductInfo(
        original_name=naming_item.original_name,
        main_keyword=naming_item.main_keyword,
        fixed_keywords=naming_item.fixed_keywords,  # 고정 키워드 설정
        use=naming_item.use,
        spec=naming_item.spec,
        style=naming_item.style,
        extra=naming_item.extra
    )
    
    # 네이버 쇼핑 API에 검색할 파라미터 설정
    params = {
        "query": naming_item.main_keyword,  # 메인 키워드 입력
        "display": display,                 # 상위 검색 결과 개수
        "sort": "sim"                       # 정렬 기준 (유사도순)
    }
    
    # API 요청 및 결과 수신
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        results = response.json()['items']
        keyword_list = [clean_text(item['title']) for item in results]

        # 패턴 분석 및 최적화 이름 생성
        patterns = analyze_patterns(keyword_list)
        optimized_name_1 = combine_keywords(naming_item.main_keyword, naming_item.fixed_keywords,naming_item, patterns)
        #optimized_name_2 = combine_keywords(naming_item.main_keyword, naming_item.fixed_keywords, naming_item, patterns, variation=True)
        
# 일단 하나의 상품명으로 테스트중 

        # 가공된 이름을 `상위판매자분석` 타입으로 추가
        processed_product.add_processed_name("상위판매자분석", optimized_name_1)
        #processed_product.add_processed_name("상위판매자분석", optimized_name_2)
    else:
        # 오류 발생 시 원본 상품명 추가
        print(f"Error fetching keywords for {naming_item.main_keyword}: {response.status_code}")
        processed_product.add_processed_name("오류처리", naming_item.original_name)

    return processed_product

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
