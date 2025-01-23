from utils.global_logger import logger

from utils.validate.validate_index import validate_data_order
import pandas as pd


def get_column_values_with_validation(sheet: pd.DataFrame, column_name: str) -> list:
    """
    특정 열에서 데이터를 가져오고 유효성을 체크하며, 문제가 발생하면 프로그램을 종료.
    :param sheet: 데이터프레임
    :param column_name: 가져올 열 이름
    :return: 열 데이터 리스트
    :raises SystemExit: 열이 없거나 NaN 값이 포함된 경우 프로그램 종료
    """
    try:
        # 열(column_name)이 존재하는지 확인
        if column_name not in sheet.columns:
            logger.log(f"❌ '{column_name}' 열이 데이터프레임에 존재하지 않습니다.", level="ERROR")
            raise SystemExit(f"프로그램 종료: '{column_name}' 열이 존재하지 않습니다.")
        
        # 열 데이터를 가져옴
        column_values = sheet[column_name].tolist()

        # 데이터가 비어 있는지 확인
        if not column_values:
            logger.log(f"❌ '{column_name}' 열에 데이터가 비어 있습니다.", level="ERROR")
            raise SystemExit(f"프로그램 종료: '{column_name}' 열에 데이터가 비어 있습니다.")
        
        # NaN 값 포함 여부 확인
        if any(pd.isna(value) for value in column_values):
            nan_indices = [index for index, value in enumerate(column_values) if pd.isna(value)]
            logger.log(
                f"❌ '{column_name}' 열에 NaN 값이 포함되어 있습니다. NaN 값 인덱스: {nan_indices}",
                level="ERROR"
            )
            raise SystemExit(f"프로그램 종료: '{column_name}' 열에 NaN 값이 포함되어 있습니다.")
        
        # 데이터 순서 검증
        validate_data_order(column_values, sheet, f"'{column_name}' 열")
        
        logger.log(f"✅ '{column_name}' 열에서 {len(column_values)}개의 데이터를 성공적으로 가져왔습니다.", level="INFO")
        return column_values
    except SystemExit as e:
        logger.log(str(e), level="CRITICAL")
        raise
    except Exception as e:
        logger.log(f"❌ '{column_name}' 열 데이터 처리 중 예외 발생: {e}", level="ERROR")
        raise SystemExit(f"프로그램 종료: '{column_name}' 열 데이터 처리 중 문제가 발생했습니다.")


def get_folder_name(sheet_data, column_name="폴더명"):
    """
    시트 데이터에서 지정된 열(column_name)의 첫 번째 값에서 '_'로 구분된 첫 번째 부분을 추출합니다.
    폴더명이 없는 경우 속행합니다.

    Parameters:
        sheet_data (pd.DataFrame): 작업 대상 데이터프레임.
        column_name (str): 폴더명이 포함된 열 이름 (기본값: '폴더명').

    Returns:
        str: '_'로 구분된 첫 번째 부분의 값 (없을 경우 빈 문자열 반환).
    """
    try:
        # 지정된 열(column_name)이 존재하는지 확인
        if column_name not in sheet_data.columns:
            logger.log(f"⚠️ 열 '{column_name}'이(가) 데이터프레임에 존재하지 않습니다. 속행합니다.", level="WARNING")
            return ""

        # 첫 번째 값 가져오기
        folder_name = sheet_data[column_name].iloc[0] if not sheet_data.empty else ""

        # 값이 NaN인 경우 처리
        if pd.isna(folder_name):
            logger.log(f"⚠️ 폴더명이 비어 있습니다. 속행합니다.", level="WARNING")
            return ""

        # '_'로 나누어 첫 번째 부분 추출
        split_parts = folder_name.split("_")
        if split_parts:
            extracted_folder_name = split_parts[0].strip()  # 첫 번째 부분 추출 후 공백 제거
            # logger.log(f"추출된 폴더명: {extracted_folder_name}", level="INFO")
            
            return folder_name, extracted_folder_name
        else:
            logger.log(f"⚠️ 폴더명 '{folder_name}'에서 '_'로 구분된 부분을 찾을 수 없습니다. 속행합니다.", level="WARNING")
            return ""

    except Exception as e:
        logger.log(f"폴더명을 가져오는 중 에러 발생: {e}", level="ERROR")
        return ""
    
def get_market_name(folder_name: str) -> str:
    """
    대괄호([])를 제거하고, '-' 앞의 부분(마켓 이름)을 추출하는 함수.

    :param folder_name: 처리할 폴더 이름 (예: "[쿠팡-블루채널]")
    :return: 추출된 마켓 이름 (예: "쿠팡")
    """
    try:
        # 대괄호 제거
        cleaned_name = folder_name.strip("[]")
        
        # '-'로 분리하여 앞부분 추출
        market_name = cleaned_name.split("-")[0]
        
        return market_name.strip()  # 앞뒤 공백 제거 후 반환
    except Exception as e:
        raise ValueError(f"폴더 이름 처리 중 에러 발생: {e}")
    
def split_market_name(folder_name):
    """
    폴더명을 '-'로 나누어 각각 리스트에 담아 반환하며, 대괄호([ ])와 같은 특수문자를 제거합니다.

    Parameters:
        folder_name (str): 분리할 폴더명 문자열.

    Returns:
        list: '-'로 나누어진 모든 부분을 담은 리스트 (없으면 빈 리스트 반환).
    """
    try:
        if not folder_name:
            logger.log(f"⚠️ 폴더명이 비어 있습니다.", level="WARNING")
            return []

        # 특수문자 제거 및 '-'로 나누기
        cleaned_folder_name = folder_name.replace("[", "").replace("]", "").strip()
        parts = [part.strip() for part in cleaned_folder_name.split("-") if part.strip()]
        if parts:
            logger.log(f"폴더명 분리: '{folder_name}' -> Parts: {parts}", level="INFO")
            return parts
        else:
            logger.log(f"⚠️ 폴더명을 '-'로 나눌 수 없습니다: '{folder_name}'", level="WARNING")
            return []

    except Exception as e:
        logger.log(f"폴더명을 분리하는 중 에러 발생: {e}", level="ERROR")
        return []