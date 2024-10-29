from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from config.settings import FILE_EXTENSION_xls
from imageFilter.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before

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

    # '상품명*' 앞에 새로운 열 삽입 (필터링의 결과를 작성하기 위해)
    insert_column_before(sheet, writable_sheet, image_column_index, "가공결과")