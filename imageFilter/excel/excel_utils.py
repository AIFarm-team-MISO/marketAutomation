from openpyxl import load_workbook
import win32com.client as win32
import psutil
import xlrd
from xlutils.copy import copy

import win32com.client as win32
from config.settings import YELLOW_COLOR_RGB  # 예시: (255, 255, 0)와 같은 RGB 값으로 설정 필요


import os
from config.settings import FILE_EXTENSION

from openpyxl.styles import PatternFill
import win32com.client
import pythoncom


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
                print(f"엑셀 파일 닫힘: {wb.FullName}")

    except Exception as e:
        # 엑셀 파일 닫기 중 오류 발생 시 오류 메시지 출력
        print(f"엑셀 파일 닫기 중 오류 발생: {e}")

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
        if file_name.endswith(FILE_EXTENSION):
            base_file_name = os.path.splitext(file_name)[0]

            # output 파일 경로 설정
            output_file_path = os.path.join(file_path, f"{base_file_name}_output{FILE_EXTENSION}")

            # 기존 output 파일이 있으면 삭제
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                    print(f"기존 output 파일 삭제 완료: {output_file_path}")
                except PermissionError:
                    # 파일이 사용 중인 경우 엑셀 인스턴스를 닫고 다시 시도
                    print(f"파일이 열려있어 삭제할 수 없습니다. 엑셀 파일을 닫습니다: {output_file_path}")
                    close_open_excel_files(output_file_path)
                    try:
                        os.remove(output_file_path)
                        print(f"다시 시도 후 삭제 완료: {output_file_path}")
                    except Exception as e:
                        print(f"output 파일 삭제 중 오류 발생: {e}")
                        continue  # 삭제 실패 시 파일 리스트에 추가하지 않음

            # 파일 리스트에 추가
            file_list.append((file_path, base_file_name))

    return file_list


def insert_column_before(sheet, writable_sheet, column_index):
    """
    엑셀 시트에서 특정 열 앞에 새로운 열을 삽입하고, 첫 번째 행에 열 이름을 추가하는 함수.
    
    Parameters:
    - sheet: 읽기 전용 엑셀 시트 객체 (xlrd로 읽어들인 시트)
    - writable_sheet: 쓰기 가능한 엑셀 시트 객체 (xlutils.copy로 생성된 객체)
    - column_index (int): 새로운 열을 삽입할 위치 (1부터 시작, 예: 12는 12번째 열 앞에 열을 삽입)
    
    작업 순서:
    1. 기존 데이터를 오른쪽으로 이동하여 새로운 열을 삽입.
    2. 새로 삽입된 열의 데이터를 비어있는 값으로 초기화.
    3. 첫 번째 행(열 제목)에 "필터링결과"라는 값을 추가.
    """
    # 모든 행에 대해, 기존 데이터를 오른쪽으로 이동하여 새로운 열 삽입
    for row_idx in range(1, sheet.nrows + 1):
        # 현재 행의 데이터를 가져옴
        current_row_data = [sheet.cell_value(row_idx - 1, col_idx) for col_idx in range(sheet.ncols)]
        # 새 열 삽입 후 기존 데이터를 오른쪽으로 이동
        for col_idx in range(column_index, sheet.ncols):
            writable_sheet.write(row_idx - 1, col_idx + 1, current_row_data[col_idx])
    
    # 새로 삽입한 열에 대한 초기값 설정
    for row_idx in range(1, sheet.nrows + 1):
        writable_sheet.write(row_idx - 1, column_index, '')
    
    # 첫 번째 행(헤더)에 "필터링결과"라는 열 제목 추가
    writable_sheet.write(0, column_index, "필터링결과")

def apply_filter_and_sort_xls(output_file_path, sort_column, sort_direction='descending', sort_on='values'):
    """
    엑셀 파일을 열고, 특정 열을 기준으로 필터링을 적용하고 정렬하는 함수.
    문자있음을 위로 정렬하고 색상을 노란색으로 설정 
    이후 순환파일에서 문자있음만을 삭제하기 위해서. 
    
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

        # 2행에 필터 적용 (A2부터 마지막 열까지)
        last_column = sheet.UsedRange.Columns.Count  # 데이터가 포함된 마지막 열 찾기
        sheet.Range(f"A2:{sheet.Cells(2, last_column).Address}").AutoFilter()  # 필터 적용 범위 설정

        # 엑셀 내부 상수 정의 (정렬 방향, 정렬 기준 등)
        xlSortOnValues = 0  # 값 기준 정렬
        xlSortOnCellColor = 1  # 색상 기준 정렬
        xlDescending = 2  # 내림차순 정렬 상수
        xlAscending = 1  # 오름차순 정렬 상수
        xlYes = 1  # 헤더 포함 상수
        xlTopToBottom = 1  # 위에서 아래로 정렬

        # 정렬 방향 설정
        if sort_direction == 'descending':
            order = xlDescending
        else:
            order = xlAscending

        # 정렬 기준 설정 (값 또는 색상)
        if sort_on == 'color':
            sort_on_value = xlSortOnCellColor
        else:
            sort_on_value = xlSortOnValues

        # 전체 데이터 범위 설정 (A3부터 마지막 열까지)
        last_row = sheet.UsedRange.Rows.Count  # 데이터가 포함된 마지막 행 찾기
        sort_range = sheet.Range(f"A3:{sheet.Cells(last_row, last_column).Address}")  # 정렬할 범위 설정

        # 정렬 필드 초기화 후 새 필드 추가
        sheet.Sort.SortFields.Clear()
        sheet.Sort.SortFields.Add(
            Key=sheet.Range(f"{sort_column}3:{sort_column}{last_row}"),  # 정렬할 열만 기준으로 지정
            SortOn=sort_on_value,  # 정렬 기준 (값 또는 색상)
            Order=order,  # 정렬 방향 설정
            DataOption=0  # 기본 정렬 옵션
        )

        # 전체 범위를 기준으로 정렬 수행
        sheet.Sort.SetRange(sort_range)
        sheet.Sort.Header = xlYes  # 첫 번째 행을 헤더로 설정
        sheet.Sort.MatchCase = False  # 대소문자 구분하지 않음
        sheet.Sort.Orientation = xlTopToBottom  # 위에서 아래로 정렬
        sheet.Sort.Apply()  # 정렬 적용

        # 정렬이 완료되었다는 메시지 출력
        print(f"\n[디버그] 순환파일이 문자있음 우선으로 정렬 및 색상적용 완료\n")


        # << 추가된 부분: 노란색을 적용할 행 선택 및 색상 적용 >>
        yellow_excel_color = rgb_to_excel_color(YELLOW_COLOR_RGB)  # RGB 값을 Excel VBA 색상 코드로 변환

        for row in range(3, last_row + 1):  # 3행부터 마지막 행까지 반복
            cell_value = sheet.Cells(row, 13).Value  # 13번째 열에서 '중복-문자있음' 확인
            if cell_value == "중복-문자있음":  # 원하는 조건 확인
                sheet.Rows(row).Interior.Color = yellow_excel_color  # 행 전체에 변환된 색상 적용

        # 정렬된 파일 저장
        workbook.Save()
    except Exception as e:
        # 오류 발생 시 메시지 출력
        print(f"파일 처리 중 오류 발생: {e}")
    finally:
        # 엑셀 파일을 닫고, 엑셀 프로세스 종료
        workbook.Close(False)
        excel.Quit()

        # COM 객체 사용 종료 (자원 해제)
        pythoncom.CoUninitialize()

        clean_up_excel_process()

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