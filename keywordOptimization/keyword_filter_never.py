import re
import random

from utils.log_utils import Logger

# logs 디렉터리에 로그 파일이 생성됩니다.
logger = Logger(log_file="logs/debug.log", enable_console=True)

import random  # 고정 키워드를 랜덤으로 섞기 위해 사용

def filter_length(name, max_length=49, main_keyword=None, fixed_keywords=None, low_priority_keywords=None):
    """
    상품명을 필터링하여 메인 키워드와 고정 키워드를 보호하며,
    남은 글자 수 내에서 키워드를 결합하는 함수.

    Parameters:
    - name (str): 필터링할 상품명.
    - max_length (int): 상품명 최대 글자 수 제한 (기본값: 49).
    - main_keyword (str): 메인 키워드 (예: 제품군 이름).
    - fixed_keywords (list): 항상 포함해야 할 고정 키워드 리스트.
    - low_priority_keywords (list): 우선순위가 낮은 키워드 리스트 (제거 대상).

    Returns:
    - str: 필터링된 상품명.
    """
    # 고정 키워드 평탄화 및 중복 제거
    flat_fixed_keywords = list(set(
        item for sublist in fixed_keywords
        for item in (sublist if isinstance(sublist, list) else [sublist])
    )) if fixed_keywords else []
    random.shuffle(flat_fixed_keywords)  # 고정 키워드 랜덤화

    # 고정 키워드 문자열로 결합
    fixed_keywords_part = " ".join(flat_fixed_keywords)

    # 메인 키워드와 고정 키워드의 초기 길이 계산
    protected_length = len(main_keyword + " " + fixed_keywords_part)

    # 1. 글자 수 제한 확인
    if len(name) <= max_length and len(name) >= protected_length:
        logger.log(f"🌀필터 완료: '{name}' (글자 수: {len(name)})")
        return name  # 글자 수 제한을 초과하지 않으면 그대로 반환

    # logger.log(f"🌀main_keyword: '{main_keyword}' (fixed_keywords: {flat_fixed_keywords})")

    # 나머지 키워드 처리 (고정 키워드와 메인 키워드 제거)
    remaining_part = name
    protected_keywords = [main_keyword] + flat_fixed_keywords  # 보호할 키워드
    for kw in protected_keywords:
        remaining_part = re.sub(rf"\b{re.escape(kw)}\b", "", remaining_part).strip()

    # 우선순위가 낮은 키워드 제거
    if low_priority_keywords:
        for kw in low_priority_keywords:
            remaining_part = re.sub(rf"\b{re.escape(kw)}\b", "", remaining_part).strip()

    # 남은 글자 수 계산
    remaining_length = max_length - protected_length - 1  # 1은 공백을 고려

    # 나머지 키워드 단어 단위로 처리
    words = remaining_part.split()
    filtered_remaining = ""
    for word in words:
        if len(filtered_remaining + " " + word) > remaining_length:
            break
        filtered_remaining += " " + word

    filtered_remaining = filtered_remaining.strip()

    # 단어 단위로 랜덤 섞기
    words = filtered_remaining.split()
    random.shuffle(words)
    filtered_remaining = " ".join(words)

    # 메인 키워드 추가
    filtered_remaining += f" {main_keyword}"

    # 최종 결과 조합
    final_name = f"{filtered_remaining} {fixed_keywords_part}".strip()

    # logger.log(f"🌀 최종 필터링 결과: '{final_name}' (글자 수: {len(final_name)})")
    return final_name








import re

def remove_special_characters(name):
    """
    특수문자를 제거하는 함수.
    
    Parameters:
    - name (str): 입력 문자열 (상품명 등).
    
    Returns:
    - str: 특수문자가 제거된 문자열.
    
    특징:
    - 한글(가-힣), 영어(a-z, A-Z), 숫자(0-9), 공백을 제외한 모든 문자를 제거.
    - 특수문자(예: #, !, (, ), 등)를 삭제하여 깔끔한 텍스트를 반환.
    
    예시:
    remove_special_characters("상품명 #특가 (신상품) 50% 할인!!")
    '상품명 특가 신상품 50 할인'
    """
    return re.sub(r"[^가-힣a-zA-Z0-9\s]", "", name)


