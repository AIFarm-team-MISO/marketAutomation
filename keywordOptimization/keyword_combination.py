# keywordOptimization/keyword_combination.py

from collections import Counter
import re
from typing import List, Set
import random

from keywordOptimization.randomize_keyword import randomize_pattern_length
from config.settings import FILTER_KEYWORDS, FILTER_UNIT_KEYWORDS, COUPANG_FILTER_KEYWORDS
from config.settings import CURRENT_MARKET_NAME

from utils.global_logger import logger

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

def filter_brand_keywords(gpt_related_keywords, brand_keywords):
    """
    브랜드 키워드가 포함된 연관 검색어를 제거하는 함수.
    :param gpt_related_keywords: GPT 기반 연관 검색어 리스트
    :param brand_keywords: 필터링할 브랜드 키워드 리스트
    :return: 브랜드 키워드가 제거된 연관 검색어 리스트
    """
    if not brand_keywords:
        logger.log(f"💬 브랜드 키워드가 비어 있어 필터링 작업을 건너뜁니다.", level="INFO")
        return gpt_related_keywords
    filtered_keywords = [kw for kw in gpt_related_keywords if not any(brand in kw for brand in brand_keywords)]
    display_filtered_out_keywords = [kw for kw in gpt_related_keywords if kw not in filtered_keywords][:3]
    logger.log(f"💬 필터링된 키워드 (브랜드 키워드와 매칭됨): {display_filtered_out_keywords}", level="INFO", also_to_report=True, separator="none")
    return filtered_keywords

def clean_fixed_keywords(basic_product_name, main_keyword):
    """
    기본 상품명에서 메인 키워드를 제외하고 불필요한 요소를 정리하는 함수.
    - 숫자 슬래시(`/`) 변환
    - 괄호 및 공백을 기준으로 분리 후 불필요한 특수문자 제거
    - 'x' 또는 'X'를 숫자 사이에 있는 경우 유지, 그 외 제거
    - 4자리 이상의 숫자만 포함된 키워드는 삭제
    
    :param basic_product_name: 기존 상품명
    :param main_keyword: 메인 키워드 (제거 대상)
    :return: 정리된 키워드 리스트
    """
    fixed_keywords = [kw for kw in basic_product_name.split() if kw != main_keyword]
    processed_fixed_keywords = []
    
    for keyword in fixed_keywords:
        keyword_with_or = re.sub(r'(\d+)/(\d+)', r'\1또는\2', keyword)  # 숫자 슬래시 변환
        split_keywords = re.split(r'[()\s]+', keyword_with_or)
        
        processed_keywords = []
        for kw in split_keywords:
            if re.match(r'\d+x\d+', kw, re.IGNORECASE):  # 숫자x숫자 유지
                processed_keywords.append(kw)
            else:
                kw = re.sub(r'[^\w\s-]', '', kw).strip()  # 특수문자 제거
                if kw and not re.fullmatch(r'\d+', kw) and not re.fullmatch(r'[a-zA-Z]+', kw):  # 숫자/영어 단독 제외
                    processed_keywords.append(kw)
        
        blink_keywords = [kw.strip() for kw in processed_keywords if kw.strip()]
        number_keywords = [
            kw for kw in blink_keywords
            if not (re.search(r'\b\d{4,}\b', kw) or re.fullmatch(r'\d+', kw) and len(kw) >= 4)
        ]
        
        filtered_keywords = [
            kw for kw in number_keywords
            if not re.search(r'\d{4,}', kw)  # 4자리 이상 숫자 포함된 경우 제거
        ]
        
        filtered_keywords = ''.join(filtered_keywords)
        processed_fixed_keywords.append(filtered_keywords)
    
    logger.log(f"💬 고정키워드 : {fixed_keywords}", also_to_report=True, separator="none")
    logger.log(f"💬 고정키워드 필터링결과 : {processed_fixed_keywords}", also_to_report=True, separator="none")
    return fixed_keywords, processed_fixed_keywords

def truncate_keywords_to_limit(keywords, max_length):
    """
    키워드를 조합하여 최대 길이를 초과하지 않도록 조절하는 함수.
    - 최대 길이 제한을 초과하지 않는 선에서 키워드를 추가
    
    :param keywords: 조합할 키워드 리스트
    :param max_length: 최대 허용 길이
    :return: 최종 상품명 문자열 (공백 포함 max_length 이내)
    """
    current_length = 0
    optimized_keywords = []
    for keyword in keywords:
        if current_length + len(keyword) + 1 > max_length:
            break
        optimized_keywords.append(keyword)
        current_length += len(keyword) + 1
    result = " ".join(optimized_keywords).strip()
    logger.log(f"💬 글자 수 제한 적용 후 최종 키워드: {result} (글자 수: {len(result)})", level="INFO")
    return result

