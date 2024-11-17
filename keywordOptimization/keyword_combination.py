# keywordOptimization/keyword_combination.py

from collections import Counter
import re
from typing import List, Set
import random

from keywordOptimization.randomize_keyword import randomize_pattern_length



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


def combine_keywords(main_keyword, fixed_keywords, sub_keywords, patterns, variation=False):
    """
    메인 키워드와 고정 키워드, 보조 키워드, 그리고 패턴을 조합하여 최적화된 상품명을 생성하는 함수.
    
    Parameters:
    - main_keyword (str): 상품의 메인 키워드.
    - fixed_keywords (List[str]): 고정 키워드 목록.
    - sub_keywords (KeywordInfo): 상품의 보조 키워드들.
    - patterns (List[str]): 상위 검색 결과에서 추출된 상위 빈도 키워드 리스트.
    - variation (bool): True일 경우 다양한 조합을 위해 상위 빈도 키워드 순서를 변화시켜 생성.
    
    Returns:
    - str: 최적화된 상품명.
    """

    # 전달된 파라미터 디버깅 출력
    print("\n" + "="*100)
    print("[디버그] 검색에 따른 상품명 키워드 조합시작")
    print("="*100)
    print(f"[디버그] 조합전 키워드")
    print(f"[디버그] 메인키워드: {main_keyword}")
    print(f"[디버그] 고정키워드: {fixed_keywords}")
    # print(f"[디버그] 보조키워드 - use: {sub_keywords.use}, spec: {sub_keywords.spec}, style: {sub_keywords.style}, extra: {sub_keywords.extra}")
    print(f"[디버그] patterns: {patterns}")
    print("-" * 50)  # 구분선 추가
    
    # 보조 키워드를 처리하여 리스트로 반환
    # processed_sub_keywords = process_sub_keywords(sub_keywords)

    # fixed_keywords가 문자열로 전달된 경우 리스트로 변환
    if isinstance(fixed_keywords, str):
        fixed_keywords = [kw.strip() for kw in fixed_keywords.split(",") if kw.strip()]
    
    # 최종 키워드 리스트 생성: 메인 키워드 + 패턴 + 보조 키워드
    combined_keywords = [main_keyword] + patterns + fixed_keywords

    # 첫 번째 패턴 생성
    print("="*50)
    print("🎨 [디버그] 1번째 패턴 생성")
    print("- 키워드 리스트 (2줄 표시):")
    half = len(combined_keywords) // 2
    print("  상단:", ", ".join(combined_keywords[:half]))
    print("  하단:", ", ".join(combined_keywords[half:]))

    # variation 옵션이 활성화된 경우
    if variation:
        print("="*50)
        print("🎨 [디버그] 2번째 패턴 생성 (Variation 활성화)")
        combined_keywords = patterns + [main_keyword] + fixed_keywords
        print("- 키워드 리스트 (2줄 표시):")
        half = len(combined_keywords) // 2
        print("  상단:", ", ".join(combined_keywords[:half]))
        print("  하단:", ", ".join(combined_keywords[half:]))


    # 중복을 제거하고 최적화된 상품명 생성
    # 중복 제거를 포함한 최적화
    unique_combined_keywords = list(dict.fromkeys(combined_keywords))  # 중복 순서 유지 제거
    optimized_name = remove_duplicates_and_optimize(unique_combined_keywords)

    # 중복 제거 및 최적화 전 키워드 리스트 출력
    print("="*50)
    print("🔍 [디버그] 중복 제거 및 최적화 키워드 리스트")
    half = len(combined_keywords) // 2
    print("- 키워드 리스트 (2줄 표시):")
    print("  상단:", ", ".join(combined_keywords[:half]))
    print("  하단:", ", ".join(combined_keywords[half:]))

    # 최적화된 상품명 출력
    print("\n✨ [디버그] 최적화된 상품명 생성")
    print(f"  - 최적화된 상품명: {optimized_name}")
    print("="*50)
    
    return optimized_name

