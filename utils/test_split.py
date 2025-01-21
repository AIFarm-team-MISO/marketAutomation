import re

def split_keywords(keyword):
    # 정규식으로 숫자+문자, 숫자-숫자+문자, 일반 단어 분리
    split_keywords = re.findall(r'\d+[a-zA-Z]+|\d+-\d+[^\s]*|[^\s]+', keyword)
    return [kw.strip() for kw in split_keywords if kw.strip()]


'''
"1cm 15칸 1-100번": ["1cm", "15칸", "1-100번"],
        "파리채 30cm": ["파리채", "30cm"],
        "티셔츠사이즈XS": ["티셔츠사이즈XS"],
        "1p 15cm": ["1p", "15cm"],
        "휴대용 안경케이스": ["휴대용", "안경케이스"],
        "2-in-1": ["2-in-1"],
        "아이템100P": ["아이템100P"],
        "LED손전등": ["LED손전등"],
        "10kg포대": ["10kg포대"],
        "1-15cm 자": ["1-15cm", "자"],
        "상품명-100": ["상품명-100"],

'''

def run_tests():
    test_cases = {
        "1cm 15칸 1-100번": ["1cm", "15칸", "1-100번"],
        "파리채 30cm": ["파리채", "30cm"],
        "티셔츠사이즈XS": ["티셔츠사이즈XS"],
        "1p 15cm": ["1p", "15cm"],
        "휴대용 안경케이스": ["휴대용", "안경케이스"],
        "2-in-1": ["2-in-1"],
        "아이템100P": ["아이템100P"],
        "LED손전등": ["LED손전등"],
        "10kg포대": ["10kg포대"],
        "1-15cm 자": ["1-15cm", "자"],
        "상품명-100": ["상품명-100"],


    }

    for test_input, expected_output in test_cases.items():
        result = split_keywords(test_input)
        assert result == expected_output, f"Test failed for input: {test_input}\nExpected: {expected_output}\nGot: {result}"
        print(f"Test passed for input: {test_input}\nResult: {result}")



import re

import re

import re

def process_keywords(keyword):
    """
    키워드를 필터링 및 처리하고 공백 없이 합치는 함수.
    
    :param keyword: 필터링할 원본 키워드 문자열
    :return: 필터링 및 처리된 공백 없는 키워드 문자열
    """
    # 특수문자 및 괄호를 기준으로 키워드 분리
    split_keywords = re.split(r'[()\s]+', keyword)

    # 'x' 또는 'X'를 숫자 사이에 있는 경우만 유지하고, 그 외에는 제거
    processed_keywords = []
    for kw in split_keywords:
        if re.match(r'\d+x\d+', kw, re.IGNORECASE):  # 숫자x숫자 유지
            processed_keywords.append(kw)
        else:  # 특수문자 제거 (괄호 포함)
            kw = re.sub(r'[^\w\s-]', '', kw)  # 알파벳, 숫자, 하이픈만 남김
            processed_keywords.append(kw)
    
    # 공백 제거 및 빈 문자열 필터링
    processed_keywords = [kw.strip() for kw in processed_keywords if kw.strip()]
    
    # 숫자가 4자리 이상 포함된 키워드 및 숫자만으로 된 키워드 삭제
    filtered_keywords = [
        kw for kw in processed_keywords
        if not (re.search(r'\b\d{4,}\b', kw) or re.fullmatch(r'\d+', kw) and len(kw) >= 4)
    ]

    # 공백 없이 키워드 합치기
    filtered_keywords = ''.join(filtered_keywords)

    # 디버깅용 출력
    print("원본 키워드:", keyword)
    print("분리된 키워드:", split_keywords)
    print("처리된 키워드:", processed_keywords)
    print("필터링된 키워드:", filtered_keywords)
    print("최종 키워드:", filtered_keywords)

    return filtered_keywords






if __name__ == "__main__":
    # run_tests()

    # 테스트할 문자열
    # test_input = "1cm 15칸 1-100번 12345  22cm 1P 특수문자@#$% 제거 3포켓 [후]  164pcs 확인 107x207 우드 20CM(블랙)1P "
    test_input = "(다국어)흡연실(초록)(9132)" 

    # 결과 출력
    result = process_keywords(test_input)
    print(result)
