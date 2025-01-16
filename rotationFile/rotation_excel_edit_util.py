from utils.global_logger import logger

import pandas as pd

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
            unique_keywords = list(dict.fromkeys(re.sub(r'[^가-힣a-zA-Z,]', '', keywords).split(',')))
            # 문자열 길이 조정
            return ','.join(unique_keywords)[:29]

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
