from utils.global_logger import logger

import pandas as pd

import pandas as pd
import random
from utils.global_logger import logger

def shuffle_keywords_in_column(dataframe: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    특정 열의 문자열을 키워드로 나누어 무작위로 섞은 후 다시 결합하여 저장하는 함수.

    :param dataframe: pandas DataFrame
    :param column_name: 키워드를 셔플할 열 이름
    :return: 값이 변경된 DataFrame
    """
    try:
        if column_name not in dataframe.columns:
            raise ValueError(f"'{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        shuffled_names = []

        for idx, value in enumerate(dataframe[column_name]):
            # 문자열이 아닌 경우 예외 처리
            if not isinstance(value, str):
                logger.log(f"⚠️ {idx+1}번째 행의 값이 문자열이 아님: {value}", level="WARNING")
                shuffled_names.append(value)
                continue

            # 키워드 나누기
            keywords = value.strip().split()
            random.shuffle(keywords)  # 키워드 섞기
            shuffled_name = ' '.join(keywords)
            shuffled_names.append(shuffled_name)

            # logger.log(f"🔄 {idx+1}번째 행 - 원본: '{value}' -> 셔플: '{shuffled_name}'", level="DEBUG", also_to_report=True)

        # 데이터프레임에 적용
        dataframe[column_name] = shuffled_names

        logger.log(f"✅ '{column_name}' 열의 모든 상품명이 키워드 단위로 셔플 완료.", level="INFO", also_to_report=True, separator="1line")

        return dataframe

    except Exception as e:
        raise ValueError(f"'{column_name}' 열의 상품명을 셔플하는 중 문제가 발생했습니다: {e}")


def swap_image_column(dataframe: pd.DataFrame, column1: str, column2: str) -> pd.DataFrame:
    """
    두 열의 값을 교환하고, column1이 비어 있는 경우 해당 행을 삭제하며,
    column2가 비어 있는 경우 column1의 데이터를 column2에 복사합니다.

    :param dataframe: 값을 교환할 데이터프레임
    :param column1: 첫 번째 열 이름 (비어 있으면 행 삭제 대상)
    :param column2: 두 번째 열 이름 (비어 있으면 column1 값을 복사)
    :return: 수정된 데이터프레임
    """
    try:
        # 열이 데이터프레임에 존재하는지 확인
        if column1 not in dataframe.columns or column2 not in dataframe.columns:
            raise ValueError(f"'{column1}' 또는 '{column2}' 열이 데이터프레임에 존재하지 않습니다.")
        
        # column1이 비어있는 경우 해당 행 삭제
        initial_row_count = len(dataframe)
        dataframe = dataframe.dropna(subset=[column1])
        removed_rows_count = initial_row_count - len(dataframe)
        
        if removed_rows_count > 0:
            logger.log(f"⚠️ '{column1}' 열이 비어 있는 {removed_rows_count}개의 행이 삭제되었습니다.", level="WARNING", also_to_report=True, separator="none")
        
        # column2가 비어있는 경우 column1 값을 복사
        dataframe[column2] = dataframe[column2].fillna(dataframe[column1])
        
        # 열 값 교환
        dataframe[column1], dataframe[column2] = dataframe[column2], dataframe[column1]
        
        logger.log(f"✅ '{column1}' 열과 '{column2}' 열의 값이 교환되었습니다.", level="INFO", also_to_report=True, separator="none")
        
        return dataframe
    
    except Exception as e:
        raise ValueError(f"열 값 교환 중 문제가 발생했습니다: {e}")
    

def adjust_column_by_percentage(dataframe, column_name, percentage, operation):
    """
    지정된 열의 모든 숫자 값을 비율에 따라 증가 또는 감소시키는 함수.
    문자열로 된 숫자 값이 포함된 경우, 이를 숫자로 변환하여 처리.

    :param dataframe: pandas DataFrame
    :param column_name: 값을 조정할 열의 이름
    :param percentage: 조정할 비율 (10은 10%를 의미)
    :param operation: "increase" 또는 "decrease" 중 하나를 입력하여 값을 증가 또는 감소
    :return: 수정된 DataFrame
    :raises ValueError: 열이 없거나 operation 값이 잘못된 경우 예외 발생
    """
    try:
        # 열이 데이터프레임에 존재하는지 확인
        if column_name not in dataframe.columns:
            raise ValueError(f"'{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        # 열의 데이터가 숫자 또는 문자열로 된 숫자인지 확인
        def convert_to_numeric(value):
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"'{column_name}' 열에 숫자가 아닌 값이 포함되어 있습니다: {value}")

        dataframe[column_name] = dataframe[column_name].apply(convert_to_numeric)

        # 조정 비율을 계산 (10%는 0.1로 변환)
        adjustment_factor = percentage / 100

        # 증가 또는 감소 작업 수행
        if operation == "인상":
            dataframe[column_name] = (dataframe[column_name] * (1 + adjustment_factor)).astype(int)
        elif operation == "인하":
            dataframe[column_name] = (dataframe[column_name] * (1 - adjustment_factor)).astype(int)
        else:
            raise ValueError("operation 값은 '인상' 또는 '인하'만 가능합니다.")

        # 마지막 자릿수를 0으로 변경
        dataframe[column_name] = (dataframe[column_name] // 10) * 10

        # 작업 성공 메시지 출력
        logger.log(f"✅ '{column_name}' 열의 값이 {percentage}% {operation} 되었습니다.", level="INFO", also_to_report=True, separator="none")
        return dataframe

    except Exception as e:
        print(f"❌ 작업 중 오류 발생: {e}")
        raise SystemExit(f"프로그램 종료: {e}")



def update_column_to_9999(dataframe: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    특정 열의 모든 값을 숫자 9999로 변경하는 함수.

    :param dataframe: pandas DataFrame
    :param column_name: 값을 변경할 열 이름
    :return: 값이 변경된 DataFrame
    """
    try:
        # 열 이름 존재 여부 확인
        if column_name not in dataframe.columns:
            raise ValueError(f"'{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        # 열 값을 9999로 변경
        dataframe[column_name] = 9999

        # 변경 완료 로그 출력
        logger.log(f"✅ '{column_name}' 열의 모든 값이 9999로 변경되었습니다.", level="INFO", also_to_report=True, separator="none")

        return dataframe

    except Exception as e:
        raise ValueError(f"'{column_name}' 열의 값을 9999로 변경하는 중 문제가 발생했습니다: {e}")

def add_prefix_to_column(dataframe, column_name, prefix, suffix=None):
    """
    특정 열의 값에 접두사(prefix)와 접미사(suffix)를 추가하는 함수.
    소수점 문제를 해결하고, 접두사와 접미사 사이에 '_'를 자동으로 추가.

    :param dataframe: 데이터프레임
    :param column_name: 값을 수정할 열 이름
    :param prefix: 추가할 접두사
    :param suffix: 추가할 접미사 (기본값: None)
    :return: 수정된 데이터프레임
    """
    try:
        if column_name not in dataframe.columns:
            raise ValueError(f"데이터프레임에 '{column_name}' 열이 존재하지 않습니다.")
        
        # 초기 데이터 수 로깅
        row_count = len(dataframe)
        # logger.log(f"✅ '{column_name}' 열의 접두사 '{prefix}' 추가 작업 시작 (총 {row_count}행).", level="INFO", also_to_report=True, separator="none")
        
        # 열 값 변환
        def transform_value(value):
            # 소수점 문제 해결 (값이 float인 경우 정수로 변환 가능)
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            # None 또는 NaN은 변환하지 않음
            if pd.isna(value):
                return value
            # 접두사와 접미사 추가
            if suffix:
                return f"{prefix}_{value}_{suffix}"
            else:
                return f"{prefix}_{value}"
        
        dataframe[column_name] = dataframe[column_name].apply(transform_value)
        
        logger.log(f"✅ '{column_name}' 열의 접두사 {row_count}개 열의 접두사 '{prefix}' 추가완료.", level="INFO", also_to_report=True, separator="none")
        return dataframe
    except Exception as e:
        raise ValueError(f"'{column_name}' 열의 데이터를 수정하는 중 문제가 발생했습니다: {e}")



def clear_column_data(dataframe, column_name):
    """
    특정 열의 데이터를 모두 삭제(해당 열을 NaN으로 설정)하는 함수.
    
    :param dataframe: 데이터프레임
    :param column_name: 데이터를 삭제할 열 이름
    :return: 수정된 데이터프레임
    """
    try:
        if column_name not in dataframe.columns:
            raise ValueError(f"데이터프레임에 '{column_name}' 열이 존재하지 않습니다.")
        
        # 초기 데이터 수 로깅
        row_count = len(dataframe)
        logger.log(f"✅ '{column_name}' 열의 데이터 삭제 작업 시작 (총 {row_count}행).", level="INFO")
        
        # 열 데이터 삭제 (NaN으로 설정)
        dataframe[column_name] = None  # 또는 dataframe[column_name] = pd.NA
        
        logger.log(f"✅ '{column_name}' 열의 데이터가 모두 삭제되었습니다.", level="INFO", also_to_report=True, separator="dash-1line")
        return dataframe
    except Exception as e:
        raise ValueError(f"'{column_name}' 열의 데이터를 삭제하는 중 문제가 발생했습니다: {e}")
    
def clear_image_columns(dataframe, columns):
    """
    지정된 이미지 열의 모든 내용을 지우는 함수.
    
    :param dataframe: pandas DataFrame (작업 대상)
    :param columns: 리스트 (지울 열 이름 리스트)
    :return: (수정된 데이터프레임, 변경된 행 수)
    """
    try:
        # 변경 전 카운트 (비어있지 않은 값의 개수)
        initial_count = dataframe[columns].notna().sum().sum()
        
        # 값 제거
        dataframe[columns] = ""
        
        # 변경된 행 수
        modified_rows = initial_count
        
        logger.log(f"🔄 지정된 열 {columns}의 모든 값이 삭제되었습니다. 총 {modified_rows}개 셀이 수정되었습니다.", level="INFO")
        
        return dataframe, modified_rows
    
    except Exception as e:
        raise ValueError(f"🚨 '{columns}' 열의 내용을 지우는 중 오류 발생: {e}")


def remove_empty_rows(dataframe, column_name):
    """
    특정 열이 비어있는 행을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[dataframe[column_name].notna()]  # 비어있지 않은 행 필터링
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"✅ {column_name} 열에서 {removed_count}개의 비어있는 행 삭제", level="INFO", also_to_report=True, separator="none")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"✅ {column_name} 열에서 비어있는 행을 삭제하는 중 문제가 발생했습니다: {e}")
    

def input_ship_column(dataframe, column_name, input_value):
    """
    멀티 인덱스 컬럼에서 특정 열에 지정된 값을 입력하는 함수 (문자열 또는 숫자 가능)

    :param dataframe: DataFrame (멀티 인덱스 컬럼 포함 가능)
    :param column_name: 기준 열 이름 (첫 번째 레벨 기준)
    :param input_value: 입력할 값 (문자열 또는 숫자)
    :return: 수정된 데이터프레임
    """
    try:
        # 멀티 인덱스 처리: 첫 번째 레벨에서 column_name 선택
        if isinstance(dataframe.columns, pd.MultiIndex):
            if column_name in dataframe.columns.get_level_values(0):
                dataframe.loc[:, pd.IndexSlice[column_name, :]] = input_value
            else:
                raise KeyError(f"'{column_name}' 컬럼을 찾을 수 없습니다.")
        else:
            if column_name in dataframe.columns:
                dataframe[column_name] = input_value
            else:
                raise KeyError(f"'{column_name}' 컬럼을 찾을 수 없습니다.")

        logger.log(f"'{column_name}' 열에 '{input_value}' 값이 입력되었습니다.", level="INFO", also_to_report=True, separator="none")


        # 고정으로 값을 입력할 8개 컬럼과 값 매핑
        fixed_values = {
            "배송 안내 입력선택": "selection",
            "배송 안내": "002001",
            "AS 안내 입력선택": "selection",
            "AS 안내": "003001",
            "환불 안내 입력선택": "selection",
            "환불 안내": "004001",
            "교환 안내 입력선택": "selection",
            "교환 안내": "005001",
        }

        # 기존 코드 적용
        fixed_ship_sheet = input_fixed_values(dataframe, fixed_values)

        return fixed_ship_sheet

    except Exception as e:
        raise ValueError(f"'{column_name}' 열에 값 입력 중 문제가 발생했습니다: {e}")
    


def input_fixed_values(dataframe, column_value_dict):
    """
    멀티 인덱스 컬럼에서 특정 열들에 대해 고정된 값을 입력하는 함수.
    : 배송관련 입력값 

    :param dataframe: DataFrame (멀티 인덱스 컬럼 포함 가능)
    :param column_value_dict: {컬럼명: 입력값} 형태의 딕셔너리
    :return: 수정된 데이터프레임
    """
    try:
        # 멀티 인덱스 컬럼 처리
        if isinstance(dataframe.columns, pd.MultiIndex):
            for column_name, input_value in column_value_dict.items():
                if column_name in dataframe.columns.get_level_values(0):
                    dataframe.loc[:, pd.IndexSlice[column_name, :]] = input_value
                else:
                    logger.log(f"'{column_name}' 컬럼을 찾을 수 없습니다.", level="WARNING")
        else:
            # 단일 인덱스 컬럼 처리
            for column_name, input_value in column_value_dict.items():
                if column_name in dataframe.columns:
                    dataframe[column_name] = input_value
                else:
                    logger.log(f"'{column_name}' 컬럼을 찾을 수 없습니다.", level="WARNING")

        logger.log(f"배송관련 열 {len(column_value_dict)}개 컬럼에 고정값 입력 완료.", level="INFO", also_to_report=True, separator="none")

        return dataframe

    except Exception as e:
        raise ValueError(f"여러 컬럼에 값 입력 중 문제가 발생했습니다: {e}")

    
  




from config.settings import FOOD_CATEGORIES_NUMBERS
def remove_food_category_rows(dataframe, column_name):
    """
    카테고리 번호가 음식 카테고리인 행을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[~dataframe[column_name].isin(FOOD_CATEGORIES_NUMBERS)]  # 음식 카테고리를 제외
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 음식 카테고리 {removed_count}개의 행이 삭제되었습니다.", level="INFO", also_to_report=True, separator="none")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 음식 카테고리 행을 삭제하는 중 문제가 발생했습니다: {e}")
    

from config.settings import ADULT_CATEGORIES_NUMBERS
def remove_adult_category_rows(dataframe, column_name):
    """
    카테고리 번호가 19금(성인) 카테고리인 행을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[~dataframe[column_name].isin(ADULT_CATEGORIES_NUMBERS)]  # 19금 카테고리를 제외
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 19금 카테고리 {removed_count}개의 행이 삭제되었습니다.", level="INFO", also_to_report=True, separator="none")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 19금 카테고리 행을 삭제하는 중 문제가 발생했습니다: {e}")
    

def filter_product_name(dataframe, product_name_column, filter_keywords):
    """
    상품명 기준으로 행을 필터링하는 함수
    :param dataframe: 데이터프레임
    :param product_name_column: 상품명 열 이름
    :param filter_keywords: 필터링할 키워드 리스트
    :return: 필터링된 데이터프레임, 삭제된 행 수
    """
    try:
        # 상품명 키워드 필터링 (단어 경계를 사용하여 독립적인 단어만 필터링)
        initial_count = len(dataframe)
        keyword_pattern = '|'.join(f"\\b{word}\\b" for word in filter_keywords)
        dataframe = dataframe[~dataframe[product_name_column].str.contains(keyword_pattern, case=False, na=False)]
        after_keyword_filter_count = len(dataframe)
        keyword_removed_count = initial_count - after_keyword_filter_count

        logger.log(f"✅ {product_name_column} 열에서 {keyword_removed_count}개의 금지 키워드 행이 삭제완료.", level="INFO", also_to_report=True, separator="none")

        return dataframe, keyword_removed_count
    except Exception as e:
        raise ValueError(f"데이터프레임 필터링 중 문제가 발생했습니다: {e}")
    
import pandas as pd

import pandas as pd

import re

def filter_forbid_product(dataframe, product_name_column, product_code_column, filter_keywords, filter_code_keywords):
    """
    상품명 및 상품코드 기준으로 행을 필터링하는 함수 (각각의 키워드 리스트 적용)
    
    :param dataframe: 데이터프레임
    :param product_name_column: 상품명 열 이름
    :param product_code_column: 상품코드 열 이름
    :param filter_keywords: 상품명을 필터링할 키워드 리스트
    :param filter_code_keywords: 상품코드를 필터링할 키워드 리스트
    :return: 필터링된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)

        # 문자열 타입 변환 (필수)
        dataframe[product_name_column] = dataframe[product_name_column].astype(str)
        dataframe[product_code_column] = dataframe[product_code_column].astype(str)

        # 예외처리할 단어 리스트 (오탐 방지)
        exception_keywords = ["칼라", "칼리그래피", "칼슘", "오일 페이퍼"]  # 오탐 방지 단어들 추가 가능

        # 필터링 키워드에서 오탐 방지 단어 제외
        refined_filter_keywords = [kw for kw in filter_keywords if kw not in exception_keywords]

        # 필터링 패턴 생성 (정확한 단어만 필터링하도록 개선)
        name_pattern = r"\b(" + "|".join(map(re.escape, refined_filter_keywords)) + r")\b" if refined_filter_keywords else None
        code_pattern = r"\b(" + "|".join(map(re.escape, filter_code_keywords)) + r")\b" if filter_code_keywords else None

        # 상품명 필터링 적용
        mask_name = dataframe[product_name_column].str.contains(name_pattern, case=False, na=False) if name_pattern else False
        # 상품코드 필터링 적용
        mask_code = dataframe[product_code_column].str.contains(code_pattern, case=False, na=False) if code_pattern else False

        # 삭제할 행 저장
        filtered_out_rows = dataframe[mask_name | mask_code]

        # 상품명 또는 상품코드에서 하나라도 키워드가 포함되면 삭제
        filtered_dataframe = dataframe[~(mask_name | mask_code)]

        removed_count = initial_count - len(filtered_dataframe)

        # 삭제된 상품명 및 상품코드 리스트 생성
        removed_product_names = ', '.join(filtered_out_rows[product_name_column].astype(str).tolist())
        removed_product_codes = ', '.join(filtered_out_rows[product_code_column].astype(str).tolist())

        logger.log(f"✅ {product_name_column}({len(filter_keywords)}개 키워드), {product_code_column}({len(filter_code_keywords)}개 키워드)에서 {removed_count}개의 금지 행 삭제 완료.",
                   level="INFO", also_to_report=True, separator="none")

        if removed_count > 0:
            logger.log(f"🗑 삭제된 상품명: {removed_product_names}", level="INFO", also_to_report=True, separator="none")
            logger.log(f"🗑 삭제된 상품코드: {removed_product_codes}", level="INFO", also_to_report=True, separator="none")

        return filtered_dataframe, removed_count
    except Exception as e:
        raise ValueError(f"데이터프레임 필터링 중 문제가 발생했습니다: {e}")




    
