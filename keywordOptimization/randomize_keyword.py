import random

def randomize_pattern_length(patterns, min_length=3, max_length=7):
    """
    패턴 키워드의 길이를 랜덤화하는 함수.
    
    Parameters:
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - min_length (int): 최소 패턴 길이.
    - max_length (int): 최대 패턴 길이.
    
    Returns:
    - List[str]: 랜덤화된 패턴 키워드 리스트 (최소 ~ 최대 길이).
    """
    random_length = random.randint(min_length, max_length)  # 랜덤한 길이 생성
    return random.sample(patterns, min(random_length, len(patterns)))  # 지정 길이만큼 랜덤 추출

def randomize_fixed_keyword_position(main_keyword, patterns, fixed_keywords):
    """
    고정 키워드를 패턴에 랜덤 위치에 삽입하는 함수.
    
    Parameters:
    - main_keyword (str): 상품의 메인 키워드.
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    
    Returns:
    - List[str]: 메인 키워드 + 랜덤으로 섞인 패턴 + 고정 키워드.
    """
    combined_keywords = patterns + fixed_keywords  # 패턴과 고정 키워드 합치기
    random.shuffle(combined_keywords)  # 랜덤 섞기
    return [main_keyword] + combined_keywords  # 메인 키워드는 항상 맨 앞

def mix_and_match_patterns_and_fixed(patterns, fixed_keywords, max_keywords=10):
    """
    패턴과 고정 키워드를 랜덤하게 섞고 일부만 선택하는 함수.
    
    Parameters:
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    - max_keywords (int): 최종 상품명에서 사용할 최대 키워드 수.
    
    Returns:
    - List[str]: 랜덤 섞인 패턴과 고정 키워드의 일부.
    """
    all_keywords = patterns + fixed_keywords  # 패턴과 고정 키워드 합치기
    random.shuffle(all_keywords)  # 랜덤 섞기
    return all_keywords[:max_keywords]  # 최대 키워드 수만큼 선택

def remove_duplicates_and_optimize(keywords):
    """
    중복 키워드를 제거하고 최적화된 문자열로 결합하는 함수.
    
    Parameters:
    - keywords (List[str]): 키워드 리스트.
    
    Returns:
    - str: 중복 키워드가 제거되고 최적화된 문자열.
    """
    unique_keywords = list(dict.fromkeys(keywords))  # 중복 제거하면서 순서 유지
    return " ".join(unique_keywords).strip()  # 최종 문자열 생성

def generate_randomized_patterns(main_keyword, patterns, fixed_keywords, max_variations=3, max_keywords=10):
    """
    패턴과 고정 키워드를 랜덤으로 조합하여 다양한 상품명을 생성하는 함수.
    
    Parameters:
    - main_keyword (str): 메인 키워드.
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    - max_variations (int): 생성할 최대 변형 개수.
    - max_keywords (int): 각 상품명에서 사용할 최대 키워드 수.
    
    Returns:
    - List[str]: 랜덤화된 상품명 리스트.
    """
    variations = []  # 결과 리스트 초기화

    for i in range(max_variations):
        print(f"[디버그] {i+1}번째 패턴생성")

        # 1. 패턴 길이 랜덤화
        randomized_patterns = randomize_pattern_length(patterns)

        # 2. 고정 키워드와 랜덤 위치에 조합
        combined_keywords = randomize_fixed_keyword_position(main_keyword, randomized_patterns, fixed_keywords)

        # 3. 랜덤화된 조합 최적화
        optimized_name = remove_duplicates_and_optimize(combined_keywords[:max_keywords])
        variations.append(optimized_name)  # 최적화된 상품명 추가

    return variations

