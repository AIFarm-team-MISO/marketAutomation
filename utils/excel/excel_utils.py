from utils.global_logger import logger

import os
import win32com.client as win32
import psutil
import pandas as pd
import win32com.client
import pythoncom
from config.settings import FILE_EXTENSION_xls
import pyexcel as pe


def save_excel_with_sheets(sheets, output_file_name, modified_df=None, modified_sheet_name=None):
    """
    수정된 시트를 포함하여 모든 시트를 저장하는 함수.
    특정 시트만 수정 가능하며, 두 번째 행에 빈 줄을 추가합니다.

    Parameters:
        sheets (dict): 시트 이름을 키로, DataFrame을 값으로 갖는 딕셔너리.
                      모든 시트의 데이터를 포함.
        output_file_name (str): 저장할 출력 파일 경로. 저장될 파일의 전체 경로.
        modified_df (pd.DataFrame, optional): 수정된 DataFrame. 기본값은 None.
                                              수정된 시트 데이터를 포함.
        modified_sheet_name (str, optional): 수정된 시트 이름. 기본값은 None.
                                             수정 대상 시트 이름.

    Returns:
        None
    """
    try:
        # 출력 파일 이름이 지정되지 않은 경우 예외 처리
        if output_file_name is None:
            raise ValueError("출력 파일 이름이 지정되지 않았습니다.")

        logger.log_separator()
        # logger.log("엑셀 저장 작업을 시작합니다.", level="INFO")

        # 수정된 시트를 반영
        if modified_df is not None:
            if modified_sheet_name is None:
                # 수정된 시트 이름이 지정되지 않은 경우 첫 번째 시트를 사용
                modified_sheet_name = list(sheets.keys())[0]
            # logger.log(f"수정된 첫번째 시트 {modified_sheet_name} 에 반영", level="INFO")
            # 수정된 시트를 sheets 딕셔너리에 반영
            sheets[modified_sheet_name] = modified_df

        # 엑셀 파일 저장
        with pd.ExcelWriter(output_file_name, engine="openpyxl") as writer:
            # 모든 시트를 순회
            for sheet_name, sheet_df in sheets.items():
                # 1. 두 번째 행에 빈 줄을 추가
                #    - 빈 DataFrame 생성: [[""] * len(sheet_df.columns)]
                #    - columns=sheet_df.columns: 원본 DataFrame의 열 이름 유지
                #    - pd.concat: 빈 행을 원본 데이터의 첫 번째 행 앞에 삽입
                sheet_df_with_empty_row = pd.concat(
                    [
                        sheet_df.iloc[:0],  # 기존 데이터의 첫 행 이전 부분
                        pd.DataFrame([[""] * len(sheet_df.columns)], columns=sheet_df.columns),  # 빈 행 추가
                        sheet_df  # 원본 데이터
                    ],
                    ignore_index=True  # 인덱스를 초기화하여 정렬
                )
                # 2. 처리된 DataFrame을 엑셀로 저장
                sheet_df_with_empty_row.to_excel(writer, sheet_name=sheet_name, index=False)

        file_name = os.path.basename(output_file_name)

        logger.log(f"변경된 파일 저장완료 : {file_name}", level="INFO", also_to_report=True, separator="2line")

    except Exception as e:
        # 예외 발생 시 에러 로그 출력
        logger.log(f"엑셀 저장 중 오류 발생: {e}", level="ERROR")
        raise

def save_excel_for_godo(sheets, output_file_name, modified_df=None, modified_sheet_name=None):
    """
    고도몰용 엑셀 파일을 저장하는 함수.
    멀티 인덱스 2행 구조를 수동으로 삽입하고, 2행 후에 1행을 비운 후 데이터 저장.
    """
    try:
        if output_file_name is None:
            raise ValueError("출력 파일 이름이 지정되지 않았습니다.")

        logger.log_separator()

        if modified_df is not None:
            if modified_sheet_name is None:
                modified_sheet_name = list(sheets.keys())[0]
            sheets[modified_sheet_name] = modified_df

        with pd.ExcelWriter(output_file_name, engine="openpyxl") as writer:
            for sheet_name, sheet_df in sheets.items():
                # 멀티 인덱스 컬럼 확인
                if isinstance(sheet_df.columns, pd.MultiIndex):
                    headers = sheet_df.columns
                    header_rows = [list(headers.get_level_values(0)), list(headers.get_level_values(1))]

                    # 2행 헤더 생성
                    header_df = pd.DataFrame([header_rows[0], header_rows[1]], columns=headers)

                    # 빈 행 생성
                    empty_row = pd.DataFrame([[""] * len(headers)], columns=headers)

                    # 데이터프레임 결합: 헤더 → 빈 행 → 데이터
                    sheet_df_with_empty_row = pd.concat([header_df, empty_row, sheet_df], ignore_index=True)

                    # 단일 컬럼으로 저장 (멀티 인덱스 → 단일화)
                    sheet_df_with_empty_row.columns = ['_'.join(str(c) for c in col) for col in headers]

                    # 엑셀 저장
                    sheet_df_with_empty_row.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                else:
                    # 단일 인덱스의 경우 기본 저장
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

        file_name = os.path.basename(output_file_name)

        logger.log(f"변경된 파일 저장 완료: {file_name}", level="INFO", also_to_report=True, separator="2line")

    except Exception as e:
        logger.log(f"엑셀 저장 중 오류 발생: {e}", level="ERROR")
        raise


