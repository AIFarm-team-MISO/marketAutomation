from utils.global_logger import logger

import pandas as pd


def validate_data_order(data: list, sheet: pd.DataFrame, title: str) -> None:
    """
    데이터의 순서를 검증하는 함수.

    :param data: 가공된 리스트 데이터.
    :param sheet: 원본 데이터프레임.
    :param title: 데이터의 제목(로그용).
    :raises ValueError: 순서 검증 실패 시 예외 발생.
    """
    try:
        # 원본 데이터프레임의 인덱스 가져오기
        sheet_index = sheet.index.tolist()
        # 비교 대상 인덱스 생성
        data_index = list(range(len(data)))

        logger.log(f"✅ data_index: {data_index}", level="INFO",also_to_report=True, separator="none")
        logger.log(f"✅ sheet_index: {sheet_index}", level="INFO",also_to_report=True, separator="none")
        
        # 데이터 순서 검증
        if data_index != sheet_index:
            logger.log(
                f"❌ {title}: 데이터 순서가 원본 데이터와 일치하지 않습니다.",
                level="ERROR",also_to_report=True, separator="none")
            
            logger.log(
                f"원본 인덱스: {sheet_index}\n현재 데이터 인덱스: {data_index}",
                level="DEBUG",also_to_report=True, separator="none")
            
            raise ValueError(
                f"{title}: 데이터 순서가 일치하지 않습니다. "
                f"원본 인덱스: {sheet_index}, 현재 데이터 인덱스: {data_index}" ,also_to_report=True, separator="none")
        
        # 검증 성공
        logger.log(
            f"✅ {title}: 데이터 순서 검증 완료. {len(data)}개의 항목.",
            level="INFO",also_to_report=True, separator="none")
        
        # logger.log(f"✅ 원본 인덱스: {sheet_index}, 현재 데이터 인덱스: {data_index}",level="INFO")

    except ValueError as e:
        logger.log(str(e), level="ERROR")
        raise