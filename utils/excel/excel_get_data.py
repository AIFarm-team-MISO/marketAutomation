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