import pandas as pd

import pandas as pd

def filter_product_code(dataframe, product_code, filter_keywords):
    """
    상품 코드 기준으로 행을 필터링하는 함수 (제거된 키워드도 로그 출력)
    :param dataframe: 데이터프레임
    :param product_code: 필터링할 상품 코드 열 이름
    :param filter_keywords: 필터링할 키워드 리스트 (숫자 포함 가능)
    :return: 필터링된 데이터프레임, 삭제된 행 수, 삭제된 키워드 목록
    """
    try:
        # 1️⃣ 🔹 필터링 키워드를 모두 문자열(str)로 변환
        filter_keywords = [str(keyword) for keyword in filter_keywords]

        # 2️⃣ 🔹 product_code 컬럼이 숫자(int/float 등)라면 문자열(str)로 변환
        if not pd.api.types.is_string_dtype(dataframe[product_code]):
            dataframe[product_code] = dataframe[product_code].astype(str)

        # 3️⃣ 🔹 필터링할 키워드 패턴 생성 (단어 경계 사용)
        keyword_pattern = '|'.join(f"\\b{word}\\b" for word in filter_keywords)

        # 4️⃣ 🔹 필터링 전에 원본 데이터 개수 저장
        initial_count = len(dataframe)

        # 5️⃣ 🔹 필터링된 행 추출 (제거될 상품 코드 리스트 생성)
        removed_rows = dataframe[dataframe[product_code].str.contains(keyword_pattern, case=False, na=False)]
        removed_keywords = removed_rows[product_code].tolist()

        # 6️⃣ 🔹 필터링 수행 (제거)
        dataframe = dataframe[~dataframe[product_code].str.contains(keyword_pattern, case=False, na=False)]
        after_keyword_filter_count = len(dataframe)
        keyword_removed_count = initial_count - after_keyword_filter_count

        # ✅ 로그 출력
        logger.log(f"✅ {product_code} 열에서 {keyword_removed_count}개의 금지 코드 상품이 삭제됨", level="INFO", also_to_report=True, separator="none")

        # 🔍 **필터링된 키워드 로그 출력**
        if removed_keywords:
            logger.log(f"🚫 필터링된 상품 코드 목록: {removed_keywords}", level="INFO", also_to_report=True, separator="none")

        return dataframe, keyword_removed_count
    except Exception as e:
        raise ValueError(f"데이터프레임 필터링 중 문제가 발생했습니다: {e}")








def convert_http_to_https(dataframe, columns):
    """
    지정된 열의 URL에서 'http://'를 'https://'로 변환하는 함수.
    
    :param dataframe: pandas DataFrame (작업 대상)
    :param columns: 리스트 (수정할 열 이름 리스트)
    :return: (수정된 데이터프레임, 변경된 행 수)
    """
    try:
        initial_count = (dataframe[columns].apply(lambda col: col.str.startswith("http://"), axis=0)).sum().sum()  # 변경 전 http:// 개수
        
        dataframe[columns] = dataframe[columns].apply(
            lambda col: col.map(lambda x: x.replace("http://", "https://") if isinstance(x, str) and x.startswith("http://") else x)
        )

        
        updated_count = (dataframe[columns].apply(lambda col: col.str.startswith("http://"), axis=0)).sum().sum()  # 변경 후 남아있는 http:// 개수
        modified_rows = initial_count - updated_count  # 실제 변경된 행 수
        
        logger.log(f"🔄 이미지열들 에서 {modified_rows}개의 'http://' URL을 'https://'로 변경", level="INFO", also_to_report=True, separator="none")
        
        return dataframe, modified_rows
    
    except Exception as e:
        raise ValueError(f"🚨 'http://'을 'https://'로 변환하는 중 오류 발생: {e}")
    
def replace_base_url(dataframe, columns, old_base_url, new_base_url):
    """
    지정된 열의 URL에서 특정 base URL을 새로운 base URL로 변경하는 함수.
    
    :param dataframe: pandas DataFrame (작업 대상)
    :param columns: 리스트 (수정할 열 이름 리스트)
    :param old_base_url: 문자열 (기존 base URL)
    :param new_base_url: 문자열 (새로운 base URL)
    :return: (수정된 데이터프레임, 변경된 행 수)
    """
    try:
        initial_count = (dataframe[columns].apply(lambda col: col.str.startswith(old_base_url), axis=0)).sum().sum()  # 변경 전 개수
        
        dataframe[columns] = dataframe[columns].apply(
            lambda col: col.map(lambda x: x.replace(old_base_url, new_base_url) if isinstance(x, str) and x.startswith(old_base_url) else x)
        )
        
        updated_count = (dataframe[columns].apply(lambda col: col.str.startswith(old_base_url), axis=0)).sum().sum()  # 변경 후 남아있는 개수
        modified_rows = initial_count - updated_count  # 실제 변경된 행 수
        
        logger.log(f"🔄 이미지열들 에서 {modified_rows}개의 URL base를 '{old_base_url}'에서 '{new_base_url}'로 변경", level="INFO", also_to_report=True, separator="none")
        
        return dataframe, modified_rows
    
    except Exception as e:
        raise ValueError(f"🚨 URL base를 변경하는 중 오류 발생: {e}")



