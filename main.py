# main.py
from imageFilter.excel.excel_handler import process_imageFiltering_excel_file
from imageFilter.excel.excel_utils import process_all_excel_files 
from rotationAuto.login.zsm_login import login_and_navigate, close_driver
from rotationAuto.workflow.page_workflow import navigate_to_download_page
from rotationAuto.workflow.page_workflow import select_radio_button
from rotationAuto.workflow.page_workflow import click_download_button
from config.settings import EXCEL_PATH

from config.settings import NAMING_EXCEL_PATH
from productNaming.name_handler import process_namingChange_excel_file

def zsm_login():
    # 로그인 및 드라이버 설정
    driver = login_and_navigate()

    # 메인 페이지에서 "상품DB 다운로드" 버튼을 클릭하여 다음 페이지로 이동
    print(f'상품DB 다운로드 페이지 이동시작')
    navigate_to_download_page(driver)

    # 해당 타이틀에 맞는 라디오 버튼을 클릭
    print(f'라디오 버튼을 클릭 이동시작')
    select_radio_button(driver, '!!상품원본!!글로벌')

    # 상품 DB 다운로드 버튼 클릭
    print(f'다운로드 버튼을 클릭 이동시작')
    click_download_button(driver)
    # 드라이버 종료
    close_driver(driver)

def process_all_files(file_path):
    """
    모든 파일을 처리하는 함수. process_all_excel_files를 호출하고, 반환된 파일 리스트를 이용해 처리.
    
    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    """
    # 모든 엑셀 파일을 가져와서 파일 리스트를 받음
    file_list = process_all_excel_files(file_path)

    # 디버깅: 파일 리스트 출력
    print(f"처리할 파일 리스트: {file_list}")

    
    # 파일 리스트에서 각 파일에 대해 처리
    for file_path, base_file_name in file_list:
        print(f"파일 처리 중: {base_file_name}")  # 디버깅: 현재 파일 이름 출력

        # 파일 경로가 NAMING_EXCEL_PATH이면 상품명 가공 처리
        if file_path.startswith(NAMING_EXCEL_PATH):
            process_namingChange_excel_file(file_path, base_file_name)
        else: # 파일경로가 EXCEL_PATH 면 이미지필터링 처리
            process_imageFiltering_excel_file(file_path, base_file_name)

        
    

if __name__ == "__main__":
    # zsm_login()


    # EXCEL_PATH : '이미지필터링' 폴더의 엑셀 파일 처리
    # NAMING_EXCEL_PATH : '#상품명가공' 폴더의 엑셀파일 처리 
    process_all_files(EXCEL_PATH)