# Pandas 경고 제거 옵션 추가
pd.set_option('future.no_silent_downcasting', True)

def save_excel_for_godo_as_xls_fixed(sheets, output_file_path, first_row_values, modified_df=None, modified_sheet_name=None):
    """
    고도몰용 엑셀 파일을 저장하는 함수.
    - 첫 번째 행은 `modified_df`의 컬럼명을 삽입
    - 두 번째 행은 `first_row_values`를 삽입
    - 세 번째 행을 빈 행으로 추가
    - 네 번째 행부터 실제 데이터 저장
    """
    try:
        if output_file_path is None:
            raise ValueError("출력 파일 이름이 지정되지 않았습니다.")

        logger.log_separator()

        if modified_df is not None:
            if modified_sheet_name is None:
                modified_sheet_name = list(sheets.keys())[0]
            sheets[modified_sheet_name] = modified_df

        # 모든 시트를 저장할 딕셔너리 생성
        book_dict = {}

        for sheet_name, sheet_df in sheets.items():
            # ✅ 1. 첫 번째 행: 기존 `modified_df`의 컬럼명 (리스트 변환)
            header_row = [list(sheet_df.columns)]  # 1행

            # ✅ 2. 두 번째 행: 보관된 `first_row_values`
            first_row_data = [first_row_values]  # 2행

            # ✅ 3. 세 번째 행: 빈 행 추가
            empty_row = [[""] * sheet_df.shape[1]]  # 3행

            # ✅ 4. NaN을 빈 문자열("")로 변환하여 정리
            sheet_df_cleaned = sheet_df.where(pd.notna(sheet_df), "").astype(str)

            # ✅ 5. 최종 데이터 구성 (1행: 컬럼명 → 2행: 원본 첫 행 → 3행: 빈 행 → 4행부터 데이터)
            final_data = header_row + first_row_data + empty_row + sheet_df_cleaned.values.tolist()

            # ✅ 6. book_dict에 추가 (엑셀 저장용 데이터)
            book_dict[sheet_name] = final_data

        # ✅ .xls 파일로 저장
        pe.save_book_as(bookdict=book_dict, dest_file_name=output_file_path)

        file_name = os.path.basename(output_file_path)
        logger.log(f"✅ 변경된 파일 저장 완료 (Excel 97-2003 형식, pyexcel 사용): {file_name}", level="INFO", also_to_report=True, separator="2line")

    except Exception as e:
        logger.log(f"❌ 엑셀 저장 중 오류 발생: {e}", level="ERROR")
        raise


















def read_and_clean_first_sheet(sheets):
    """
    첫 번째 시트를 읽어 반환
    쓰지 않는 2번째 행을 제거하여 반환

    :param sheets: 엑셀 시트 딕셔너리
    :return: 첫 번째 시트 이름과 정리된 데이터프레임
    """
    try:
        

        # 첫 번째 시트 가져오기
        first_sheet_name = list(sheets.keys())[0]
        first_sheet_data = sheets[first_sheet_name]

        # 2번째 행(인덱스 1) 삭제
        if len(first_sheet_data) > 1:  # 데이터가 2행 이상 있는 경우에만 삭제
            first_sheet_data.drop(index=0, inplace=True)  # 인덱스 1 행 삭제
            logger.log(f"첫 번째 시트 '{first_sheet_name}'에서 컬럼제외 1번째 행(인덱스 0) 삭제 완료.", level="INFO")
        else:
            logger.log(f"첫 번째 시트 '{first_sheet_name}'의 행 수가 2 미만으로, 삭제할 행이 없습니다.", level="WARNING")

        
        # 데이터중 비어있는 행 제거
        cleaned_data = first_sheet_data.dropna(how='all')  # 모든 열이 NaN인 행 제거
        logger.log(f"첫 번째 시트 '{first_sheet_name}'를 읽어오고 비어있는 2번행 제거완료 ", level="INFO")

        # 인덱스를 0부터 다시 설정
        cleaned_data.reset_index(drop=True, inplace=True)
        logger.log(f"첫번째 시트데이터 인덱스 정렬완료 : {cleaned_data.index}", level="DEBUG")

        return first_sheet_name, cleaned_data

    except Exception as e:
        logger.log(f"첫 번째 시트를 읽고 정리하는 중 에러 발생: {e}", level="ERROR")
        raise ValueError(f"첫 번째 시트를 읽고 정리하는 중 문제가 발생했습니다: {e}")

