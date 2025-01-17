from utils.global_logger import logger
import os
import pandas as pd
import pythoncom
import win32com.client

from config.settings import FILE_EXTENSION_xls

def process_all_excel_files(folder_path):
    """
    폴더 내의 모든 엑셀 파일을 처리하고, 기존의 _output.xlsx 파일 삭제 후 파일 리스트 반환.
    
    Parameters:
    - folder_path (str): 엑셀 파일이 위치한 폴더 경로
    
    Returns:
    - list: 처리할 파일의 경로와 이름 리스트
    """
    file_list = []

    for file_name in os.listdir(folder_path):
        # _output 파일 처리
        if file_name.endswith("_output.xlsx"):
            output_file_path = os.path.join(folder_path, file_name)

            # 파일 닫기 및 삭제 시도
            if not safely_delete_file(output_file_path):
                logger.log(f"파일 삭제 실패: {output_file_path}", level="ERROR", also_to_report=True)
                continue
            else:
                # logger.log(f"_output 파일 삭제 완료: {output_file_path}", level="INFO", also_to_report=True)
                continue  # 삭제된 파일은 처리 제외

        # 다른 파일 처리 (조건: .xlsx 확장자)
        # if not file_name.endswith(FILE_EXTENSION_xls):
        #     logger.log(f"처리 제외 - 확장자가 .xls가 아님: {file_name}", level="INFO")
        #     continue

        # base_name = os.path.splitext(file_name)[0]
        file_list.append((folder_path, file_name))

    return file_list

def safely_delete_file(file_path):
    """
    안전하게 파일 삭제. 열려 있는 경우 엑셀 파일 닫기 후 재시도.
    
    Parameters:
    - file_path (str): 삭제할 파일 경로
    
    Returns:
    - bool: 파일 삭제 성공 여부
    """
    try:
        os.remove(file_path)

        base_name = os.path.basename(file_path) #경로 제거후 파일명만 출력하기 위해 
        logger.log(f"_output 파일 삭제 완료: {base_name}", level="INFO", also_to_report=True)
        return True
    except PermissionError:
        logger.log(f"파일이 열려 있어 삭제 실패: {file_path}", also_to_report=True)
        close_open_excel_files(file_path)
        try:
            os.remove(file_path)
            logger.log(f"파일 삭제 재시도 성공: {file_path}")
            return True
        except Exception as e:
            logger.log(f"파일 삭제 중 오류 발생: {e}")
            return False
        


def close_open_excel_files(file_name):
    """
    열려 있는 엑셀 파일을 찾아 강제로 닫음.
    
    Parameters:
    - file_name (str): 닫을 엑셀 파일 경로 또는 이름
    """
    pythoncom.CoInitialize()
    xl = win32com.client.Dispatch("Excel.Application")
    workbooks = xl.Workbooks

    try:
        for wb in workbooks:
            if file_name in wb.FullName:
                wb.Close(SaveChanges=False)
                logger.log(f"엑셀 파일 닫음: {wb.FullName}")
    except Exception as e:
        logger.log(f"엑셀 닫기 중 오류 발생: {e}")
    finally:
        xl.Quit()
        pythoncom.CoUninitialize()



