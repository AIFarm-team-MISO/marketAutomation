import os
import pandas as pd
from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from config.settings import FILE_EXTENSION_xls
from imageFilter.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before, column_letter_to_index, apply_row_color_by_condition
from imageFilter.excel.url_filter import save_filtered_urls

def process_namingChange_excel_file(file_path, file_name):
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

    sheet, writable_book, writable_sheet = read_excel_file(file_path, file_name, FILE_EXTENSION_xls)
    if sheet is None:
        return

    image_column_index = 'E'       # '상품명*' 열번호 (썸네일)
    image_column_index_int = column_letter_to_index(image_column_index)

    # '상품명*' 앞에 새로운 열 삽입 (필터링의 결과를 작성하기 위해)
    insert_column_before(sheet, writable_sheet, image_column_index, "가공결과")


    # URL 리스트 생성 (3행부터 시작)
    naming_list = [
        sheet.cell_value(idx, image_column_index_int) 
        for idx in range(2, sheet.nrows)  # 데이터가 3행부터 시작하므로 인덱스를 2부터 시작
        if pd.notna(sheet.cell_value(idx, image_column_index_int))
    ]
    
    print(f"[디버그]행갯수: {sheet.nrows}") 
    # print(f"[디버그] 문자 있음 필터링된 URL 목록 : {naming_list}")


    # 데이터를 엑셀에 다시 쓰기
    for new_idx, result in enumerate(naming_list):

        # 새로운 열에 필터링 상태 기록 ('목록이미지' 는 유지하고 그앞열 '필터링결과' 필터링상태를 기록 )
        writable_sheet.write(new_idx + 2, image_column_index_int, result)  # 필터링 상태 기록

    # << 추가된 부분: 노란색을 적용할 행 선택 및 색상 적용 >>
    apply_row_color_by_condition(writable_sheet, target_column=image_column_index_int, naming_list=naming_list, color_name='yellow')



    # 결과 파일 저장 (output 파일(순환파일) 생성)
    output_file_path = os.path.join(file_path, f"{file_name}_output.xls")
    save_excel_file(writable_book, output_file_path)