def set_dual_column_headers(df):
    """
    기존 컬럼명을 유지하면서 첫 번째 행을 서브 컬럼으로 설정하여 반환.
    """
    try:
        # 첫 행을 서브 컬럼으로 설정
        sub_headers = df.iloc[0].fillna('')

        # 첫 행 제거 (이제 컬럼으로 설정되었으므로 필요 없음)
        df = df[1:].copy()  # copy()로 슬라이스 경고 방지

        # 멀티 인덱스 컬럼 설정 (zip 사용으로 FutureWarning 방지)
        df.columns = pd.MultiIndex.from_tuples([(col, value) for col, value in zip(df.columns, sub_headers)])

        # 인덱스 리셋
        df.reset_index(drop=True, inplace=True)

        logger.log("멀티 인덱스 컬럼 설정 완료.", level="INFO")
        return df

    except Exception as e:
        logger.log(f"set_dual_column_headers 함수 실행 중 오류 발생: {e}", level="ERROR")
        raise


def remove_rows_gododata(sheets):
    """
    첫 번째 시트를 읽어 반환.
    첫 번째 행을 별도로 저장하고, NaN으로만 이루어진 행만 제거하여 반환.

    :param sheets: 엑셀 시트 딕셔너리
    :return: (첫 번째 시트 이름, 첫 번째 행 리스트, 정리된 데이터프레임)
    """
    try:
        # 첫 번째 시트 가져오기
        first_sheet_name = list(sheets.keys())[0]
        first_sheet_data = sheets[first_sheet_name]

        # ✅ 첫 번째 행을 별도로 저장
        first_row_values = first_sheet_data.iloc[0].tolist()

        # ✅ 첫 번째 행을 제거한 후 데이터프레임 유지
        df_without_first_row = first_sheet_data.iloc[1:].reset_index(drop=True)

        # 삭제 전 데이터 크기 출력
        initial_rows = df_without_first_row.shape[0]
        logger.log(f"삭제 전 데이터 크기: {initial_rows} 행", level="DEBUG")

        # ✅ NaN만 삭제 (특정 행 삭제 X)
        cleaned_data = df_without_first_row.dropna(how='all')

        # 삭제 후 데이터 크기 출력
        after_cleaning_rows = cleaned_data.shape[0]
        logger.log(f"NaN 행 제거 후 데이터 크기: {after_cleaning_rows} 행", level="DEBUG")

        logger.log(f"첫 번째 시트 '{first_sheet_name}'를 읽어오고 NaN 제거 완료.", level="INFO", also_to_report=True, separator="2line")

        # 인덱스 초기화
        cleaned_data.reset_index(drop=True, inplace=True)
        logger.log(f"첫 번째 시트 데이터 인덱스 정렬 완료: {cleaned_data.index}", level="DEBUG")

        return first_sheet_name, first_row_values, cleaned_data  # ✅ 첫 번째 행을 함께 반환

    except Exception as e:
        logger.log(f"첫 번째 시트를 읽고 정리하는 중 에러 발생: {e}", level="ERROR")
        raise ValueError(f"첫 번째 시트를 읽고 정리하는 중 문제가 발생했습니다: {e}")





def read_xls_all_sheets(file_path):
    """
    엑셀 파일의 모든 시트를 읽어와 시트 이름과 내용을 반환하는 함수.

    Parameters:
        file_path (str): 읽을 엑셀 파일 경로.

    Returns:
        dict: 시트 이름을 키로, DataFrame을 값으로 갖는 딕셔너리.

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 경우.
        Exception: 파일 읽기 중 발생한 기타 예외.
    """
    try:
        # 파일이 존재하는지 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 모든 시트 읽기
        sheets = pd.read_excel(file_path, sheet_name=None, engine="xlrd")
        # print(f"파일에서 읽은 시트: {list(sheets.keys())}")

        return sheets

    except Exception as e:
        logger.log(f"엑셀 파일 읽기 중 오류 발생: {e}")
        raise

import os
import pandas as pd

def read_xlsx_all_sheets(file_path):
    """
    .xlsx 파일의 모든 시트를 읽어와 시트 이름과 내용을 반환하는 함수.

    Parameters:
        file_path (str): 읽을 엑셀 파일 경로.

    Returns:
        dict: 시트 이름을 키로, DataFrame을 값으로 갖는 딕셔너리.

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 경우.
        Exception: 파일 읽기 중 발생한 기타 예외.
    """
    try:
        # 파일이 존재하는지 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 모든 시트 읽기 (openpyxl 엔진 사용)
        sheets = pd.read_excel(file_path, sheet_name=None, engine="openpyxl")

        print(f"[INFO] 파일에서 읽은 시트: {list(sheets.keys())}")

        return sheets

    except FileNotFoundError as fnf_error:
        print(f"[ERROR] {fnf_error}")
        raise
    except Exception as e:
        print(f"[ERROR] 엑셀 파일 읽기 중 오류 발생: {e}")
        raise


