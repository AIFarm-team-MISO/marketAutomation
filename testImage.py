import os
import pandas as pd
import pytesseract
from PIL import Image
import requests
from io import BytesIO

# Tesseract 경로 설정 (Windows 사용자만 해당)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지에 텍스트가 있는지 판별하는 함수
def is_text_in_image(image_url):
    try:
        # 이미지 다운로드
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        # OCR을 사용하여 이미지에서 텍스트 추출
        text = pytesseract.image_to_string(img)

        # 텍스트가 있는지 여부를 확인
        if text.strip():
            return True
        else:
            return False
    except Exception as e:
        # 예외 발생 시 False 반환 (이미지 문제 또는 다운로드 실패)
        print(f"Error processing image {image_url}: {e}")
        return False

# 프로그램 실행 함수 (엑셀 파일 처리)
def run_program():
    # 사용자로부터 경로와 파일 이름을 각각 입력받기
    file_path = input("엑셀 파일이 위치한 경로를 입력하세요 (예: F:\\work\\#쇼핑몰\\#대량등록): ")
    file_name = input("엑셀 파일 이름을 입력하세요 (확장자 없이, 예: ZSM_20241015_esellers): ")

    # 파일 확장자 설정 (주석으로 .xls 또는 .xlsx 중 하나로 설정)
    file_extension = '.xls'  # .xlsx로 변경할 수 있음

    # 최종 파일 경로 생성
    file_name_with_extension = f"{file_name}{file_extension}"
    excel_file_path = os.path.join(file_path, file_name_with_extension)

    # 터미널에 전체 파일 경로 출력
    print(f"엑셀 파일 경로: {excel_file_path}")

    # 파일 확장자에 따른 엔진 설정
    if file_extension == '.xls':
        engine = 'xlrd'  # .xls 파일을 처리할 때 사용하는 엔진
    elif file_extension == '.xlsx':
        engine = 'openpyxl'  # .xlsx 파일을 처리할 때 사용하는 엔진
    else:
        print("지원되지 않는 파일 형식입니다.")
        return

    # 엑셀 파일 읽기
    try:
        df = pd.read_excel(excel_file_path, engine=engine)
    except FileNotFoundError:
        print(f"지정한 경로에 엑셀 파일이 존재하지 않습니다: {excel_file_path}")
        return

    # 실제 엑셀 파일의 이미지 URL이 포함된 열 이름 확인 후 설정
    image_column = '목록 이미지*'  # 엑셀에서 이미지 URL이 포함된 열 이름을 확인하여 변경하세요.

    # 이미지 URL이 있는 열을 확인하고, 텍스트가 있으면 '글자있음'으로 변경
    if image_column not in df.columns:
        print(f"'{image_column}' 열이 엑셀 파일에 존재하지 않습니다. 열 이름을 확인해 주세요.")
        return

    for idx, row in df.iterrows():
        image_url = row[image_column]

        if pd.notna(image_url):  # URL이 존재하는지 확인
            print(f"{idx + 1}/{len(df)}번째 행 처리 중... URL: {image_url}")  # 진행 상황 출력과 URL 표시
            if is_text_in_image(image_url):
                df.at[idx, image_column] = '글자있음'
    
    # 변경된 데이터프레임을 엑셀 파일로 다시 저장
    output_file_path = os.path.join(file_path, file_name_with_extension.replace(file_extension, f"_output{file_extension}"))
    df.to_excel(output_file_path, index=False)

    print(f"처리가 완료되었습니다. 결과가 {output_file_path}에 저장되었습니다.")

# 개별 URL 처리 함수
def check_single_url():
    # 사용자가 URL을 입력하도록 요청
    url = input("판별할 이미지 URL을 입력하세요: ")
    
    # URL에서 텍스트 여부 확인
    if is_text_in_image(url):
        print("이미지에 텍스트가 있습니다.")
    else:
        print("이미지에 텍스트가 없습니다.")

# 프로그램 실행
if __name__ == "__main__":
    run_program()

    # URL 하나만 판별하는 함수 실행 예시 (주석 처리됨)
    # check_single_url()
