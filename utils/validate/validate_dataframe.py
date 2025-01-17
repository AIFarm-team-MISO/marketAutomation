
from utils.global_logger import logger
import pandas as pd


def validate_data_integrity(initial_count, filtered_sort_complete_sheets, processed_count, task_name, task_type="deletion"):
    """
    데이터 무결성을 검증하는 함수
    :param initial_count: 작업 전 데이터프레임의 행 수
    :param result_sheet_data: 작업 후 데이터프레임의 행 수
    :param processed_count: 처리된 데이터 수 (삭제/추가/변경)
    :param task_name: 작업 이름
    :param operation_type: 작업 유형 ('deletion', 'addition', 'modification')
    :return: None
    """
    # logger.log(f" - {task_name} 작업 - 무결성 검증시작", level="INFO")
    # logger.log(f"최초갯수 : {initial_count},  {task_type} 처리된 갯수 : {processed_count}, 처리후갯수 : {result_shee_count} ", level="INFO")

    # 반환값 검증
    if not isinstance(filtered_sort_complete_sheets, pd.DataFrame):
        raise ValueError(f"{task_name} 작업에서 반환된 데이터가 데이터프레임이 아닙니다.")
    if not isinstance(processed_count, int):
        raise ValueError(f"{task_name} 작업에서 반환된 처리된 데이터 수가 정수가 아닙니다.")

    # 무결성 검증
    result_shee_count = len(filtered_sort_complete_sheets)

    logger.log(f"작업 : {task_name} , 타입 :  {task_type} 검증.", also_to_report=True, separator="none")

    try:
        if task_type == "deletion":
            if initial_count - processed_count != result_shee_count:
                raise ValueError(
                    f"{task_name} 작업 중 삭제 무결성 오류 발생: "
                    f"초기 데이터({initial_count}), 삭제된 데이터({processed_count}), 남은 데이터({result_shee_count})"
                )
            logger.log(f"최초 데이터 수 : {initial_count}, 삭제된 데이터 수: {processed_count}, 남은 총데이터 수: {len(filtered_sort_complete_sheets)}", also_to_report=True, separator="none")
            logger.log(f"무결성 처리완료", level="INFO", also_to_report=True, separator="dnone")

        elif task_type == "addition":
            if initial_count + processed_count != result_shee_count:
                raise ValueError(
                    f"{task_name} 작업 중 추가 무결성 오류 발생: "
                    f"초기 데이터({initial_count}), 추가된 데이터({processed_count}), 최종 데이터({result_shee_count})"
                )
            logger.log(f"최초 데이터 수 : {initial_count}, 추가된 데이터 수: {processed_count}, 남은 총데이터 수: {len(filtered_sort_complete_sheets)}", also_to_report=True, separator="none")
            logger.log(f"무결성 처리완료", level="INFO", also_to_report=True, separator="none")

        elif task_type == "modification":
            if initial_count != result_shee_count:
                raise ValueError(
                    f"{task_name} 작업 중 변경 무결성 오류 발생: "
                    f"초기 데이터({initial_count}), 최종 데이터({result_shee_count})"
                )
            logger.log(f"최초 데이터 수 : {initial_count}, 변경된 데이터 수: {processed_count}, 남은 총데이터 수: {len(filtered_sort_complete_sheets)}", also_to_report=True, separator="none")
            logger.log(f"최초 데이터 수 : {initial_count}, 남은 총데이터 수: {len(filtered_sort_complete_sheets)} 가 동일해야함", level="INFO", also_to_report=True, separator="none")
            logger.log(f"무결성 처리완료", level="INFO", also_to_report=True, separator="dnone")

        else:
            raise ValueError(f"{task_name} 작업에서 알 수 없는 작업 유형: {task_type}")

    except Exception as e:
        raise ValueError(f"무결성 검증 중 오류 발생: {e}")