def make_output_file_path(file_path, base_file_name, suffix, file_extension):
    """
    입력받은 파일 경로, 파일 이름, 추가 문자, 확장자를 기반으로 출력 파일 경로를 생성.

    Parameters:
        file_path (str): 디렉토리 경로.
        base_file_name (str): 기본 파일 이름.
        suffix (str): 추가 문자 (예: '_rotate').
        file_extension (str): 파일 확장자 (예: '.xls', '.xlsx').

    Returns:
        str: 생성된 출력 파일 경로.

    Raises:
        ValueError: 입력값이 유효하지 않을 경우.
    """
    try:
        # 입력값 검증
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path가 유효한 문자열이 아닙니다.")
        
        if not base_file_name or not isinstance(base_file_name, str):
            raise ValueError("base_file_name이 유효한 문자열이 아닙니다.")

        if not file_extension.startswith("."):
            raise ValueError("file_extension은 '.'으로 시작해야 합니다.")

        if not suffix or not isinstance(suffix, str):
            raise ValueError("suffix가 유효한 문자열이 아닙니다.")

        # 출력 파일 이름 생성
        output_file_name = f"{base_file_name}{suffix}{file_extension}"

        # 전체 경로 생성
        output_file_path = os.path.join(file_path, output_file_name)

        return output_file_path

    except Exception as e:
        logger.log(f"엑셀 파일 읽기 중 오류 발생: {e}")
        raise

def make_input_file_path(file_path, file_name):
    """
    파일 경로, 파일 이름, 확장자를 받아 전체 파일 경로를 반환하는 함수.

    Parameters:
        file_path (str): 디렉토리 경로.
        file_name (str): 파일 이름.
        file_extension (str): 파일 확장자 (예: '.xls', '.xlsx').

    Returns:
        str: 전체 파일 경로.

    Raises:
        ValueError: 입력값이 유효하지 않을 경우.
        FileNotFoundError: 생성된 경로가 실제 파일과 일치하지 않을 경우.
    """
    try:
        # 입력값 검증
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path가 유효한 문자열이 아닙니다.")
        
        if not file_name or not isinstance(file_name, str):
            raise ValueError("file_name이 유효한 문자열이 아닙니다.")

        # 전체 경로 생성
        excel_file_path = os.path.join(file_path, f"{file_name}")

        # 경로 정리 및 디버깅 메시지 출력
        full_path = os.path.abspath(excel_file_path)
        # print(f"생성된 파일 경로: {full_path}")

        # 파일 존재 여부 확인 (필요 시 제거 가능)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {full_path}")

        return full_path

    except Exception as e:
        logger.log(f"엑셀 파일 읽기 중 오류 발생: {e}")
        raise


def close_open_excel_files(file_name):
    """
    열려 있는 엑셀 파일을 찾아 강제로 닫는 함수.
    특정 파일 이름을 포함하는 엑셀 파일을 모두 닫아 파일 삭제가 가능하도록 처리합니다.

    Parameters:
    - file_name (str): 닫아야 할 엑셀 파일의 경로 또는 이름
    """
    # COM 라이브러리 사용을 위한 초기화 (멀티스레드 환경에서 안전하게 사용하기 위함)
    pythoncom.CoInitialize()
    
    # Excel Application 객체를 생성하여 엑셀 인스턴스를 가져옴
    xl = win32com.client.Dispatch("Excel.Application")
    
    # 열려 있는 모든 워크북 목록을 가져옴
    workbooks = xl.Workbooks

    try:
        # 열려 있는 모든 워크북을 반복하면서 지정된 파일이 열려 있는지 확인
        for wb in workbooks:
            # 파일 이름이 워크북의 전체 경로에 포함되어 있으면 닫기
            if file_name in wb.FullName:
                # 변경사항 저장 없이 워크북 닫기
                wb.Close(SaveChanges=False)
                logger.log(f"엑셀 파일 닫힘: {wb.FullName}")

    except Exception as e:
        # 엑셀 파일 닫기 중 오류 발생 시 오류 메시지 출력
        logger.log(f"엑셀 파일 닫기 중 오류 발생: {e}")

    finally:
        # Excel Application 종료 (모든 워크북 닫기 후 엑셀 프로그램 자체 종료)
        xl.Quit()
        
        # COM 객체 사용 종료 (자원 해제)
        pythoncom.CoUninitialize()

def process_all_excel_files(file_path):
    """
    폴더 내의 모든 엑셀 파일을 반복하여 파일 리스트를 반환하는 함수.
    기존의 .output 파일이 있으면 삭제한 후, 파일 경로와 이름을 리스트로 반환.
    
    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    
    Returns:
    - file_list (list): 파일 경로와 파일 이름 리스트 반환
    """
    file_list = []  # 처리할 파일 리스트를 저장할 리스트

    for file_name in os.listdir(file_path):
        # _output이 포함된 파일은 건너뜀 (이미 처리된 파일)
        if '_output' in file_name:
            continue
        
        # 엑셀 파일 확장자에 맞는 파일만 처리
        if file_name.endswith(FILE_EXTENSION_xls):
            base_file_name = os.path.splitext(file_name)[0]

            # output 파일 경로 설정
            output_file_path = os.path.join(file_path, f"{base_file_name}_output{FILE_EXTENSION_xls}")

            # 기존 output 파일이 있으면 삭제
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                    logger.log(f"기존 output 파일 삭제 완료: {output_file_path}")
                except PermissionError:
                    # 파일이 사용 중인 경우 엑셀 인스턴스를 닫고 다시 시도
                    logger.log(f"파일이 열려있어 삭제할 수 없습니다. 엑셀 파일을 닫습니다: {output_file_path}")
                    close_open_excel_files(output_file_path)
                    try:
                        os.remove(output_file_path)
                        logger.log(f"다시 시도 후 삭제 완료: {output_file_path}")
                    except Exception as e:
                        logger.log(f"output 파일 삭제 중 오류 발생: {e}")
                        continue  # 삭제 실패 시 파일 리스트에 추가하지 않음

            # 파일 리스트에 추가
            file_list.append((file_path, base_file_name))

    return file_list

