# keywordOptimization/keyword_combination.py

from collections import Counter
import re
from typing import List, Set
import random

from keywordOptimization.randomize_keyword import randomize_pattern_length

from utils.log_utils import Logger

# logs 디렉터리에 로그 파일이 생성됩니다.
logger = Logger(log_file="logs/debug.log", enable_console=True)

def analyze_related_patterns(
    related_keywords_data,
    top_n=10,
    min_search_volume=100,
    min_clicks=10,
    min_ctr=1.0,
    max_ad_depth=10,
    max_competition="중간",
    shuffle=True
):
    """
    연관검색어 데이터를 분석하여 상위 키워드 및 랜덤화된 패턴을 생성.

    Parameters:
    - related_keywords_data (list of dict): 연관검색어 데이터 리스트.
    - top_n (int): 반환할 상위 키워드의 개수 (기본값: 10).
    - min_search_volume (int): 최소 검색량 기준 (PC+모바일 합).
    - min_clicks (int): 최소 클릭 수 기준.
    - min_ctr (float): 최소 클릭률 기준 (%).
    - max_ad_depth (int): 최대 광고 노출 심도 기준.
    - max_competition (str): 최대 경쟁 강도 ("낮음", "중간", "높음").
    - shuffle (bool): True일 경우, 결과를 랜덤하게 섞음.

    Returns:
    - List[str]: 최종 연관 키워드 리스트.
    """
        # 필터링된 키워드를 저장할 리스트
    filtered_keywords = []

    for keyword_data in related_keywords_data:
        try:
            # 데이터에서 필요한 필드 추출 (기본값 설정)
            pc_volume = parse_int_safe(keyword_data.get("monthlyPcQcCnt", 0))
            mobile_volume = parse_int_safe(keyword_data.get("monthlyMobileQcCnt", 0))
            pc_clicks = parse_float_safe(keyword_data.get("monthlyAvePcClkCnt", 0))
            mobile_clicks = parse_float_safe(keyword_data.get("monthlyAveMobileClkCnt", 0))
            pc_ctr = parse_float_safe(keyword_data.get("monthlyAvePcCtr", 0))
            mobile_ctr = parse_float_safe(keyword_data.get("monthlyAveMobileCtr", 0))
            ad_depth = parse_int_safe(keyword_data.get("plAvgDepth", 0))
            competition = keyword_data.get("compIdx", "Unknown")
            rel_keyword = keyword_data.get("relKeyword", "Unknown")

            # 검색량 합계
            total_volume = pc_volume + mobile_volume
            # 클릭 수 합계
            total_clicks = pc_clicks + mobile_clicks
            # 클릭률 평균
            avg_ctr = (pc_ctr + mobile_ctr) / 2

            # 필터링 조건 확인
            if (
                total_volume >= min_search_volume and
                total_clicks >= min_clicks and
                avg_ctr >= min_ctr and
                ad_depth <= max_ad_depth and
                competition in ["낮음", max_competition]
            ):
                filtered_keywords.append(rel_keyword)
        except Exception as e:
            logger.log(f"⚠️ 키워드 처리 중 오류 발생: {e}. 데이터: {keyword_data}", level="ERROR")

    # 키워드 빈도 계산 (중복된 키워드 제거 효과)
    keyword_counts = Counter(filtered_keywords)

    # 상위 키워드 추출
    most_common_keywords = [keyword for keyword, _ in keyword_counts.most_common(top_n)]

    # 랜덤화된 패턴 생성
    if shuffle:
        random.shuffle(most_common_keywords)

    # 디버깅 정보 출력
    logger.log_separator()
    logger.log_list("📊[연관검색어 상위 키워드]", most_common_keywords)

    return most_common_keywords


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


