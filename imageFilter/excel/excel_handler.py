import os
from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from imageFilter.excel.image_processing import process_image_urls
from imageFilter.excel.url_filter import save_filtered_urls
from imageFilter.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before
from config.settings import FILE_EXTENSION, FILTERED_URL_FILE
from openpyxl import load_workbook

import win32com.client as win32
import os
import time
import psutil  # 추가로 프로세스를 확인하기 위한 라이브러리


def process_excel_file(file_path, file_name):
    """

    1. 폴더에 있는 기존 파일을 복사해 내용을 수정하여 output 파일(순환파일) 을 생성함
    2. 기존에 이미지필터링을 통과했는지 확인하여 필터링 실행여부를 결정, 필터링 실행후 필터링 모음파일에 저장

    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    - file_name (str): 엑셀 파일 이름 (확장자 제외)
    - FILE_EXTENSION : 엑셀파일의 확장자 

    - tuple: (엑셀 sheet, 복사된 writable_book, writable_sheet)
      - sheet: 최초 폴더의 있는 엑셀의 첫 번째 시트를 나타내는 객체, 데이터를 읽기 위해 사용
      - writable_book: 기존 엑셀 파일을 복사하여 수정 가능한 형태로 만든 workbook 객체. 
                       데이터를 변경하거나 저장하기 위해 사용
      - writable_sheet: writable_book 내의 첫 번째 시트를 나타내는 객체. 
                        이 시트를 통해 셀 데이터를 수정하거나 추가할 수 있음.

    """ 

    sheet, writable_book, writable_sheet = read_excel_file(file_path, file_name, FILE_EXTENSION)
    if sheet is None:
        return

    image_column_index = 12       # '목록이미지' 열번호 (썸네일)
    seller_code_column_index = 1  # 판매자관리코드가 위치한 열 인덱스 (예: 1열)

    # 12열 앞에 새로운 열 삽입 (필터링의 결과를 작성하기 위해)
    insert_column_before(sheet, writable_sheet, 12)


    # 이미지 URL 처리 및 필터링된 URL 목록 획득 (기존 필터링된 URL 파일과 비교)
    # FILTERED_URL_FILE (str): 기존에 필터링된 URL 목록을 포함한 파일 경로
    data, filtered_urls, no_text_urls  = process_image_urls(sheet, image_column_index, seller_code_column_index, FILTERED_URL_FILE)
    

    # 데이터를 엑셀에 다시 쓰기
    for new_idx, (result, image_url) in enumerate(data):

        # 새로운 열에 필터링 상태 기록 ('목록이미지' 는 유지하고 그앞열 '필터링결과' 필터링상태를 기록 )
        writable_sheet.write(new_idx + 2, image_column_index, result)  # 필터링 상태 기록
        writable_sheet.write(new_idx + 2, image_column_index + 1, image_url)  # 기존 이미지 URL 유지

    # 결과 파일 저장 (output 파일(순환파일) 생성)
    output_file_path = os.path.join(file_path, f"{file_name}_output.xls")
    save_excel_file(writable_book, output_file_path)

    
    # 필터 및 정렬 적용 (.xls 파일에서 처리)
    # 예: M열을 내림차순으로 정렬
    apply_filter_and_sort_xls(output_file_path, sort_column="M", sort_direction="descending", sort_on="values")



    # 필터링된 URL '필터링url모음파일.xlsx' 에 저장
    save_filtered_urls(filtered_urls, no_text_urls)