def column_letter_to_index(column_letter):
    """
    엑셀 열 문자 ('A', 'B', ..., 'AA', ...)를 0부터 시작하는 열 인덱스로 변환
    
    Parameters:
    - column_letter (str): 열 문자 (예: 'A', 'M', 'AA')

    Returns:
    - int: 0부터 시작하는 열 인덱스 (예: 'A' -> 0, 'M' -> 12)
    """
    index = 0
    for char in column_letter:
        index = index * 26 + (ord(char.upper()) - ord('A')) + 1
    return index - 1  # 0부터 시작하도록 -1

def insert_column_before(sheet, writable_sheet, column, new_column_title):
    """
    엑셀 시트에서 특정 열 앞에 새로운 열을 삽입하고, 첫 번째 행에 열 이름을 추가하는 함수.
    
    Parameters:
    - sheet: 읽기 전용 엑셀 시트 객체 (xlrd로 읽어들인 시트)
    - writable_sheet: 쓰기 가능한 엑셀 시트 객체 (xlutils.copy로 생성된 객체)
    - column (int 또는 str): 열 위치 (숫자 인덱스 또는 문자열 열 이름, 예: 'M' 또는 12)
    - new_column_title (str): 새 열의 제목 (예: "필터링결과")
    """
    # column이 문자열이면 숫자 인덱스로 변환
    if isinstance(column, str):
        column_index = column_letter_to_index(column)
    else:
        column_index = column

    # 모든 행에 대해, 기존 데이터를 오른쪽으로 이동하여 새로운 열 삽입
    for row_idx in range(1, sheet.nrows + 1):
        current_row_data = [sheet.cell_value(row_idx - 1, col_idx) for col_idx in range(sheet.ncols)]
        for col_idx in range(column_index, sheet.ncols):
            writable_sheet.write(row_idx - 1, col_idx + 1, current_row_data[col_idx])
    
    # 새로 삽입한 열에 대한 초기값 설정
    for row_idx in range(1, sheet.nrows + 1):
        writable_sheet.write(row_idx - 1, column_index, '')
    
    # 첫 번째 행(헤더)에 새로운 열 제목 추가
    writable_sheet.write(0, column_index, new_column_title)

import win32com.client as win32
import pythoncom

def apply_filter_and_sort_xls(output_file_path, sort_column, sort_direction='descending', sort_on='values'):
    """
    엑셀 파일을 열고 특정 열을 기준으로 필터링을 적용하고 정렬한 후, 특정 조건에 따라 색상을 적용하는 함수.
    
    Parameters:
    - output_file_path (str): 정렬할 엑셀 파일 경로
    - sort_column (str): 정렬할 열 (예: 'M'은 M열을 기준으로 정렬)
    - sort_direction (str): 정렬 방향 ('ascending' 또는 'descending', 기본값: 'descending')
    - sort_on (str): 정렬 기준 ('values' 또는 'color', 기본값: 'values')
    """
    
    # COM 라이브러리 사용을 위한 초기화 (특히 멀티스레드 환경에서 안정적인 사용을 위해 필요)
    pythoncom.CoInitialize()

    try:
        # 엑셀 애플리케이션 실행
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False  # 엑셀 창을 숨긴 상태로 실행

        # 엑셀 파일 열기
        workbook = excel.Workbooks.Open(output_file_path)
        sheet = workbook.Sheets(1)  # 첫 번째 시트 선택

        # 데이터가 포함된 마지막 열을 찾기
        last_column = sheet.UsedRange.Columns.Count  # 예: 데이터의 마지막 열이 'G'열이라면 last_column은 7이 됨
        
        # 필터 적용 (2행부터 마지막 열까지 적용)
        # A2 셀부터 마지막 열까지 범위를 지정하여 필터를 활성화
        sheet.Range(f"A2:{sheet.Cells(2, last_column).Address}").AutoFilter()

        # 엑셀 내부 상수 정의 (정렬 방향, 정렬 기준 등)
        xlSortOnValues = 0  # 값 기준 정렬
        xlSortOnCellColor = 1  # 색상 기준 정렬
        xlDescending = 2  # 내림차순 정렬 상수
        xlAscending = 1  # 오름차순 정렬 상수
        xlYes = 1  # 첫 번째 행을 헤더로 간주
        xlTopToBottom = 1  # 위에서 아래로 정렬

        # 정렬 방향 설정: 기본은 내림차순이며, sort_direction에 따라 방향 변경
        order = xlDescending if sort_direction == 'descending' else xlAscending

        # 정렬 기준 설정: 기본은 값 기준이며, sort_on에 따라 색상 기준 설정 가능
        sort_on_value = xlSortOnCellColor if sort_on == 'color' else xlSortOnValues

        # 정렬할 범위 설정 (A2부터 마지막 행까지)
        # A2 셀부터 마지막 데이터 행과 열까지 범위를 지정해 정렬 대상 영역 설정
        last_row = sheet.UsedRange.Rows.Count  # 데이터가 포함된 마지막 행 찾기
        sort_range = sheet.Range(f"A2:{sheet.Cells(last_row, last_column).Address}")

        # 정렬 필드를 초기화한 후, 새 필드를 추가하여 정렬을 수행할 열과 조건을 설정
        sheet.Sort.SortFields.Clear()
        sheet.Sort.SortFields.Add(
            Key=sheet.Range(f"{sort_column}2:{sort_column}{last_row}"),  # sort_column 기준으로 정렬
            SortOn=sort_on_value,  # 값 또는 색상 기준
            Order=order,  # 정렬 방향 (오름차순 또는 내림차순)
            DataOption=0  # 기본 정렬 옵션
        )

        # 정렬 설정 적용
        sheet.Sort.SetRange(sort_range)  # 정렬 범위 설정
        sheet.Sort.Header = xlYes  # 첫 번째 행을 헤더로 설정
        sheet.Sort.MatchCase = False  # 대소문자 구분 안 함
        sheet.Sort.Orientation = xlTopToBottom  # 위에서 아래로 정렬
        sheet.Sort.Apply()  # 정렬 적용

        # 정렬 완료 후 메시지 출력
        print(f"\n[디버그] 순환파일이 문자있음 우선으로 정렬 및 색상적용 완료\n")

        # 노란색을 적용할 Excel VBA 색상 코드 (여기서는 노란색 65535로 설정)
        yellow_excel_color = 65535

        # 색상 적용 루프: 조건에 맞는 셀에만 색상을 적용
        for row in range(2, last_row + 1):  # 2행부터 마지막 행까지 반복
            cell_value = sheet.Cells(row, 13).Value  # 13번째 열의 값을 가져와 조건 확인
            if cell_value == "중복-문자있음":  # 특정 조건 만족 시
                sheet.Rows(row).Interior.Color = yellow_excel_color  # 행 전체를 노란색으로 설정

        # 정렬 및 색상 적용이 완료된 파일을 저장
        workbook.Save()

    except Exception as e:
        # 오류 발생 시 메시지 출력
        print(f"파일 처리 중 오류 발생: {e}")

    finally:
        # 엑셀 파일을 닫고, 엑셀 프로세스 종료
        workbook.Close(False)
        excel.Quit()
        pythoncom.CoUninitialize()

        # 기타 자원 해제 작업 (필요에 따라 추가)
        clean_up_excel_process()


import xlwt

def apply_row_color_by_condition(
    writable_sheet, target_column, final_optimized_naming_list, 
    color_name, condition_value=None
):
    """
    xlwt 기반의 시트에서 리스트에 따라 특정 열의 값에 대해 행 색상을 적용하는 함수.
    
    Parameters:
    - writable_sheet: xlwt의 수정 가능한 sheet 객체
    - target_column (int): 색상 적용할 열 인덱스 (예: 4 -> E열)
    - naming_list (list): 행의 개수와 셀 값 참조용으로 사용
    - color_name (str): 색상 이름 (예: 'yellow', 'red' 등) 
    - condition_value (str, optional): 특정 문자열 값 (없을 경우 모든 값이 있는 행에 색상 적용)
    """
    # 색상 이름을 사용해 xlwt 스타일 생성
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map.get(color_name, xlwt.Style.colour_map['yellow'])  # 기본값 노란색

    style = xlwt.XFStyle()
    style.pattern = pattern

    # 'filtered' 타입의 상품명 리스트 추출
    processed_naming_list = final_optimized_naming_list

    # 경고 메시지 출력 (모든 값이 있는 행에 색상을 적용할 때)
    if condition_value is None:
        logger.log("💾해당 열의 모든 값이 있는 행에 색상을 " + str(color_name)+ "색으로 적용!")
    
    # naming_list의 길이를 사용하여 각 행에 조건에 따라 색상 적용
    for row, cell_value in enumerate(processed_naming_list, start=2):  # 3행부터 시작
        if condition_value is None:
            # 모든 값이 있는 셀에 색상 적용
            if cell_value is not None and cell_value != "":
                writable_sheet.write(row, target_column, cell_value, style)
        else:
            # 특정 조건을 만족하는 셀에만 색상 적용
            if cell_value == condition_value:
                writable_sheet.write(row, target_column, cell_value, style)




