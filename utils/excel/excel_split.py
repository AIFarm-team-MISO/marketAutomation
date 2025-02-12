from utils.global_logger import logger

import pandas as pd
import os
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, read_and_clean_first_sheet, read_xlsx_all_sheets
from utils.excel.excel_utils import save_excel_with_sheets
from config.settings import FILE_EXTENSION_xlsx

def save_split_excel_files(first_sheet_data, sheets, file_path, base_file_name, rows_per_file, first_sheet_name):
    """
    분할된 엑셀 데이터를 저장하고 무결성을 검증하는 함수.

    :param first_sheet_data: 첫 번째 시트 데이터 (DataFrame)
    :param sheets: 모든 시트 데이터
    :param file_path: 원본 파일 경로
    :param base_file_name: 생성할 파일의 기본 이름
    :param rows_per_file: 한 파일에 포함될 행의 수
    :param first_sheet_name: 첫 번째 시트 이름
    """

    total_rows = first_sheet_data.shape[0]
    split_rows = 0

    for i in range(0, total_rows, rows_per_file):
        # 슬라이스하여 부분 데이터프레임 생성
        part_df = first_sheet_data.iloc[i:i + rows_per_file]
        split_rows += part_df.shape[0]

        # 파일 이름 생성
        output_file_path = make_output_file_path(file_path, f"{base_file_name}_part_{i // rows_per_file + 1}", "_split_output", FILE_EXTENSION_xlsx)
        output_file_name = os.path.basename(output_file_path)

        # 모든 시트 저장
        save_excel_with_sheets(sheets, output_file_path, part_df, first_sheet_name)

        # 정렬 검증 및 출력
        if '원본번호*' in part_df.columns:
            min_id = part_df['원본번호*'].min()
            max_id = part_df['원본번호*'].max()

            logger.log(f"파일명 : {output_file_name}, '원본번호*': {min_id}번 ~ {max_id}번, 총갯수: {part_df.shape[0]}", also_to_report=True, separator="2line")

    # 필수 검증: 총 행 수 확인
    assert total_rows == split_rows, "총행갯수 무결성 실패!"
    logger.log(f"무결성 체크 : 총행갯수 {total_rows}행 분할 완료.", also_to_report=True, separator="2line")


def split_excel_by_rows(file_path, base_file_name, task_type="single", sheets=None, modify_data=None, first_sheet_name=None):
    """
    엑셀 파일의 행을 지정한 크기로 나누어 각 파일을 생성합니다.

    :param file_path: 원본 엑셀 파일 경로
    :param base_file_name: 생성할 파일의 기본 이름
    """

    rows_per_file = 1500

    try:
        if sheets is None: # 단독실행일경우 

            excel_file_path = make_input_file_path(file_path, base_file_name)
            # output_file_name = make_output_file_path(file_path, base_file_name, "_image_filtered_output", FILE_EXTENSION_xlsx)
            _, file_extension = os.path.splitext(base_file_name)


            # 모든 시트 읽기(파일확장명에 따라)
            if file_extension.lower() == ".xlsx":
                sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
            elif file_extension.lower() == ".xls":
                sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
            else:
                raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")

            # 첫 번째 시트를 읽고 비어 있는 행 제거
            first_sheet_name, first_sheet_data = read_and_clean_first_sheet(sheets)

        else: # 시트가 제공된 경우, 첫 번째 시트 및 정제처리가 필요없음 : 자동화실행일 경우
            logger.log(f"시트가 존재하여 순환가공된 파일 기준으로 분할시작!")
            sheets = sheets
            first_sheet_name = first_sheet_name
            first_sheet_data = modify_data

        

        # 원본번호 기준으로 번호정렬 및 데이터 타입 변환
        first_sheet_data = first_sheet_data.copy()
        first_sheet_data['원본번호*'] = first_sheet_data['원본번호*'].astype(int)  # 정수형으로 변환
        first_sheet_data = first_sheet_data.sort_values(by='원본번호*', ascending=True)
        
        logger.log_separator()
        logger.log(f"{base_file_name}를 원본번호* 기준으로 정렬완료! {rows_per_file}행씩 분할합니다.")

        # 분할된 파일 저장
        save_split_excel_files(first_sheet_data, sheets, file_path, base_file_name, rows_per_file, first_sheet_name)
        logger.log_separator()


    except Exception as e:
        logger.log(f"Error occurred: {e}")
