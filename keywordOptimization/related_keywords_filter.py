from utils.global_logger import logger


def filter_related_keywords(keyword_data, min_search_volume=50, max_competition="중간"):
    """
    연관 키워드를 선별하는 함수. 필터링된 원본 데이터 반환.
    검색량이 기준 이상이고 경쟁 강도가 낮거나 중간인 검색어를 선별.
    """
    filtered_keywords = []
    logger.log_separator()
    logger.log("📊 필터링된 연관 키워드 정보:")

    for keyword in keyword_data:
        try:
            # 데이터에서 필요한 키 추출
            rel_keyword = keyword.get("relKeyword", "Unknown")
            pc_volume = keyword.get("monthlyPcQcCnt", 0)
            mobile_volume = keyword.get("monthlyMobileQcCnt", 0)
            competition = keyword.get("compIdx", "Unknown")

            # 문자열 "< 10" 및 공백 처리
            pc_volume = parse_int_safe(pc_volume)
            mobile_volume = parse_int_safe(mobile_volume)

            # 검색량과 경쟁 강도 조건 확인
            if (
                (pc_volume >= min_search_volume or mobile_volume >= min_search_volume)
                and competition in ["낮음", max_competition]
            ):
                filtered_keywords.append(keyword)  # 원본 데이터 추가
                logger.log(
                    f"  🔍 키워드: {rel_keyword} | PC 검색량: {pc_volume}, 모바일 검색량: {mobile_volume}, 경쟁 강도: {competition}",
                    level="DEBUG",
                )
        except Exception as e:
            logger.log(f"⚠️ 키워드 필터링 중 오류: {e}. 데이터: {keyword}", level="ERROR")

    logger.log_separator()
    return filtered_keywords


def parse_int_safe(value):
    """
    문자열을 안전하게 정수로 변환하는 함수.
    '< 10'과 같은 경우를 처리하여 기본값 0을 반환하거나
    숫자 값만 추출.
    """
    try:
        # 문자열 "< 10" 같은 경우 처리
        if isinstance(value, str):
            value = value.replace("<", "").strip()  # "<" 및 공백 제거
            return int(value) if value.isdigit() else 0
        # 숫자인 경우 그대로 반환
        return int(value)
    except ValueError:
        return 0





def generate_optimized_product_name(main_keyword, fixed_keywords, related_keywords):
    """
    최적화된 상품명을 생성하는 함수.
    
    Parameters:
    - main_keyword (str): 메인 키워드.
    - fixed_keywords (list): 고정 키워드 리스트.
    - related_keywords (list): 연관 키워드 리스트.
    
    Returns:
    - str: 최적화된 상품명.
    """
    # 연관 키워드 3개만 사용
    related_snippet = " ".join(related_keywords[:3]) if related_keywords else ""
    return f"{main_keyword} {related_snippet} {' '.join(fixed_keywords)}"


def generate_optimized_names(naming_item, display=10, source_type="ads"):
    """
    네이버 광고 API를 통해 최적화된 상품명을 생성.
    
    Parameters:
    - naming_item (ProductInfo): 상품 정보 객체.
    - source_type (str): API 종류 선택 ("shopping" 또는 "ads").
    - display (int): 검색 결과 개수 (기본값: 10).
    
    Returns:
    - dict: 최적화된 상품명과 연관 키워드 데이터.
    """
    if source_type == "ads":
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
            "hintKeywords": naming_item["제품군"],
            "showDetail": "1"
        }

        # API 요청
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            full_response = response.json()
            
            # 연관 키워드 필터링
            related_keywords_data = full_response["keywordList"]
            filtered_keywords = filter_related_keywords(related_keywords_data)

            # 최적화된 상품명 생성
            optimized_name = generate_optimized_product_name(
                main_keyword=naming_item["제품군"],
                fixed_keywords=naming_item["고정키워드"],
                related_keywords=filtered_keywords
            )

            # 결과 출력 및 반환
            logger.log_separator()
            logger.log("🔍 전체 검색 응답 데이터:")
            logger.log(json.dumps(full_response, indent=4, ensure_ascii=False))
            logger.log_separator()

            logger.log_list("연관검색어 출력", filtered_keywords)
            return {
                "type": "연관검색어",
                "optimized_name": optimized_name,
                "keywords": filtered_keywords
            }
        else:
            logger.log(f"Error fetching data: {response.status_code}", level="ERROR")
            return {"type": "오류처리", "original_name": naming_item["기본상품명"]}
    else:
        raise ValueError(f"Invalid source_type: {source_type}. Must be 'shopping' or 'ads'.")