def convert_column_str(dataframe, column_name, new_str):
    """
    지정된 열의 문자열을 새로운 문자열로 변경하는 함수.
    
    :param dataframe: pandas DataFrame (작업 대상)
    :param column_name: str (수정할 열 이름)
    :param new_str: str (새로운 문자열)
    :return: (수정된 데이터프레임, 변경된 행 수)
    """
    try:
        # 변경 전 카운트 (수정 대상 열의 전체 행 수)
        initial_count = len(dataframe[column_name])
        
        # 문자열 치환
        dataframe[column_name] = new_str
        
        # 변경된 행 수
        modified_rows = initial_count
        
        logger.log(f"🔄 '{column_name}' 열의 모든 값이 '{new_str}'로 변경되었습니다. 총 {modified_rows}개 행이 수정되었습니다.", level="INFO")
        
        return dataframe, modified_rows
    
    except Exception as e:
        raise ValueError(f"🚨 '{column_name}' 열을 '{new_str}'로 변경하는 중 오류 발생: {e}")




def remove_duplicate_rows(dataframe, column_name, keep_type="remove_all"):
    """
    특정 열에서 중복된 항목을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :param keep_type: 중복 처리 유형 ('keep_one' - 중복중 하나 남김, 'remove_all' - 모두 삭제)
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수

        # 공백(NaN 또는 빈 문자열)인 행 필터링
        dataframe = dataframe[dataframe[column_name].notna() & (dataframe[column_name] != "")]

        if keep_type == "keep_one":
            # 하나를 남기고 중복 제거
            dataframe = dataframe.drop_duplicates(subset=[column_name])
        elif keep_type == "remove_all":
            # 중복된 항목 모두 삭제
            duplicate_mask = dataframe[column_name].duplicated(keep=False)
            dataframe = dataframe[~duplicate_mask]
        else:
            raise ValueError(f"Invalid keep_type: {keep_type}. Use 'keep_one' or 'remove_all'.")

        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"✅ <{column_name}> 열에서 중복된 {removed_count}개의 행이 삭제완료 (처리 방식: {keep_type})", level="INFO", also_to_report=True, separator="none")

        return dataframe, removed_count

    except Exception as e:
        raise ValueError(f"{column_name} 열에서 중복된 행을 삭제하는 중 문제가 발생했습니다: {e}")

def remove_options_rows(dataframe, column_name):
    """
    '선택사항 타입' 열에서 옵션이 있는행은 제거 
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[dataframe[column_name].isna()]  # 비어있는 행 필터링
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 옵션이 있는 {removed_count}개의 행이 삭제되었습니다.", level="DEBUG", also_to_report=True, separator="none")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 비어있지 않은 행을 삭제하는 중 문제가 발생했습니다: {e}")

