from keywordOptimization.keyword_combination import analyze_patterns,analyze_related_patterns, combine_keywords

from utils.global_logger import logger


def find_main_keyword_by_basic_name(dictionary, basic_product_name):
    for main_keyword, value in dictionary.items():
        # "기본상품명"이 key로 존재하고, 리스트 내에 basic_product_name이 포함되어 있는지 확인
        if "기본상품명" in value and isinstance(value["기본상품명"], list):
            if basic_product_name in value["기본상품명"]:
                return main_keyword
    return None  # 찾지 못한 경우

from keywordOptimization.keyword_filter_never import filter_length


def gpt_result_generate_name(basic_product_name, dictionary):
    """
    gpt 데이터를 통해 통해 최적화된 상품명을 생성.
    
    Parameters:
    - basic_product_name : 기본상품명
    - dictionary : 사전데이터
    
    Returns:
    - optimized_name: gpt의 키워드조합후 최종상품명
    """
    logger.log(f"📌 {basic_product_name} : 필터링시작", also_to_report=True, separator="none")

    # 1. 기본상품명을 통해 그데이터의 메인키워드 추출
    main_keyword = find_main_keyword_by_basic_name(dictionary, basic_product_name)

    # 2. 메인키워드를 통해 메인키워드의 모든 데이터를 사전에서 가져오기
    existing_data = dictionary.get(main_keyword, {})

    # 3. 글자수 필터링 및 키워드 조합 후 가공상품명 생성 
    optimized_name = combine_keywords(existing_data, basic_product_name, 99)  # 최적화된 상품명 생성


    return optimized_name