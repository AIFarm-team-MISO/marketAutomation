import os
import xlrd
import xlwt

def process_add_prefix_to_excel_in_folder_with_sheets(folder_path, column_letter, prefix):
    """
    현재 폴더에 있는 모든 .xls 파일을 대상으로 특정 열의 값에 접두사를 추가하며,
    기존 파일의 모든 탭 이름을 유지. 추가로 비어있는 D 열의 행 삭제 및 G 열 값을 9999로 변경.

    Parameters:
    - folder_path (str): 엑셀 파일들이 위치한 폴더 경로.
    - column_letter (str): 접두사를 추가할 열의 열 문자 (예: 'B').
    - prefix (str): 추가할 접두사 문자열.

    Returns:
    - list: 생성된 결과 파일 경로 목록.
    """
    try:
        # 1. 현재 폴더 내의 모든 .xls 파일 가져오기
        xls_files = [f for f in os.listdir(folder_path) if f.endswith(".xls")]
        if not xls_files:
            raise FileNotFoundError("현재 폴더에 .xls 파일이 존재하지 않습니다.")

        output_files = []

        for file_name in xls_files:
            input_file_path = os.path.join(folder_path, file_name)
            base_name, ext = os.path.splitext(file_name)
            output_file_path = os.path.join(folder_path, f"{base_name}_processed{ext}")

            # 2. 기존 .xls 파일 열기
            workbook = xlrd.open_workbook(input_file_path, formatting_info=True)
            writable_book = xlwt.Workbook()

            # 3. 각 시트 복사 및 수정
            for sheet_idx in range(workbook.nsheets):
                sheet = workbook.sheet_by_index(sheet_idx)
                writable_sheet = writable_book.add_sheet(sheet.name)

                # 열 문자 → 열 인덱스 변환
                column_index = column_letter_to_index(column_letter)
                column_d_index = column_letter_to_index('D')
                column_g_index = column_letter_to_index('G')

                new_row_idx = 0  # 새로 작성할 행의 인덱스

                for row_idx in range(sheet.nrows):
                    # D 열 값 체크를 3번째 행부터 시작
                    if row_idx >= 2:  # 3번째 행부터
                        cell_value_d = sheet.cell_value(row_idx, column_d_index)
                        if not cell_value_d:  # D 열 값이 비어 있으면 행 건너뜀
                            continue

                    for col_idx in range(sheet.ncols):
                        cell_value = sheet.cell_value(row_idx, col_idx)

                        # B 열의 값에 접두사 추가
                        if col_idx == column_index and row_idx > 0:  # 헤더 제외
                            if isinstance(cell_value, float):  # 소수점 있는 숫자 처리
                                cell_value = str(int(cell_value))
                            cell_value = f"{prefix}{cell_value}" if cell_value else cell_value

                        # G 열 값을 9999로 변경
                        if col_idx == column_g_index and row_idx > 0:  # 헤더 제외
                            cell_value = 9999

                        writable_sheet.write(new_row_idx, col_idx, cell_value)

                    new_row_idx += 1

            # 4. 결과 저장
            writable_book.save(output_file_path)
            print(f"파일 '{file_name}'에 접두사 추가 및 수정 작업이 완료되었습니다: {output_file_path}")
            output_files.append(output_file_path)

        return output_files

    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def column_letter_to_index(letter):
    """
    열 문자를 열 인덱스로 변환 (예: 'A' → 0, 'B' → 1).
    """
    return ord(letter.upper()) - ord('A')