def parse_float_safe(value):
    """
    문자열을 안전하게 실수로 변환하는 함수.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0




def analyze_patterns(keyword_list, top_n=10, shuffle=True, randomize_length=True, min_length=7, max_length=10):
    """
    상위 검색 결과에서 자주 등장하는 키워드를 추출하고 랜덤화를 적용하는 함수.
    
    Parameters:
    - keyword_list (list of str): 상위 검색 결과의 상품명 리스트.
    - top_n (int): 반환할 상위 키워드의 개수 (기본값: 10).
    - shuffle (bool): True일 경우, 상위 키워드 리스트를 랜덤하게 섞음.
    - randomize_length (bool): True일 경우, 랜덤화된 패턴 길이를 적용.
    - min_length (int): 랜덤화 패턴 길이의 최소값.
    - max_length (int): 랜덤화 패턴 길이의 최대값.
    
    Returns:
    - List[str]: 빈도순으로 정렬된 상위 키워드 리스트 또는 랜덤 순서의 리스트.
    """
    
    # 키워드 전체를 수집하기 위한 리스트 초기화
    all_keywords = []

    # 각 상품명에서 키워드 추출
    for title in keyword_list:
        # 상품명에서 특수문자를 제거하고, 단어 단위로 분리하여 키워드 리스트 생성
        words = re.findall(r'\b\w+\b', title)
        all_keywords.extend(words)


    # 불필요한 키워드 필터링
    exclude_keywords = {"의", "가", "에", "는", "과", "및", "로", "에서"}
    filtered_keywords = [word for word in all_keywords if word not in exclude_keywords]


    # 키워드 빈도 계산
    keyword_counts = Counter(filtered_keywords)

    # 상위 키워드 선택
    most_common_keywords = [keyword for keyword, _ in keyword_counts.most_common(top_n)]

    # 랜덤화된 패턴 생성
    randomized_patterns = randomize_pattern_length(
        patterns=filtered_keywords,
        min_length=min_length,
        max_length=max_length,
        must_include=most_common_keywords[:10]  # 상위 10개 필수 포함
    )

    # 디버깅 정보 출력
    print("="*50)
    print("🔍 [디버그] 검색 결과 패턴 분석")
    print("="*50)

    # 전체 키워드 빈도 출력
    print("\n📊 [키워드 빈도]")
    sorted_keyword_counts = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    for rank, (keyword, count) in enumerate(sorted_keyword_counts, start=1):
        if rank <= 3:
            # 1~3위는 세로로 출력
            print(f"  {rank}. {keyword}: {count}회")
        else:
            # 나머지는 가로로 출력
            break

    if len(sorted_keyword_counts) > 3:
        print("  -- 나머지:")
        print("   " + ", ".join([f"{keyword}: {count}회" for keyword, count in sorted_keyword_counts[3:]]))

    # 상위 Top N 키워드 출력
    print(f"\n🏆 [상위 Top {top_n} 키워드]")
    for rank, keyword in enumerate(most_common_keywords, start=1):
        if rank <= 3:
            # 1~3위는 세로로 출력
            print(f"  {rank}. {keyword}")
        else:
            # 나머지는 가로로 출력
            break

    if len(most_common_keywords) > 3:
        print("  4~10:")
        print("   " + ", ".join(most_common_keywords[3:]))

    # 랜덤화된 패턴 출력
    print("\n🎲 [랜덤화된 패턴]")
    print("  " + ", ".join(randomized_patterns))

    print("="*50 + "\n")

    return randomized_patterns

def process_sub_keywords(sub_keywords) -> List[str]:
    """
    보조 키워드를 처리하여 중복 없이 정리된 보조 키워드 리스트를 반환하는 함수.
    
    Parameters:
    - sub_keywords (KeywordInfo): 보조 키워드 정보 (use, spec, style, extra).

    Returns:
    - List[str]: 중복 제거된 보조 키워드 리스트.
    """
    combined_sub_keywords = set()  # 중복을 제거하기 위해 set으로 초기화

    # sub_keywords의 각 속성을 순회하며 키워드 리스트를 생성
    for keyword_category in [sub_keywords.use, sub_keywords.spec, sub_keywords.style, sub_keywords.extra]:
        if keyword_category:
            keywords = keyword_category.split(",")  # 콤마로 분리
            cleaned_keywords = {kw.strip() for kw in keywords if kw.strip()}  # 공백 제거 및 중복 제거
            combined_sub_keywords.update(cleaned_keywords)

    # 정리된 보조 키워드를 리스트로 변환하여 반환
    return list(combined_sub_keywords)

def remove_duplicates_and_optimize(keywords: List[str]) -> str:
    """
    중복 키워드를 제거하고 최적화된 문자열로 결합하는 함수.
    
    Parameters:
    - keywords (List[str]): 결합할 키워드 리스트.
    
    Returns:
    - str: 중복 키워드가 제거되고 최적화된 공백을 가진 문자열.
    """
    # 중복 제거 및 순서 유지
    unique_keywords = list(dict.fromkeys(keywords))
    
    # 중복된 공백 제거
    optimized_name = " ".join(unique_keywords)
    optimized_name = re.sub(r'\s+', ' ', optimized_name).strip()
    
    return optimized_name


def combine_keywords(existing_data, basic_product_name):
    """
    네이밍 아이템을 기반으로 최적화된 상품명을 생성.
    
    Parameters:
    - naming_item (dict): 상품 정보를 포함하는 딕셔너리.
    
    Returns:
    - str: 최적화된 상품명.
    """
    # 필요한 데이터 추출
    main_keyword = existing_data.get("제품군", "")
    related_keywords = existing_data.get("네이버연관검색어", [])
    gpt_related_keywords = existing_data.get("GPT연관검색어", [])
    patterns = existing_data.get("패턴", [])

    # 기본상품명에서 메인키워드를 제외한 나머지를 고정 키워드로 설정
    fixed_keywords = [kw for kw in basic_product_name.split() if kw != main_keyword]

    # 패턴에서 상위 10개만 선택
    top_patterns = patterns[:10] if isinstance(patterns, list) else []

    # 조합할 키워드 리스트 생성
    combined_keywords = [main_keyword]

    # 패턴이 있으면 패턴추가 (현재는 일단 네이버연관검색어를 빼고 패턴만 추가 )
    if top_patterns:
        combined_keywords += top_patterns
        combined_keywords += gpt_related_keywords
    # 패턴이 없으면 + 연관검색어
    else:
        combined_keywords += gpt_related_keywords
    
    # if related_keywords:
    #     combined_keywords += related_keywords

    # # 패턴과 네이버 연관 키워드가 없는 경우 GPT 연관검색어만 추가
    # if not top_patterns and not related_keywords:
    #     combined_keywords += gpt_related_keywords

    # 고정 키워드는 맨 마지막에 추가
    combined_keywords += fixed_keywords

        # 디버깅용: 결합된 키워드 출력
    logger.log(f"🔍 결합된 키워드: {combined_keywords}", level="DEBUG")

    # 데이터 검증: 중첩 리스트 평탄화 및 문자열만 포함
    validated_keywords = []
    for keyword in combined_keywords:
        if isinstance(keyword, list):  # 리스트가 중첩된 경우
            logger.log(f"⚠️ 중첩 리스트 발견 및 평탄화: {keyword}", level="WARNING")
            validated_keywords.extend(keyword)  # 리스트를 평탄화
        elif isinstance(keyword, str):  # 문자열인 경우
            validated_keywords.append(keyword)  # 문자열 추가
        else:
            logger.log(f"⚠️ 예상치 못한 데이터 타입 무시: {keyword}", level="ERROR")

    # "없음" 키워드 제거
    validated_keywords = [kw for kw in validated_keywords if kw != "없음"]

    # 중복 제거 및 순서 유지
    unique_combined_keywords = list(dict.fromkeys(validated_keywords))


    # 최적화된 상품명 생성
    optimized_name = " ".join(unique_combined_keywords)

    # 디버깅 정보 출력
    logger.log_separator()
    logger.log_list("🔑최종 조합키워드 리스트🔑", unique_combined_keywords, level="DEBUG")
    logger.log(f"✨최적화된 상품명✨: {optimized_name}")
    logger.log("기본상품명 : ", basic_product_name)
    logger.log("제품군 : ", main_keyword)
    logger.log_list("고정키워드 : ", fixed_keywords)
    logger.log_list("네이버연관검색어 : ", related_keywords)
    logger.log_list("연관검색어 : ", gpt_related_keywords)
    logger.log_list("패턴 : ", patterns)
    logger.log_separator()
    logger.log("\n")
    

    return optimized_name




def flatten_list(input_list):
    """
    리스트 내 중첩된 리스트를 평탄화하는 함수.
    Parameters:
    - input_list (list): 입력 리스트.

    Returns:
    - list: 평탄화된 리스트.
    """
    flattened = []
    for item in input_list:
        if isinstance(item, list):  # 리스트인 경우 재귀적으로 평탄화
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened

