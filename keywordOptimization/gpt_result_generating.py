from keywordOptimization.keyword_combination import analyze_patterns,analyze_related_patterns, combine_keywords
from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary

from utils.global_logger import logger


def find_main_keyword_by_basic_name(dictionary, basic_product_name):
    for main_keyword, value in dictionary.items():
        # "기본상품명"이 key로 존재하고, 리스트 내에 basic_product_name이 포함되어 있는지 확인
        if "기본상품명" in value and isinstance(value["기본상품명"], list):
            if basic_product_name in value["기본상품명"]:
                return main_keyword
    return None  # 찾지 못한 경우

from keywordOptimization.keyword_filter_never import filter_length


def gpt_result_generate_name(basic_product_name, dictionary, name_strength=49):
    """
    gpt 데이터를 통해 통해 최적화된 상품명을 생성.
    
    Parameters:
    - basic_product_name : 기본상품명
    - dictionary : 사전데이터
    
    Returns:
    - optimized_name: gpt의 키워드조합후 최종상품명
    """
    logger.log(f"📌 {basic_product_name} : 필터링시작", also_to_report=True, separator="none")
    logger.log(f"📌 마켓글자수제한 : {name_strength}", also_to_report=True, separator="none")


    # 브랜드키워드중 연관검색어 있는것들 삭제하는 코드 
    # for main_keyword, keyword_data in dictionary.items():
    #         # 브랜드 키워드와 연관검색어 가져오기
    #         brand_keywords = keyword_data.get("브랜드키워드", [])
    #         related_keywords = keyword_data.get("GPT연관검색어", [])

    #         # 브랜드 키워드가 없으면 건너뜀
    #         if not brand_keywords:
    #             logger.log(f"💬 '{main_keyword}'의 브랜드 키워드가 비어 있어 필터링 작업을 건너뜁니다.", level="INFO")
    #             continue

    #         # 필터링된 연관검색어와 제거된 연관검색어 구분
    #         filtered_out_keywords = [
    #             keyword for keyword in related_keywords
    #             if any(brand in keyword for brand in brand_keywords)
    #         ]
    #         updated_related_keywords = [
    #             keyword for keyword in related_keywords
    #             if keyword not in filtered_out_keywords
    #         ]

    #         # 필터링 결과 로그 출력
    #         if filtered_out_keywords:
    #             logger.log(f"💬 '{main_keyword}'에서 제거된 연관검색어 (브랜드와 매칭됨):", level="INFO")
    #             for keyword in filtered_out_keywords:
    #                 matching_brands = [brand for brand in brand_keywords if brand in keyword]
    #                 logger.log(f"    🔹 연관검색어: '{keyword}' -> 매칭된 브랜드 키워드: {matching_brands}", level="INFO")

    #         # 사전 데이터 업데이트
    #         dictionary[main_keyword]["GPT연관검색어"] = updated_related_keywords
            
    # save_dictionary(dictionary)




    # 1. 기본상품명을 통해 그데이터의 메인키워드 추출
    main_keyword = find_main_keyword_by_basic_name(dictionary, basic_product_name)

    # 2. 메인키워드를 통해 메인키워드의 모든 데이터를 사전에서 가져오기
    existing_data = dictionary.get(main_keyword, {})

    # 3. 글자수 필터링 및 키워드 조합 후 가공상품명 생성 
    optimized_name = combine_keywords(existing_data, basic_product_name, name_strength)  # 최적화된 상품명 생성


    return optimized_name