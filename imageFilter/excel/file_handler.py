import os
import xlrd
from xlutils.copy import copy

# 엑셀 파일을 읽는 함수
def read_excel_file(file_path, file_name, file_extension):
    """
    엑셀 파일을 읽고 수정 가능한 형태로 반환하는 함수.
    
    Parameters:
    - file_path (str): 엑셀 파일이 있는 경로
    - file_name (str): 엑셀 파일 이름
    - file_extension (str): 엑셀 파일의 확장자 (.xls만 지원)
    
    Returns:
    - tuple: (엑셀 sheet, 복사된 writable_book, writable_sheet)
      - sheet: 읽기 전용으로 열려 있는 엑셀의 첫 번째 시트를 나타내는 객체, 데이터를 읽기 위해 사용
      - writable_book: 기존 엑셀 파일을 복사하여 수정 가능한 형태로 만든 workbook 객체. 
                       데이터를 변경하거나 저장하기 위해 사용
      - writable_sheet: writable_book 내의 첫 번째 시트를 나타내는 객체. 
                        이 시트를 통해 셀 데이터를 수정하거나 추가할 수 있음.

    """
    excel_file_path = os.path.join(file_path, f"{file_name}{file_extension}")
    
    if file_extension == '.xls':
        try:
            # .xls 파일 열기 (xlrd 사용)
            book = xlrd.open_workbook(excel_file_path, formatting_info=True)
            sheet = book.sheet_by_index(0)
            # 복사본 생성 (writable 형태로)
            writable_book = copy(book)
            writable_sheet = writable_book.get_sheet(0)
            return sheet, writable_book, writable_sheet
        except Exception as e:
            print(f"엑셀 파일을 여는 중 오류 발생: {e}")
            return None, None, None
    else:
        print("지원되지 않는 파일 형식입니다.")
        return None, None, None

# 엑셀 파일을 저장하는 함수
def save_excel_file(writable_book, output_file_path):
    """
    엑셀 파일을 저장하는 함수.
    
    Parameters:
    - writable_book: 저장할 복사된 엑셀 book 객체
    - output_file_path (str): 결과를 저장할 경로
    """
    try:
        # 변경된 내용을 저장
        writable_book.save(output_file_path)
        print(f"[디버그] 필터링 결과가 순환파일로 저장되었습니다.")
        print(f"[디버그] 파일경로 : {output_file_path}")

    except Exception as e:
        # 저장 중 오류 발생 시 출력
        print(f"파일 저장 중 오류 발생: {e}")