def get_top_patterns(patterns, limit=10):
    """
    패턴에서 상위 N개를 선택하는 함수.
    :param patterns: 전체 패턴 리스트
    :param limit: 선택할 최대 개수 (기본값 10개)
    :return: 상위 N개의 패턴 리스트
    """
    return patterns[:limit] if isinstance(patterns, list) else []


def combine_keywords(existing_data, basic_product_name, max_length=49):
    """
    최적화된 상품명을 생성하는 메인 함수.
    - 브랜드 키워드를 포함한 연관 검색어 필터링
    - 기본 상품명에서 불필요한 요소 제거
    - 메인 키워드와 연관 검색어 조합
    - 네이버 마켓일 경우 중복 제거 및 50자 이내로 제한
    
    :param existing_data: 기존 데이터 (딕셔너리 형태)
    :param basic_product_name: 기본 상품명
    :param max_length: 최대 길이 (기본값 45자)
    :return: 최적화된 상품명 문자열
    """
    # 필요한 데이터 추출
    main_keyword = existing_data.get("제품군", "")
    related_keywords = existing_data.get("네이버연관검색어", [])
    gpt_related_keywords = existing_data.get("GPT연관검색어", [])
    patterns = existing_data.get("패턴", [])
    brand_keywords = existing_data.get("브랜드키워드", [])

    market_name = CURRENT_MARKET_NAME
    logger.log(f" #키워드조합# market_name : {market_name}")

    # 1️⃣ 연관검색어 브랜드 키워드 필터링 필터링: 연관검색어의 브랜드 키워드 제거(브랜드 키워드가 비어있지 않을 경우에만 필터링 수행)

    gpt_related_keywords = filter_brand_keywords(gpt_related_keywords, brand_keywords)
    # 브랜드 키워드 제거 후 출력 (최대 3개만)
    display_gpt_related_keywords = gpt_related_keywords[:3]
    logger.log(f"💬 최종 연관검색어 (브랜드 키워드 제거 후): {display_gpt_related_keywords}", level="INFO")

    # 2️⃣ 기본 상품명 정리 : 필터링된 고정키워드
    fixed_keywords, processed_fixed_keywords = clean_fixed_keywords(basic_product_name, main_keyword)


    # 🔥 3️⃣ 기본 상품명 & 연관 키워드 필터링 (쿠팡 브랜드 네임 및 금지어 제거)
    gpt_related_keywords = [word for word in gpt_related_keywords if word not in COUPANG_FILTER_KEYWORDS + FILTER_KEYWORDS + FILTER_UNIT_KEYWORDS]
    processed_fixed_keywords = [word for word in processed_fixed_keywords if word not in COUPANG_FILTER_KEYWORDS + FILTER_KEYWORDS +FILTER_UNIT_KEYWORDS]

    # 4️⃣ 글자 수 제한 계산 : 메인 키워드 + 고정 키워드가 차지하는 길이를 먼저 계산하고, 남은 길이(remaining_length)를 구함!
    protected_length = len(main_keyword) + len(" ".join(processed_fixed_keywords)) + 1  # 공백 1개만 고려
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
    
    final_keywords = f"{filtered_part} {fixed_keywords_part} {main_keyword}".split()
    final_keywords_unique = list(dict.fromkeys(final_keywords)) # 완전히 동일한 키워드만 중복 제거

    # 최적화된 상품명 생성
    optimized_name = " ".join(final_keywords_unique).strip()

    # 디버깅 정보 출력
    logger.log(f"💬 기본상품명 : {basic_product_name}", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 메인키워드 : {main_keyword}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 고정키워드 : ", fixed_keywords, level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 필터 및 랜덤화된 고정키워드 : ", processed_fixed_keywords, level="INFO", also_to_report=True, separator="none")

    # 최대 3개만 출력
    display_related_keywords = gpt_related_keywords[:3]
    # 로그에 출력
    logger.log(f"💬 연관검색어(3개만출력): {display_related_keywords}", level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 패턴 : ", patterns, level="INFO", also_to_report=True, separator="none")
    logger.log_list(f"💬 조합키워드 리스트", final_keywords_unique, level="INFO", also_to_report=True, separator="none")
    logger.log(f"🚀 최적화된 상품명: '{optimized_name}' (글자 수: {len(optimized_name)})", level="INFO", also_to_report=True, separator="dash-2line")
    

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