def remove_spam_keywords(name, spam_keywords):
    """
    스팸 키워드를 제거하는 함수.
    
    Parameters:
    - name (str): 입력 문자열 (상품명 등).
    - spam_keywords (list of str): 제거할 스팸 키워드 리스트.
    
    Returns:
    - str: 스팸 키워드가 제거된 문자열.
    
    특징:
    - 제공된 스팸 키워드 리스트를 순회하며 입력 문자열에서 해당 키워드를 제거.
    - 단순한 치환 방식으로 동작하며, 대소문자 구분에 민감.
    
    예시:
    >>> remove_spam_keywords("상품명 초특가 1+1 빅세일!", ["초특가", "1+1", "빅세일"])
    '상품명 '
    """
    for spam in spam_keywords:
        name = name.replace(spam, "")
    return name


def remove_unrelated_keywords(name, unrelated_keywords):
    """
    관련 없는 키워드를 제거하는 함수.
    
    Parameters:
    - name (str): 입력 문자열 (상품명 등).
    - unrelated_keywords (list of str): 제거할 관련 없는 키워드 리스트.
    
    Returns:
    - str: 관련 없는 키워드가 제거된 문자열.
    
    특징:
    - 입력된 키워드 리스트에서 관련 없는 키워드를 찾아 제거.
    - 단순한 치환 방식으로 동작하며, 대소문자 구분에 민감.
    
    예시:
    >>> remove_unrelated_keywords("상품명 스타일 st 최신형", ["스타일", "st"])
    '상품명 최신형'
    """
    for keyword in unrelated_keywords:
        name = name.replace(keyword, "")
    return name


def remove_extra_spaces(name):
    """
    여분의 공백을 제거하는 함수.
    
    Parameters:
    - name (str): 입력 문자열 (상품명 등).
    
    Returns:
    - str: 공백이 정리된 문자열.
    
    특징:
    - 연속된 공백(2개 이상)을 하나의 공백으로 변경.
    - 문자열 양쪽의 공백도 제거.
    
    예시:
    >>> remove_extra_spaces("상품명   초특가   할인  ")
    '상품명 초특가 할인'
    """
    return re.sub(r"\s{2,}", " ", name).strip()


def find_related_data(processed_name, dictionary):
    """
    가공상품명을 기준으로 관련 메인 키워드와 데이터를 탐색.

    Parameters:
    - processed_name (str): 가공상품명.
    - dictionary (dict): 데이터 사전.

    Returns:
    - dict: 관련 데이터 (메인 키워드, 기본상품명, 고정 키워드 등) 또는 None.
    """
    for main_keyword, data in dictionary.items():
        # 연관검색어-가공상품명 리스트에서 가공상품명을 탐색
        processed_names = data.get("연관검색어-가공상품명", [])
        if processed_name in processed_names:
            # 해당 가공상품명의 인덱스를 기준으로 기본상품명과 고정키워드 매핑
            index = processed_names.index(processed_name)
            basic_name = data["기본상품명"][index]
            fixed_keywords = data["고정키워드"][index]
            
            return {
                "main_keyword": main_keyword,
                "basic_name": basic_name,
                "fixed_keywords": fixed_keywords,
            }
    return None

def apply_filters(processed_names, spam_keywords, unrelated_keywords, dictionary, max_length=49):
    """
    필터링을 적용하여 가공된 상품명을 업데이트.

    Parameters:
    - processed_names (list of str): 가공된 상품명 리스트.
    - spam_keywords (list of str): 스팸 키워드 리스트.
    - unrelated_keywords (list of str): 불필요한 키워드 리스트.
    - dictionary (dict): 데이터 사전 (메인키워드, 기본상품명, 고정키워드 등 포함).
    - max_length (int): 글자 수 제한.

    Returns:
    - list of str: 필터링된 상품명 리스트.
    """
    filtered_results = []
    
    for name in processed_names:
        # 메타 정보 찾기
        related_data = find_related_data(name, dictionary)
        if not related_data:
            continue  # 관련 데이터가 없으면 무시
        
        main_keyword = related_data["main_keyword"]
        fixed_keywords = related_data["fixed_keywords"]

        # 필터링 실행
        filtered_name = filter_length(
            name=name,
            max_length=max_length,
            main_keyword=main_keyword,
            fixed_keywords=fixed_keywords,
            low_priority_keywords=spam_keywords + unrelated_keywords,
        )
        filtered_results.append(filtered_name)

    return filtered_results


def shuffle_keywords(name):
    """
    상품명의 키워드를 섞는 함수.
    
    Parameters:
    - name (str): 상품명 문자열.
    
    Returns:
    - str: 키워드가 섞인 상품명.
    """
    keywords = name.split()  # 공백으로 키워드 분리
    random.shuffle(keywords)  # 키워드 순서 섞기
    return " ".join(keywords)