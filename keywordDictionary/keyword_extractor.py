import sys
import os

import pandas as pd
from keywordOptimization.product_info import KeywordInfo, SubKeywordInfo

# 프로젝트 루트 절대 경로 추가
sys.path.append("f:/marketAutomation")

# # 현재 파일의 디렉토리를 기준으로 상위 디렉토리 절대 경로 추가
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(project_root)

import openai
from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary
from config.settings import OPENAI_API_KEY  # settings.py에서 API 키 불러오기

# API 키 설정
openai.api_key = OPENAI_API_KEY

def generate_category_description(dictionary):
    """
    사전에서 카테고리 목록을 가져와서 프롬프트에 포함할 설명 텍스트를 생성합니다.
    각 카테고리의 설명을 정의하여 GPT 프롬프트에 포함할 정보로 사용합니다.
    """
    category_descriptions = {
        "용도": "제품이 사용되는 상황 또는 목적 (예: 캠핑, 사무용, 실내용, 다이어트용, 운동용, 여행용)",
        "사양": "제품의 기능적 사양이나 특성 (예: 무선, 방수, 충전식, 120mm, 초경량)",
        "스타일": "제품의 디자인 스타일 (예: 심플, 모던, 미니멀, 빈티지)",
        "재질": "제품의 소재 (예: 나무, 플라스틱, 스테인리스)"
    }

    if not dictionary:  # dictionary가 비어 있는지 확인
        return "\n".join([f"{category}: {description}" for category, description in category_descriptions.items()])

    descriptions = []
    for category in KeywordInfo().get_categories().keys():  # KeywordInfo의 기본 카테고리 사용
        description = category_descriptions.get(category, f"{category}의 특징을 입력")
        descriptions.append(f"{category}: {description}")

    return "\n".join(descriptions)

def gpt_extract_main_and_sub_keywords(product_name, dictionary, model="gpt-3.5-turbo"):
    """
    GPT를 이용하여 상품명에서 메인 제품군과 카테고리별 보조 키워드를 추출하는 함수.
    """
    # 사전이 비어 있는 경우 기본 카테고리 정의
    if not dictionary:
        sub_keywords = KeywordInfo(main_keyword="")
    else:
        # 사전이 비어 있지 않을 경우 기존 방식대로 카테고리 생성
        sub_keywords = KeywordInfo(main_keyword="")



    # 카테고리 정보를 가져와 프롬프트에 포함
    category_info = generate_category_description(dictionary)

    # GPT에 전달할 프롬프트 설정
    prompt = (
        f"'{product_name}'이라는 상품의 주요 '제품군'과 '제품특징'를 다음 카테고리에 따라 분류하세요.\n"
        f"'제품군' 은 제품의 핵심적인 이름을 단일 단어로 나타냅니다.\n\n"
        f"카테고리 설명:\n{category_info}\n\n"
        f"카테고리 예시:\n"
        f"- '캠핑', '사무용' 등은 '용도'에 속합니다.\n"
        f"- '무선', '방수' 등은 '사양'에 속합니다.\n"
        f"- '심플', '빈티지' 등은 '스타일'에 속합니다.\n"
        f"- '빨간', '파란' 등은 '색상'에 속합니다.\n\n"
        f"주의사항:\n"
        f"- 상품명에 붙어 있는 단어(예: '숫자스티커101')는 숫자와 문자, 또는 서로 다른 단어를 분리해서 처리해 주세요.\n"
        f"- 예: '숫자스티커101' → '숫자', '스티커', '101'\n"
        f"응답 형식:\n"
        f"제품군: <메인 키워드>, 용도: <보조키워드>, 사양: <보조키워드>, 스타일: <보조키워드>.., 기타 카테고리: <보조키워드>..\n\n"
        f"예시 응답 형식:\n"
        f"제품군: 의자, 용도: 캠핑, 사양: 방수, 스타일: 없음, 추가 카테고리: 색상: 빨간\n\n"
        f"기존 카테고리와 맞지 않는 '보조키워드'는 기타 카테고리로 지정합니다. \n\n"
        f"주의: 상품명에 포함된 단어만 사용하고, 상품명에 없는 새로운 단어나 의미는 생성하지 마세요.\n"
        f"각 카테고리가 없으면 '없음'으로 표시하고, 정확히 위의 형식에 맞춰서 응답해 주세요."
    )

    try:
        # GPT 모델에 프롬프트 요청
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant specialized in extracting product categories and classifying keywords."},
                {"role": "user", "content": prompt}
            ]
        )

        # GPT 응답 추출 및 디버깅 출력
        extracted_data = response.choices[0].message['content'].strip()
        print(f"[디버그] GPT 응답: {extracted_data}")  # GPT 응답 내용 확인

        # 응답을 기반으로 메인 및 보조 키워드 추출
        main_keyword = None
        for line in extracted_data.split(", "):
            if "제품군:" in line:
                main_keyword = line.split("제품군:")[1].strip()
            elif "용도:" in line:
                sub_keywords.use.append(line.split("용도:")[1].strip())
            elif "사양:" in line:
                sub_keywords.spec.append(line.split("사양:")[1].strip())
            elif "스타일:" in line:
                sub_keywords.style.append(line.split("스타일:")[1].strip())
            elif "기타 카테고리:" in line:
                additional_categories = line.split("기타 카테고리:")[1].strip()
                for cat in additional_categories.split(","):
                    sub_keywords.extra.append(cat.strip())

        # '없음'으로 표시된 항목 제거
        sub_keywords.use = [kw for kw in sub_keywords.use if kw != "없음"]
        sub_keywords.spec = [kw for kw in sub_keywords.spec if kw != "없음"]
        sub_keywords.style = [kw for kw in sub_keywords.style if kw != "없음"]
        sub_keywords.extra = [kw for kw in sub_keywords.extra if kw != "없음"]

        return main_keyword, sub_keywords

    except openai.OpenAIError as e:
        # OpenAI API 호출 실패 시 처리
        print(f"[오류] OpenAI API 호출 실패: {e}")
        return None, KeywordInfo(main_keyword="", fixed_keywords=[], use=[], spec=[], style=[], extra=[])
    except (AttributeError, IndexError, KeyError) as e:
        # GPT 응답 형식 오류 시 처리
        print(f"[오류] GPT 응답 처리 실패: {e}")
        print(f"[디버그] 원본 응답: {response.choices[0].message['content'].strip() if 'response' in locals() else '응답 없음'}")
        return None, KeywordInfo(main_keyword="", fixed_keywords=[], use=[], spec=[], style=[], extra=[])
    except Exception as e:
        # 기타 예외 처리
        print(f"[오류] 예기치 않은 에러 발생: {e}")
        return None, KeywordInfo(main_keyword="", fixed_keywords=[], use=[], spec=[], style=[], extra=[])