def clean_search_keywords(dataframe, column_name):
    """
    검색어 열에서 중복 키워드 제거, 숫자/특수문자 제거, 문자열 길이 조정을 수행하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 변경된 데이터 수
    """
    try:
        import re

        def clean_keywords(keywords):
            # 중복 제거, 숫자 및 특수문자 제거
            if pd.isna(keywords):
                return ""
            # 숫자/특수문자 제거 및 쉼표로 나누기
            cleaned_keywords = re.sub(r'[^가-힣a-zA-Z,]', '', keywords).split(',')
            # 중복 제거 및 키워드 길이 제한 적용 (10자 이상인 키워드 제외)
            filtered_keywords = [kw for kw in dict.fromkeys(cleaned_keywords) if len(kw) <= 15]
            return ','.join(filtered_keywords)


        # 초기 상태 복사
        original_keywords = dataframe[column_name].copy()

        # 데이터 정리 작업 수행
        dataframe[column_name] = dataframe[column_name].apply(clean_keywords)

        # 변경된 데이터 수 계산
        changed_count = int((original_keywords != dataframe[column_name]).sum())

        logger.log(f"{column_name}열의 검색어가 정리되었습니다. 변경된 데이터 수: {changed_count}", level="DEBUG", also_to_report=True, separator="none")
        return dataframe, changed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열의 검색어를 정리하는 중 문제가 발생했습니다: {e}")