def apply_filter_only_xls(output_file_path, sort_column, sort_direction='descending', sort_on='values'):
    """
    특정 열을 기준으로 필터링 및 정렬을 적용하는 함수 (색상 변경 없음).
    
    Parameters:
    - output_file_path (str): 정렬할 엑셀 파일 경로
    - sort_column (str): 정렬할 열 (예: 'M'은 M열을 기준으로 정렬)
    - sort_direction (str): 정렬 방향 ('ascending' 또는 'descending', 기본값: 'descending')
    - sort_on (str): 정렬 기준 ('values' 또는 'color', 기본값: 'values')
    """

    pythoncom.CoInitialize()
    try:
        # 엑셀 애플리케이션 실행
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False

        # 엑셀 파일 열기
        workbook = excel.Workbooks.Open(output_file_path)
        sheet = workbook.Sheets(1)

        # 필터 적용
        last_column = sheet.UsedRange.Columns.Count
        sheet.Range(f"A2:{sheet.Cells(2, last_column).Address}").AutoFilter()

        # 엑셀 상수 정의
        xlSortOnValues = 0
        xlSortOnCellColor = 1
        xlDescending = 2
        xlAscending = 1
        xlYes = 1
        xlTopToBottom = 1

        # 정렬 방향 설정
        order = xlDescending if sort_direction == 'descending' else xlAscending
        sort_on_value = xlSortOnCellColor if sort_on == 'color' else xlSortOnValues

        # 데이터 범위 설정
        last_row = sheet.UsedRange.Rows.Count
        sort_range = sheet.Range(f"A3:{sheet.Cells(last_row, last_column).Address}")

        # 정렬 필드 초기화 후 새 필드 추가
        sheet.Sort.SortFields.Clear()
        sheet.Sort.SortFields.Add(
            Key=sheet.Range(f"{sort_column}3:{sort_column}{last_row}"),
            SortOn=sort_on_value,
            Order=order,
            DataOption=0
        )

        # 정렬 수행
        sheet.Sort.SetRange(sort_range)
        sheet.Sort.Header = xlYes
        sheet.Sort.MatchCase = False
        sheet.Sort.Orientation = xlTopToBottom
        sheet.Sort.Apply()

        # 정렬된 파일을 저장
        workbook.Save()
        print("[디버그] 정렬 작업 완료")

    except Exception as e:
        print(f"정렬 작업 중 오류 발생: {e}")
    finally:
        workbook.Close(False)
        excel.Quit()
        pythoncom.CoUninitialize()

def update_seller_codes(dataframe: pd.DataFrame, column_name: str, prefix: str) -> pd.DataFrame:
    """
    데이터프레임에서 특정 열의 각 값에 접두사를 추가하는 함수.
    중복으로 접두사가 추가되지 않도록 방지.
    
    :param dataframe: 수정할 데이터프레임
    :param column_name: 접두사를 추가할 열의 이름
    :param prefix: 추가할 접두사 문자열
    :return: 수정된 데이터프레임
    """
    try:
        # 열이 데이터프레임에 존재하는지 확인
        if column_name not in dataframe.columns:
            raise ValueError(f"'{column_name}' 열이 데이터프레임에 존재하지 않습니다.")
        
        # 접두사 추가 (이미 접두사가 있는 경우 무시)
        dataframe[column_name] = dataframe[column_name].apply(
            lambda x: f"{prefix}-{x}" if pd.notnull(x) and not str(x).startswith(prefix) else x
        )
        
        # 로그 출력
        logger.log(f"✅ '{column_name}' 열에 접두사 '{prefix}' 추가 완료 (중복 방지).", level="INFO", also_to_report=True, separator="none")
        return dataframe
    except Exception as e:
        logger.log(f"❌ '{column_name}' 열에 접두사 추가 중 에러 발생: {e}", level="ERROR")
        raise


def update_seller_codes_xls(sheet, writable_sheet, number_column_index, ptype):
    """
    엑셀 시트의 특정 열(B열)의 판매자코드를 업데이트하는 함수.

    Parameters:
    - sheet: 읽기 전용으로 열려 있는 엑셀의 첫 번째 시트를 나타내는 객체 (xlrd)
    - writable_sheet: 수정 가능한 sheet 객체 (xlwt)
    - number_column_index (int): 판매자코드가 위치한 열 인덱스
    - ptype (str): 접두사로 추가할 문자열 (예: '상위판매자분석')

    Returns:
    - None
    """

    for row_idx in range(2, sheet.nrows):  # 3행부터 시작
        existing_seller_code = sheet.cell_value(row_idx, number_column_index)
        new_seller_code = f"{ptype}-{existing_seller_code}" if existing_seller_code else ptype

        # 디버깅 정보 출력
        logger.log(f"💾행번호: {row_idx + 1}, 기존코드: {existing_seller_code}, 새코드: {new_seller_code}")

        # 업데이트
        writable_sheet.write(row_idx, number_column_index, new_seller_code)