def randomize_pattern_length(patterns, min_length=3, max_length=7, must_include=None):
    """
    패턴 키워드 길이를 랜덤화하고, 필수 키워드를 포함.

    Parameters:
    - patterns (List[str]): 전체 패턴 키워드 리스트.
    - min_length (int): 패턴 키워드 최소 길이.
    - max_length (int): 패턴 키워드 최대 길이.
    - must_include (List[str]): 반드시 포함해야 할 키워드 리스트.

    Returns:
    - List[str]: 랜덤화된 패턴 키워드 리스트.
    """
    if must_include is None:
        must_include = []

    # 필수 포함 키워드를 먼저 추가
    randomized_patterns = must_include[:]

    # 필수 키워드를 제외한 나머지 키워드 중에서 랜덤 선택
    remaining_patterns = [p for p in patterns if p not in must_include]

    # 랜덤 길이 결정
    random_length = random.randint(min_length, max_length)

    # 남은 키워드에서 최대 샘플 가능한 크기를 계산
    max_remaining_sample = max(0, min(len(remaining_patterns), random_length - len(must_include)))

    # 랜덤 샘플 추가
    if max_remaining_sample > 0:
        randomized_patterns.extend(random.sample(remaining_patterns, max_remaining_sample))

    # 최종 결과 랜덤 순서로 반환
    random.shuffle(randomized_patterns)
    return randomized_patterns

def randomize_fixed_keyword_position(main_keyword, patterns, fixed_keywords):
    """
    고정 키워드를 패턴에 랜덤 위치에 삽입하는 함수.
    
    Parameters:
    - main_keyword (str): 상품의 메인 키워드.
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    
    Returns:
    - List[str]: 메인 키워드 + 랜덤으로 섞인 패턴 + 고정 키워드.
    """
    combined_keywords = patterns + fixed_keywords  # 패턴과 고정 키워드 합치기
    random.shuffle(combined_keywords)  # 랜덤 섞기
    return [main_keyword] + combined_keywords  # 메인 키워드는 항상 맨 앞

def mix_and_match_patterns_and_fixed(patterns, fixed_keywords, max_keywords=10):
    """
    패턴과 고정 키워드를 랜덤하게 섞고 일부만 선택하는 함수.
    
    Parameters:
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    - max_keywords (int): 최종 상품명에서 사용할 최대 키워드 수.
    
    Returns:
    - List[str]: 랜덤 섞인 패턴과 고정 키워드의 일부.
    """
    all_keywords = patterns + fixed_keywords  # 패턴과 고정 키워드 합치기
    random.shuffle(all_keywords)  # 랜덤 섞기
    return all_keywords[:max_keywords]  # 최대 키워드 수만큼 선택

def remove_duplicates_and_optimize(keywords):
    """
    중복 키워드를 제거하고 최적화된 문자열로 결합하는 함수.
    
    Parameters:
    - keywords (List[str]): 키워드 리스트.
    
    Returns:
    - str: 중복 키워드가 제거되고 최적화된 문자열.
    """
    unique_keywords = list(dict.fromkeys(keywords))  # 중복 제거하면서 순서 유지
    return " ".join(unique_keywords).strip()  # 최종 문자열 생성

def generate_randomized_patterns(main_keyword, patterns, fixed_keywords, max_variations=3, max_keywords=10):
    """
    패턴과 고정 키워드를 랜덤으로 조합하여 다양한 상품명을 생성하는 함수.
    
    Parameters:
    - main_keyword (str): 메인 키워드.
    - patterns (List[str]): 상위 검색 패턴 키워드.
    - fixed_keywords (List[str]): 고정 키워드.
    - max_variations (int): 생성할 최대 변형 개수.
    - max_keywords (int): 각 상품명에서 사용할 최대 키워드 수.
    
    Returns:
    - List[str]: 랜덤화된 상품명 리스트.
    """
    variations = []  # 결과 리스트 초기화

    for i in range(max_variations):
        print(f"[디버그] {i+1}번째 패턴생성")

        # 1. 패턴 길이 랜덤화
        randomized_patterns = randomize_pattern_length(patterns)

        # 2. 고정 키워드와 랜덤 위치에 조합
        combined_keywords = randomize_fixed_keyword_position(main_keyword, randomized_patterns, fixed_keywords)

        # 3. 랜덤화된 조합 최적화
        optimized_name = remove_duplicates_and_optimize(combined_keywords[:max_keywords])
        variations.append(optimized_name)  # 최적화된 상품명 추가

    return variations