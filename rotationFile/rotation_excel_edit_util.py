from utils.global_logger import logger

import pandas as pd

def swap_image_column(dataframe: pd.DataFrame, column1: str, column2: str) -> pd.DataFrame:
    """
    두 열의 값을 교환하고, 두 열 중 하나라도 비어 있는 경우 해당 행을 삭제합니다.

    :param dataframe: 값을 교환할 데이터프레임
    :param column1: 첫 번째 열 이름
    :param column2: 두 번째 열 이름
    :return: 수정된 데이터프레임
    """
    try:
        # 열이 데이터프레임에 존재하는지 확인
        if column1 not in dataframe.columns or column2 not in dataframe.columns:
            raise ValueError(f"'{column1}' 또는 '{column2}' 열이 데이터프레임에 존재하지 않습니다.")

        # 두 열 중 하나라도 비어 있는 경우 해당 행 삭제
        initial_row_count = len(dataframe)
        dataframe = dataframe.dropna(subset=[column1, column2])
        removed_rows_count = initial_row_count - len(dataframe)

        if removed_rows_count > 0:
            print(f"⚠️ 두 열 중 하나라도 비어 있는 {removed_rows_count}개의 행이 삭제되었습니다.")

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
        
        logger.log(f"✅ '{column_name}' 열의 접두사 열의 접두사 '{prefix}' 추가완료.", level="INFO", also_to_report=True, separator="none")
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
        logger.log(f"{column_name} 열에서 {removed_count}개의 행 삭제", level="INFO")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 비어있는 행을 삭제하는 중 문제가 발생했습니다: {e}")

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
        logger.log(f"{column_name} 열에서 음식 카테고리 {removed_count}개의 행이 삭제되었습니다.", level="INFO")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 음식 카테고리 행을 삭제하는 중 문제가 발생했습니다: {e}")

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
        logger.log(f"<{column_name}> 열에서 중복된 {removed_count}개의 행이 삭제되었습니다. (처리 방식: {keep_type})", level="INFO")

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
        logger.log(f"{column_name} 열에서 옵션이 있는 {removed_count}개의 행이 삭제되었습니다.", level="DEBUG")

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

        logger.log(f"{column_name}열의 검색어가 정리되었습니다. 변경된 데이터 수: {changed_count}", level="DEBUG")
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
            logger.log(f"{column_name} 열의 값이 모두 '{value}'로 변경되었습니다. 변경된 데이터 수: {changed_count}", level="INFO")
        else:
            logger.log(f"{column_name} 열의 값은 이미 '{value}'로 설정되어 있습니다. 변경된 데이터가 없습니다.", level="INFO")

        return dataframe, changed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열의 값을 변경하는 중 문제가 발생했습니다: {e}")