def delete_column(dataframe: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    데이터프레임에서 특정 열을 삭제하는 함수.
    
    :param dataframe: 수정할 데이터프레임
    :param column_name: 삭제할 열의 이름
    :return: 열이 삭제된 데이터프레임
    """
    try:
        # 열이 데이터프레임에 존재하는지 확인
        if column_name not in dataframe.columns:
            raise ValueError(f"'{column_name}' 열이 데이터프레임에 존재하지 않습니다.")
        
        # 열 삭제
        dataframe = dataframe.drop(columns=[column_name])
        
        # 로그 출력
        logger.log(f"✅ '{column_name}' 열이 성공적으로 삭제되었습니다.", level="INFO")
        return dataframe
    except Exception as e:
        logger.log(f"❌ '{column_name}' 열 삭제 중 에러 발생: {e}", level="ERROR")
        raise

def rename_and_delete_columns(dataframe: pd.DataFrame, target_column: str, new_column_name: str, delete_column: str) -> pd.DataFrame:
    """
    데이터프레임에서 특정 열의 이름을 변경하고 다른 열을 삭제하는 함수.
    
    :param dataframe: 수정할 데이터프레임
    :param target_column: 이름을 변경할 열의 이름
    :param new_column_name: 변경 후 열의 새 이름
    :param delete_column: 삭제할 열의 이름
    :return: 수정된 데이터프레임
    """
    try:
        # 열 존재 여부 확인
        if target_column not in dataframe.columns:
            raise ValueError(f"'{target_column}' 열이 데이터프레임에 존재하지 않습니다.")
        if delete_column not in dataframe.columns:
            raise ValueError(f"'{delete_column}' 열이 데이터프레임에 존재하지 않습니다.")
        
        # 삭제할 열 제거
        dataframe = dataframe.drop(columns=[delete_column])
        logger.log(f"✅ '{delete_column}' 열이 성공적으로 삭제되었습니다.", level="INFO")
        
        # 열 이름 변경
        dataframe = dataframe.rename(columns={target_column: new_column_name})
        logger.log(f"✅ '{target_column}' 열의 이름을 '{new_column_name}'으로 변경 완료.", level="INFO", also_to_report=True, separator="none")       
        
        return dataframe
    except Exception as e:
        logger.log(f"❌ 열 이름 변경 및 삭제 중 에러 발생: {e}", level="ERROR")
        raise
    
def rename_and_modify_columns(dataframe: pd.DataFrame, target_column: str, new_column_name: str, change_column_name: str) -> pd.DataFrame:
    """
    데이터프레임에서 특정 열의 이름을 변경하고 기존 새 열(new_column_name)의 이름을 다른 이름으로 변경하는 함수.
    
    :param dataframe: 수정할 데이터프레임
    :param target_column: 이름을 변경할 대상 열의 이름
    :param new_column_name: target_column을 변경할 새 이름
    :param change_column_name: new_column_name을 변경할 새 이름
    :return: 수정된 데이터프레임
    """
    try:
        # 열 존재 여부 확인
        if target_column not in dataframe.columns:
            raise ValueError(f"'{target_column}' 열이 데이터프레임에 존재하지 않습니다.")
        if new_column_name not in dataframe.columns:
            raise ValueError(f"'{new_column_name}' 열이 데이터프레임에 존재하지 않습니다.")



        # 열 이름 변경 (new_column_name -> change_column_name)
        dataframe = dataframe.rename(columns={new_column_name: change_column_name})
        logger.log(
            f"✅ '{new_column_name}' 열의 이름을 '{change_column_name}'으로 변경 완료.",
            level="INFO",
            also_to_report=True,
            separator="none"
        )
        
        # 열 이름 변경 (target_column -> new_column_name)
        dataframe = dataframe.rename(columns={target_column: new_column_name})
        logger.log(
            f"✅ '{target_column}' 열의 이름을 '{new_column_name}'으로 변경 완료.",
            level="INFO",
            also_to_report=True,
            separator="none"
        )

        return dataframe

    except Exception as e:
        logger.log(f"❌ 열 이름 변경 중 에러 발생: {e}", level="ERROR")
        raise


def clean_up_excel_process():
    """
    백그라운드에서 실행 중인 엑셀 프로세스를 종료하는 함수.
    
    작업 순서:
    1. 현재 실행 중인 프로세스 목록을 확인.
    2. 'excel.exe' 프로세스가 실행 중이면 이를 종료.
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 'EXCEL.EXE' 프로세스를 찾기
            if proc.info['name'].lower() == 'excel.exe':
                # 프로세스가 여전히 실행 중인지 확인
                if proc.is_running():
                    proc.kill()  # 프로세스 종료
                    print(f"[디버그] Excel 프로세스 종료됨 (pid={proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 프로세스가 이미 종료되었거나 접근 권한이 없는 경우 예외 처리
            continue


# RGB 값을 Excel 색상 코드로 변환하는 함수 추가
def rgb_to_excel_color(rgb):
    return rgb[0] + (rgb[1] * 256) + (rgb[2] * 256 * 256)