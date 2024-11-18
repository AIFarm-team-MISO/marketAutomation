import re
import random

def filter_length(name, max_length=49, main_keyword=None, fixed_keywords=None, low_priority_keywords=None):
    """
    메인 키워드와 고정 키워드를 분리하여 보호하고, 글자 수 제한을 적용.
    
    Parameters:
    - name (str): 원본 문자열.
    - max_length (int): 글자 수 제한.
    - main_keyword (str): 메인 키워드 (항상 보호되는 최우선 키워드).
    - fixed_keywords (list of str): 고정 키워드 (보호되지만 순서 고정 없음).
    - low_priority_keywords (list of str): 우선 제거 대상 키워드.
    
    Returns:
    - str: 필터링된 결과.
    """
    if len(name) <= max_length:
        return name  # 이미 제한 길이 이내면 그대로 반환
    

    # 메인 키워드와 고정 키워드 병합 및 랜덤화
    all_keywords = [main_keyword] if main_keyword else []
    if fixed_keywords:
        all_keywords.extend(fixed_keywords)

    # 중복 제거 및 랜덤 섞기
    all_keywords = list(dict.fromkeys(all_keywords))  # 중복 제거
    random.shuffle(all_keywords)  # 랜덤화

    # 랜덤화된 키워드로 protected_part 생성
    protected_part = " ".join(kw for kw in all_keywords if kw in name)

    # 나머지 부분 추출 (모든 키워드를 정확히 제거)
    remaining_part = name
    for kw in all_keywords:
        remaining_part = re.sub(rf"\b{re.escape(kw)}\b", "", remaining_part).strip()

    # 불필요한 키워드 제거
    if low_priority_keywords is not None:
        for kw in low_priority_keywords:
            remaining_part = re.sub(rf"\b{re.escape(kw)}\b", "", remaining_part).strip()

    # 글자 수 초과 시 단어 단위로 자르기
    words = remaining_part.split()
    filtered_remaining = ""
    for word in words:
        if len(protected_part + " " + filtered_remaining + " " + word) > max_length:
            break
        filtered_remaining += " " + word

    # 최종 결과 생성
    filtered_name = (protected_part + " " + filtered_remaining).strip()

    # 글자 수 제한 준수 확인
    if len(filtered_name) > max_length:
        filtered_name = filtered_name[:max_length].rstrip()

    return filtered_name



import re

def remove_special_characters(name):
    """
    특수문자를 제거하는 함수.
    
    Parameters:
    - name (str): 입력 문자열 (상품명 등).
    
    Returns:
    - str: 특수문자가 제거된 문자열.
    
    특징:
    - 한글(가-힣), 영어(a-z, A-Z), 숫자(0-9), 공백(\s)을 제외한 모든 문자를 제거.
    - 특수문자(예: #, !, (, ), 등)를 삭제하여 깔끔한 텍스트를 반환.
    
    예시:
    >>> remove_special_characters("상품명 #특가 (신상품) 50% 할인!!")
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


def apply_filters(processed_products, spam_keywords, unrelated_keywords, max_length=99):
    """
    필터링을 적용하여 가공된 상품명을 업데이트.
    
    Parameters:
    - processed_products (list of ProcessedProductInfo): 상품 정보 객체 리스트.
    - spam_keywords (list of str): 스팸 키워드 리스트.
    - unrelated_keywords (list of str): 불필요한 키워드 리스트.
    - max_length (int): 글자 수 제한.
    
    Returns:
    - list of ProcessedProductInfo: 필터링된 상품 정보 객체 리스트.
    """
    for product in processed_products:  # ProcessedProductInfo 객체

        # '상위판매자분석' 가공 타입의 이름을 가져와 필터링
        processed_names = product.processed_names.get("상위판매자분석", [])
        filtered_names = []

        for name in processed_names:
            # 메인 키워드와 고정 키워드 분리
            main_keyword = product.main_keyword
            fixed_keywords = product.get_fixed_keywords()


            # 필터링 단계별 적용
            filtered_name = filter_length(
                name=name,
                max_length=max_length,
                main_keyword=main_keyword,
                fixed_keywords=fixed_keywords,
                low_priority_keywords=spam_keywords + unrelated_keywords,
            )

            # 추가 클린업 단계
            filtered_name = remove_special_characters(filtered_name)
            filtered_name = remove_extra_spaces(filtered_name)

            filtered_names.append(filtered_name)

        # 필터링 결과 저장
        product.processed_names["상위판매자분석"] = filtered_names

    return processed_products  # 필터링 완료된 객체 리스트 반환


def process_duplicates_with_variation(filtered_results, max_attempts=10):
    """
    중복된 필터링된 상품명을 변형하여 고유한 이름 생성.
    
    Parameters:
    - filtered_results (list of ProcessedProductInfo): 필터링된 결과 리스트.
    - max_attempts (int): 키워드 셔플 최대 시도 횟수 (기본값: 10).
    
    Returns:
    - list of ProcessedProductInfo: 변형된 결과 리스트.
    """
    seen_names = set()  # 중복된 상품명을 추적
    unique_results = []

    for product in filtered_results:
        unique_filtered = []
        for name in product.processed_names.get("filtered", []):
            if name in seen_names:
                # 중복된 상품명을 변형
                attempts = 0
                modified_name = shuffle_keywords(name)  # 키워드 셔플
                while modified_name in seen_names and attempts < max_attempts:
                    modified_name = shuffle_keywords(name)
                    attempts += 1

                # 셔플 최대 시도 초과 시 '신상' 키워드 추가
                if modified_name in seen_names:
                    modified_name += " 신상"

                unique_filtered.append(modified_name)
                seen_names.add(modified_name)  # 새로운 이름 저장
            else:
                unique_filtered.append(name)
                seen_names.add(name)
        
        # 업데이트된 필터된 이름 리스트 저장
        product.processed_names["filtered"] = unique_filtered
        unique_results.append(product)

    return unique_results


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