def extract_keywords(product_name, dictionary, model="gpt-3.5-turbo"):
    """
    상품명에서 메인 키워드와 보조 키워드를 추출하는 함수.
    사전에 메인 키워드가 있는 경우 사전에서 바로 보조 키워드를 추출하고,
    메인 키워드가 없으면 GPT를 호출하여 키워드를 생성한 후 사전에 추가한다.
    
    Parameters:
    - product_name (str): 분석할 상품명.
    - dictionary (Dict[str, KeywordInfo]): 키워드 사전.
    - model (str): GPT 모델 이름 (기본값은 "gpt-3.5-turbo").

    Returns:
    - main_keyword (str): 상품의 메인 키워드.
    - sub_keywords (SubKeywordInfo): 상품에 대한 보조 키워드 정보 (메인 키워드 제외).
    - remaining_words (List[str]): 메인 키워드를 제외한 나머지 단어들.
    """
    
    try:

        # 초기 변수 설정
        main_keyword = None
        remaining_words = []
        sub_keywords = SubKeywordInfo()  # SubKeywordInfo 객체 생성 (보조 키워드 정보만 저장)

        # 상품명을 단어 단위로 분리하고 공백 및 대소문자 처리하여 리스트로 저장
        words = [word.strip().lower() for word in product_name.split()]
        print(f"[디버그] 기본상품명 분석 시작")
        # print(f"[디버그] 상품명 분리 단어 리스트: {words}")
        print("-" * 50)  # 구분선 추가

        # 사전에서 상품명과 일치하는 메인 키워드 검색
        for dict_key, keyword_info in dictionary.items():
            # 사전의 키워드들을 쉼표로 구분하여 리스트로 변환한 후 대소문자 처리
            dict_main_keywords = [key.strip().lower() for key in dict_key.split(',')]

            # 상품명에 사전의 메인 키워드가 포함된 경우를 찾음
            if any(word in dict_main_keywords for word in words):
                main_keyword = dict_key
                print(f"[디버그] 사전에 존재하는 메인 키워드 발견: {main_keyword}")

                # remaining_words 설정: 메인 키워드를 제외한 나머지 단어들로 구성
                remaining_words = [w for w in words if w not in dict_main_keywords]
                
                # 사전에 고정 키워드 추가 (기존 고정 키워드에 누적)
                dictionary[main_keyword].add_keywords(fixed=remaining_words)
                
                # 현재 상품명에 한정된 고정 키워드 정보로 SubKeywordInfo 생성
                sub_keywords = SubKeywordInfo(
                    use=keyword_info.use,
                    spec=keyword_info.spec,
                    style=keyword_info.style,
                    extra=keyword_info.extra,
                    fixed_keywords=remaining_words  # 반환 시 현재 상품명에 한정된 고정 키워드만 포함
                )
                break  # 사전에서 메인 키워드를 찾으면 반복 종료

        # 사전에 메인 키워드가 없는 경우 GPT 호출을 통해 키워드 생성
        if not main_keyword:
            print("[디버그] 사전에 메인 키워드가 없으므로 GPT 호출 시작.")
            
            # GPT 호출하여 메인 키워드와 보조 키워드 생성
            main_keyword, gpt_output = gpt_extract_main_and_sub_keywords(product_name, dictionary, model=model)
            
            # GPT 응답이 있을 경우 응답 내용을 처리
            if main_keyword:
                print(f"[디버그] GPT 응답 - main_keyword: {main_keyword}, sub_keywords: {gpt_output}")

                # remaining_words 설정: GPT가 반환한 메인 키워드를 제외한 단어들로 구성
                remaining_words = [w for w in words if w != main_keyword]

                # GPT 결과를 사전에 고정 키워드로 추가
                gpt_output.fixed_keywords = remaining_words
                dictionary[main_keyword] = gpt_output  # GPT 응답을 사전에 저장

                # 현재 상품명에 한정된 고정 키워드 정보로 SubKeywordInfo 생성
                sub_keywords = SubKeywordInfo(
                    use=gpt_output.use,
                    spec=gpt_output.spec,
                    style=gpt_output.style,
                    extra=gpt_output.extra,
                    fixed_keywords=remaining_words  # 반환 시 현재 상품명에 한정된 고정 키워드만 포함
                )

        # 최종 반환할 메인 키워드, 보조 키워드 정보, remaining_words 디버그 출력
        print(f"[디버그] 최종 반환 main_keyword: {main_keyword}")
        print(f"[디버그] 고정키워드: {remaining_words}")
        #print(f"[디버그] 최종 반환 보조키워드: {sub_keywords}")

        # 사전 업데이트 후 저장
        save_dictionary(dictionary)  # 기존 키워드가 업데이트된 경우 저장

        # 메인 키워드, 보조 키워드 정보 (SubKeywordInfo), 메인 키워드를 제외한 나머지 단어 리스트 반환
        return main_keyword, sub_keywords, remaining_words

    except openai.OpenAIError as e:
        print(f"[오류] OpenAI API 호출 실패: {e}")
    except KeyError as e:
        print(f"[오류] 키 처리 실패: {e}")
    except Exception as e:
        print(f"[오류] 예기치 못한 에러 발생: {e}")

    # 실패 시 기본값 반환 (상품명 그대로 반환)
    print("[경고] 키워드 추출 실패, 기본값으로 반환.")
    return product_name, SubKeywordInfo(), product_name.split()