def update_column_value(dataframe, column_name, value):
    """
    특정 열의 값을 일괄 변경하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :param value: 변경할 값
    :return: 수정된 데이터프레임, 변경된 데이터 수
    """
    try:
        # 초기 상태 복사
        original_column = dataframe[column_name].copy()

        # 데이터 타입 강제 변환
        dataframe[column_name] = dataframe[column_name].astype(type(value))

        # 열 값을 일괄 변경
        dataframe[column_name] = value

        # 변경된 데이터 수 계산 (타입 차이 허용)
        changed_count = int((original_column != dataframe[column_name]).sum())

        # 디버깅 로그 추가
        # logger.log(f"변경 전 데이터 타입: {original_column.dtype}", level="DEBUG")
        # logger.log(f"변경 후 데이터 타입: {dataframe[column_name].dtype}", level="DEBUG")
        # logger.log(f"변경 전 데이터: {original_column.unique()}", level="DEBUG")
        # logger.log(f"변경 후 데이터: {dataframe[column_name].unique()}", level="DEBUG")

        if changed_count > 0:
            logger.log(f"{column_name} 열의 값이 모두 '{value}'로 변경되었습니다. 변경된 데이터 수: {changed_count}", level="INFO", also_to_report=True, separator="none")
        else:
            logger.log(f"{column_name} 열의 값은 이미 '{value}'로 설정되어 있습니다. 변경된 데이터가 없습니다.", level="INFO", also_to_report=True, separator="none")

        return dataframe, changed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열의 값을 변경하는 중 문제가 발생했습니다: {e}")
