import json
import sys
import os
import re

import pandas as pd
from keywordOptimization.product_info import KeywordInfo, SubKeywordInfo

# 프로젝트 루트 절대 경로 추가
sys.path.append("f:/marketAutomation")

# # 현재 파일의 디렉토리를 기준으로 상위 디렉토리 절대 경로 추가
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(project_root)

# Logger 클래스 가져오기
from utils.log_utils import Logger

# Logger 초기화
logger = Logger(log_file="logs/debug.log", enable_console=True)

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
    연관검색어와 브랜드키워드도 함께 추출합니다.
    """

    # 카테고리 정보를 가져와 프롬프트에 포함
    category_info = generate_category_description(dictionary)

    # GPT에 전달할 프롬프트 설정
    prompt = (
        f"'{product_name}'이라는 상품명에서 아래 지침을 따라 '제품군'과 '제품특징'을 분류하세요:\n"
        f" '제품군' 은 제품의 핵심적인 이름을 단일 단어로 나타냅니다.\n\n"
        f"  '제품군'은 제품의 핵심적인 이름의 상위 개념으로 설정합니다:\n"

        
        f"- '제품군' 선정 시, 다음 지침을 참고하세요:\n"
        f"  '제품군'은 제품의 본질을 나타내는 단어로, 제품의 구체적 이름을 나타내야 합니다.\n"
        f"  예: '보관' (행동/행위) ❌, 'DVD케이스' (구체적 제품명) ✅\n"
        f"  추출된 '제품군'은 제품의 핵심적인 이름을 단일 명사로 표현하며, 모호하거나 추상적인 단어는 제외해야 합니다.\n"
        f"  예: '관리', '사용', '보관' ❌, '책상', '노트', '가방' ✅\n"
        f"  행동이나 행위를 나타내는 단어는 배제하고, 물리적으로 존재하는 제품이나 물건을 나타내는 단어를 사용하세요.\n"
        f"  예: '보관' ❌ -> 'DVD케이스' ✅\n"
        f"  제품의 용도를 설명하지 않고, 물리적 형태와 본질을 나타냅니다.\n"
        f"  예: '인사관리도구' ❌ -> '파일' ✅\n"
        f"  '제품군'은 복합명사(예: 'DVD보관지갑')가 아닌, 더 넓은 의미의 상위 단어로 설정합니다.\n"
        f"  예: 'DVD보관지갑' ❌ -> 'DVD케이스' ✅\n"

        
        f"   유사한 의미를 가진 단어를 포함할 수 있습니다.\n"
        f"   예: '야간독서등' (협소한 범위) ❌ -> '독서등' (넓은 범위) ✅\n"
        f"   '야간독서등', '도서등', '독서램프' 등 유사한 의미를 가진 단어 중 가장 일반적인 단어를 선택하세요.\n"
        f"   예: '야간독서등' ❌ -> '독서등' ✅\n"
        f"   '제품군' 선정 시,유사성을 고려하되, 너무 일반적인 단어는 배제합니다.\n"
        f"   예: '조명' ❌ -> '독서등' ✅\n"
        f"   제품군이 실제 고객이 검색에서 사용할 법한 상위 단어인지 검토하세요.\n"


        f"카테고리 설명:\n{category_info}\n\n"
        f"카테고리 예시:\n"
        f"- '캠핑', '사무용' 등은 '용도'에 속합니다.\n"
        f"- '무선', '방수' 등은 '사양'에 속합니다.\n"
        f"- '심플', '빈티지' 등은 '스타일'에 속합니다.\n"
        f"- '빨간', '파란' 등은 '색상'에 속합니다.\n\n"
        f"주의사항:\n"
        f"- 상품명에 붙어 있는 단어(예: '숫자스티커101')는 숫자와 문자, 또는 서로 다른 단어를 분리해서 처리해 주세요.\n"
        f"- 예: '숫자스티커101' → '숫자', '스티커', '101'\n"
        f"기존 카테고리와 맞지 않는 '보조키워드'는 기타 카테고리로 지정합니다. \n\n"
        # f"주의: 반드시 상품명에 포함된 단어만 사용하고, 상품명에 없는 새로운 단어나 의미는 생성하지 마세요.\n" 
        #         상품명이외의 단어도 사용할수 있게 함으로써 좀더 차별화를 두기위해서 현재 지워둠 .
        f"각 카테고리가 없으면 '없음'으로 표시하고, 정확히 위의 형식에 맞춰서 응답해 주세요."

        f"추가 작업:\n"    
        f"1. '제품군' 의 '연관검색어' 를 5개 추출하세요. \n"
        f" - '연관검색어' 는 '제품군'과 관련성이 높아야 하며 실제 사용자가 쇼핑 검색에서 입력할 법한 간결하고 구체적인 키워드여야 합니다.\n"
        f" - 특히, 한국어에서는 '붙여쓰기'(예: 관리도서)가 '띄어쓰기'(예: 관리 도서)보다 니치 키워드로 작용할 가능성이 높습니다."
        f" - 붙여쓰기 키워드는 특정 검색 쿼리와 정확히 매칭되기 쉽고, 경쟁이 적어 SEO에서 더 유리합니다.\n"
        f" - 따라서 '연관검색어' 생성 시, '붙여쓰기' 로서 '니치키워드' 를 우선적으로 생성해 주세요 \n"

        f"- 예시: \n"
        f"  - 상품명: 독서등\n"
        f"  연관검색어: 군인독서등, 야간독서조명, LED독서등, 밤독서등, 야간스탠드\n"
        f"  - 상품명: 클리어북\n"
        f"  연관검색어: 인사관리책, 회사파일, 문서관리노트, 클리어파일\n"

        f" - 주의 : 새로운 단어를 생성하지 말고 쇼핑검색에서 실제 사용될만한 키워드을 만들어주세요.\n"
        f" - 주의 : 비현실적이거나 상품관 관련없는 단어(예:전생, 전투... )는 포함하지 마세요.\n"
        f" - 주의 : 중복되는 키워드는 제외하고 유사한 의미의 키워드로 바꿔 주세요.\n"
        # f" - 주의 : 쇼핑 검색에서 실제로 사용할 가능성이 높은 단어만 포함하세요.\n"
        # f" - 주의 : '연관검색어'은 반드시 '붙여쓰기' 키워드로만 만들어 주세요. \n"
        f" - 주의 : '연관검색어'은 반드시 공백없는 키워드로만 만들어 주세요. \n"
        f"            예: 'DVD 케이스' ❌ -> 'DVD케이스' ✅\n"
        f" - 주의 : '12P, 1p, 2P'등 갯수와 관련된 키워드는 '연관검색어' 에서 제외하세요. \n"
        # f" - 주의 : 검색SEO와 니치키워드에 적합하도록 간결하고 실제 검색에서 활용될 법한 키워드만 생성하세요.\n"
        f" - 주의 : '연관검색어'는 반드시 '제품군'과 연관성이 있어야 합니다.\n"



        f"2. '제품군' 관련된 주요 브랜드명을 최대 5개 추출하세요. "
        f"브랜드명은 상품명과 관련성이 높은 실제 브랜드를 제안해야 하며, 새로운 브랜드를 생성하지 마세요.\n"


        f"최종 응답 형식: JSON 형식으로 제공하세요. \n"
        f"{{\n"
        f"  \"제품군\": \"<메인 키워드>\",\n"
        f"  \"용도\": [\"<용도 키워드1>\", \"<용도 키워드2>\"],\n"
        f"  \"사양\": [\"<사양 키워드1>\", \"<사양 키워드2>\"],\n"
        f"  \"스타일\": [\"<스타일 키워드1>\", \"<스타일 키워드2>\"],\n"
        f"  \"기타 카테고리\": [\"<기타 키워드1>\", \"<기타 키워드2>\"],\n"
        f"  \"GPT연관검색어\": [\"<검색어1>\", \"<검색어2>\", \"<검색어3>\"],\n"
        f"  \"브랜드키워드\": [\"<브랜드1>\", \"<브랜드2>\", \"<브랜드3>\"]\n"
        f"}}\n\n"
        f"예시 응답:\n"
        f"{{\n"
        f"  \"제품군\": \"의자\",\n"
        f"  \"용도\": [\"캠핑\"],\n"
        f"  \"사양\": [\"방수\"],\n"
        f"  \"스타일\": [],\n"
        f"  \"기타 카테고리\": [\"색상: 빨간\", \"추가 키워드: 경량\", \"추가 키워드: 12p\"],\n"
        f"  \"연관검색어\": [\"캠핑의자\", \"차박의자\", \"낚시의자\", \"접이식의자\", \"휴대용의자\"],\n"
        f"  \"브랜드키워드\": [\"콜맨\", \"헬리녹스\", \"스노우라인\"]\n"
        f"}}\n\n"
        f"주의사항:\n"
        f"- 빈 값은 빈 배열([])로 표시하세요.\n"
        f"- 정확히 JSON 형식에 맞게 작성하세요.\n"
        f"- 의미 없는 키워드나 특수문자(예: '**')는 포함하지 마세요."
        

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
        gpt_data = json.loads(response.choices[0].message["content"].strip())
         
        # GPT 응답 출력
        # logger.log_gpt_response(gpt_data)

        
        return gpt_data  # JSON 데이터 반환

    except openai.OpenAIError as e:
        print(f"[오류] OpenAI API 호출 실패: {e}")
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파싱 실패: {e}")
    except Exception as e:
        print(f"[오류] 예기치 않은 에러 발생: {e}")

    # 오류 발생 시 기본값 반환
    return {
        "제품군": "없음",
        "용도": [],
        "사양": [],
        "스타일": [],
        "기타 카테고리": []
    }






def extract_keywords(product_name, dictionary, model="gpt-3.5-turbo"):
    """
    상품명에서 메인 키워드와 고정 키워드를 추출하는 함수.
    기존 사전을 우선적으로 조회하고, 없을 경우 GPT를 호출하여 키워드를 생성 후 사전에 추가.
    
    Parameters:
    - product_name (str): 분석할 상품명.
    - dictionary (Dict[str, dict]): 키워드 사전.
    - model (str): GPT 모델 이름 (기본값: "gpt-3.5-turbo").

    Returns:
    - dict: 최적화된 상품 데이터 (메인 키워드, 고정키워드, 연관검색어 등 포함).
    """

    # 초기 변수 설정
    main_keyword = None
    gpt_data = None  # 사전에 저장될 모든 데이터

    # >> 빈 값 검증 추가
    if not product_name.strip():
        logger.log("⚠️ 기본상품명이 비어 있어 처리하지 않습니다.", level="WARNING")
        return None

    # 상품명을 단어 단위로 분리하고 공백 및 대소문자 처리하여 리스트로 저장
    words = [word.strip().lower() for word in product_name.split()]
    logger.log("기본상품명 분석 시작", level="DEBUG")
    logger.log_list("상품명 분리 단어 리스트", words)
    logger.log_separator()

   
    '''
        - 기본상품명을 통한 사전 조회 - 
        1. 기존과 같은 상품명이 들어올때
            최초 사전에 기본상품명이 있는지 확인하여 (기본상품명은 메인키워드에 리스트형태로 종속되있음)
            만약 존재한다면 기본상품명에에 속한 모든 데이터를 그대로 반환한다.
            *** 사전에 저장안됨 ***

        2. 다른상품명이 들어온 경우 무조건 gpt호출
            2-1. 다른상품명일 경우 메인키워드,보조키워드,고정키워드등 gpt답변을 반환 후 사전저장
            *** 사전에 저장 ***

            2-2. 다른상품명이지만 메인키워드가 사전에 있는경우
                 - 메인키워드의 기본상품명 리스트에 기본상품명 추가
                 - 메인키워드의 고정키워드 리스트에 고정키워드 추가
                 - 메인키워드의 연관상품명 리스트에 새로운 내용이 있으면 추가
            *** 사전에 저장 ***
        
        3. 사전에 저장되는 내용과 반환되는 값은 다른값. 
            - 사전내용 : 기본상품명, 고정키워드가 리스트
            - 반환내용 : 기본상품명, 고정키워드가 단일값


    '''
    # 1️⃣ 기본상품명 기준 사전조회
    for key, data in dictionary.items():
        # 기존 데이터에서 기본상품명을 확인하고 관련 데이터 반환
        if product_name in data.get("기본상품명", []):
            logger.log(f"기본상품명 '{product_name}' 을 사전에서 발견", level="INFO")
            main_keyword = key

            # 기본상품명과 고정키워드, 연관검색어 등의 데이터를 추출
            idx = data["기본상품명"].index(product_name)
            fixed_keywords = data["고정키워드"][idx] if idx < len(data["고정키워드"]) else []
            gpt_data = data.copy()  # 기존 데이터 복사
            gpt_data["기본상품명"] = product_name  # 단일 값으로 반환
            gpt_data["고정키워드"] = fixed_keywords  # 단일 리스트로 반환

            # 기존 데이터에서 연관검색어, 브랜드키워드 등은 그대로 유지
            #logger.log(f"사전에서 반환된 데이터: {gpt_data}", level="DEBUG")
            logger.log(f"1️⃣사전에 기본상품명 존재하여 기존데이터 반환!", level="DEBUG")
            break
    
    # 2️⃣ 메인키워드 기준 추가 조회 (기본상품명이 사전에 없는 경우)
    if not gpt_data:
        logger.log(f"기본상품명 '{product_name}' 사전에 없음. 메인키워드 기준 추가 조회", level="INFO")

        # GPT 호출로 메인키워드 생성 및 고정키워드 추출
        gpt_result = gpt_extract_main_and_sub_keywords(product_name, dictionary, model=model)

        # >> GPT 응답 검증 추가
        if not gpt_result or not gpt_result.get("제품군"):
            logger.log("❌ GPT 호출 결과가 유효하지 않아 저장하지 않습니다.", level="ERROR")
            return None

        # GPT 응답 처리 : 메인키워드 설정 
        main_keyword = gpt_result.get("제품군", "").strip()
        # 고정키워드 설정 : GPT에서 반환된 메인 키워드가 words에 포함된 경우만 제외
        fixed_keywords = [w for w in words if w != main_keyword.lower()]
        # GPT 결과로 gpt_data 반환 데이터 업데이트
        gpt_result.update({"고정키워드": fixed_keywords})


        # GPT응답의 메인키워드가 사전에 있는 경우 기본상품명, 고정키워드, 연관검색어 추가
        if main_keyword in dictionary:
            logger.log(f"2️⃣-2️⃣ 사전에서 기존 메인키워드 '{main_keyword}' 발견" , level="INFO")
            
            logger.log(f"메인키워드 '{main_keyword}' 기존 기본상품명에 '{product_name}'추가" , level="INFO")
            logger.log(f"메인키워드 '{main_keyword}' 기존 고정키워드에 '{fixed_keywords}'추가" , level="INFO")

            dictionary[main_keyword]["기본상품명"].append(product_name)
            dictionary[main_keyword]["고정키워드"].append(fixed_keywords)

            # 연관검색어 병합 로직 추가(중복방지포함)
            existing_related_keywords = set(dictionary[main_keyword]["GPT연관검색어"])
            new_related_keywords = set(gpt_result.get("GPT연관검색어", []))
            merged_related_keywords = list(existing_related_keywords | new_related_keywords)
            dictionary[main_keyword]["GPT연관검색어"] = merged_related_keywords
            logger.log(f"GPT연관검색어 병합 완료: {merged_related_keywords}", level="INFO")

        else:
            # 새로운 메인키워드 추가
            logger.log(f"2️⃣-1️⃣ 메인키워드 '{main_keyword}' 신규 생성", level="INFO")
            
            # 사전에 저장할 데이터 생성
            saved_data = {
                "기본상품명": [product_name],  # 리스트로 저장
                "제품군": main_keyword,
                "고정키워드": [fixed_keywords],  # 리스트로 저장
                "GPT연관검색어": gpt_result.get("GPT연관검색어", []),
                "브랜드키워드": gpt_result.get("브랜드키워드", []),
                "용도": gpt_result.get("용도", []),
                "사양": gpt_result.get("사양", []),
                "스타일": gpt_result.get("스타일", []),
                "기타 카테고리": gpt_result.get("기타 카테고리", []),
                "네이버연관검색어": [],  # 초기값으로 빈 리스트 설정
                "패턴": []  # 초기값으로 빈 리스트 설정
            }
            
            dictionary[main_keyword] = saved_data
            logger.log(f"✅ 메인키워드 '{main_keyword}' 데이터 저장 완료", level="INFO")


        # gpt 호출후 반환할 데이터 생성
        gpt_data = {
            "기본상품명": product_name,  # 반환 데이터는 단일 값
            "제품군": main_keyword,
            "고정키워드": fixed_keywords,  # 반환 데이터는 단일 리스트
            "GPT연관검색어": gpt_result.get("GPT연관검색어", []),
            "브랜드키워드": gpt_result.get("브랜드키워드", []),
            "용도": gpt_result.get("용도", []),
            "사양": gpt_result.get("사양", []),
            "스타일": gpt_result.get("스타일", []),
            "기타 카테고리": gpt_result.get("기타 카테고리", []),
            "네이버연관검색어": [],  # 초기값으로 빈 리스트 설정
            "패턴": []  # 초기값으로 빈 리스트 설정
        }

        # 디버깅: 반환 데이터 확인
        # logger.log(f"최종 GPT 데이터 반환: {gpt_data}", level="DEBUG")
        logger.log(f"2️⃣사전에 기본상품명 없어 GPT데이터 반환!", level="DEBUG")
    

    # 3️⃣ 사전 저장
    save_dictionary(dictionary)

    # 메인 키워드, 보조 키워드 정보(제품특성, GPT연관검색어, 브랜드키워드):JSON 형식, 메인 키워드를 제외한 나머지 단어 리스트 반환
    return wrap_data_with_main_keyword(main_keyword, gpt_data)

def wrap_data_with_main_keyword(main_keyword, gpt_data):
    ''' 
    주어진 데이터 gpt_data를 main_keyword로 묶어 상위 구조를 생성하는 함수.

    Args:
        main_keyword (str): 
            상위에 추가할 메인 키워드. 
            최상위 딕셔너리의 키로 사용됩니다.
            예: "DVD케이스", "USB메모리"
        
        gpt_data (dict): 
            하위에 위치할 데이터를 담고 있는 딕셔너리.
            생성된 딕셔너리의 값으로 설정됩니다.
            예: {"기본상품명": "DVD 보관함", "제품군": "DVD케이스", ...}

    Returns:
        dict: 
            main_keyword를 최상위 키로 하고, gpt_data를 값으로 가지는 딕셔너리.
            예: {"DVD케이스": {"기본상품명": "DVD 보관함", "제품군": "DVD케이스", ...}}

    '''
    # main_keyword를 최상위 키로, gpt_data를 값으로 설정한 딕셔너리 생성 및 반환
    return {main_keyword: gpt_data}

def refine_main_keyword(main_keyword, dictionary):
    """
    메인 키워드를 정제하는 함수. 
    상위 개념의 키워드가 사전에 존재하면 대체.
    현재는 사전에 키워드가 적고 키워드호출에 gpt비용이 발생하므로
    이코드는 일단 적용하지 않음
    
    Parameters:
    - main_keyword (str): 추출된 메인 키워드
    - dictionary (dict): 기존 키워드 사전

    Returns:
    - refined_keyword (str): 정제된 메인 키워드
    """
    for existing_keyword in dictionary.keys():
        if existing_keyword in main_keyword and existing_keyword != main_keyword:
            # 로그 추가: 정제 대상 발견
            logger.log(
                f"정제 대상 발견: '{main_keyword}' -> '{existing_keyword}' (사전에 상위 개념 키워드 존재)", 
                level="INFO"
            )
            return existing_keyword  # 상위 개념으로 대체
    
    # 로그 추가: 정제가 필요 없는 경우
    logger.log(f"정제 대상 아님: '{main_keyword}'", level="DEBUG")
    return main_keyword



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