if __name__ == "__main__":
    # 사전 로드
    dictionary = load_dictionary()

    # 테스트용 예시 상품명
    test_product_name = "24칸 악세사리 보관통 투명"

    # 9구 멀티옷걸이 블루
    # 9구 멀티옷걸이 그린
    # 3공 다이어리 오렌지
    # 24칸 악세사리 보관통 투명
    # 발세척매트 풋브러쉬 블루
    # 필라테스 쪼임이 핑크
    # 핸드스퀴지
    # 이동식 3단 틈새수납장 화이트
    # 필라테스 스트레칭 튜빙바


    
    # GPT 프롬프트 다이렉트 테스트 (메인 및 보조 키워드 추출)
    # main_keyword, sub_keywords = gpt_extract_main_and_sub_keywords(test_product_name, dictionary, model="gpt-3.5-turbo")
    # print(f"메인 키워드: {main_keyword}")
    # print(f"보조 키워드: {sub_keywords}")

    # 추가적인 모델 선택을 포함한 예시
    model_choice = "gpt-3.5-turbo"  # 또는 gpt-4
    main_keyword, sub_keywords = extract_keywords(test_product_name, dictionary, model=model_choice)
    print(f"메인 키워드: {main_keyword}")
    print(f"보조 키워드: {sub_keywords}")

    # for category, keywords in sub_keywords.items():
    #     print(f"{category} 키워드: {', '.join(keywords) if keywords else '없음'}")
