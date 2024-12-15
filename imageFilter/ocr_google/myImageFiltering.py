import os
from google.cloud import vision
import requests
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
import re

# Google Cloud Vision API 클라이언트 설정 (환경 변수로 경로 설정)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"F:\marketAutomation\imageFilter\ocr_google\myimagefiltering-cbe09de0dab6.json"

# Google Cloud Vision API 클라이언트 생성
client = vision.ImageAnnotatorClient()

# 이미지에 텍스트가 있는지 판별하는 함수
import os
from google.cloud import vision
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import re
import urllib3

# Google Cloud Vision API 클라이언트 설정 (환경 변수로 경로 설정)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"F:\marketAutomation\imageFilter\ocr_google\myimagefiltering-cbe09de0dab6.json"

# Google Cloud Vision API 클라이언트 생성
client = vision.ImageAnnotatorClient()

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 이미지에 텍스트가 있는지 판별하는 함수
def is_text_in_image(image_url):
    """
    이미지 URL에서 텍스트가 포함되어 있는지 감지하는 함수.
    Google Cloud Vision API를 사용하여 텍스트를 감지하고,
    HTTPS 실패 시 HTTP로 자동 전환하여 재시도합니다.
    
    Args:
        image_url (str): 처리할 이미지 URL.

    Returns:
        str: 감지된 텍스트 정보(상단 및 하단). 감지된 텍스트가 없으면 빈 문자열 반환.
    """
    try:
        # HTTPS를 우선 시도하며, 실패 시 HTTP로 재시도 설정
        try_https_first = True  # HTTPS 시도 여부 플래그
        current_url = image_url  # 현재 URL (HTTPS → HTTP 변경될 수 있음)

        # HTTPS -> HTTP 재시도 처리 루프
        while True:
            try:
                # 이미지 다운로드
                if current_url.startswith('http'):
                    # URL에서 이미지 요청 (SSL 검증 비활성화)
                    response = requests.get(current_url, timeout=10, verify=False)
                    response.raise_for_status()  # HTTP 에러가 발생하면 예외 처리


                    # HTTP로 전환된 경우 성공 메시지 추가
                    if not try_https_first:
                        print(f"HTTP로 전환 후 성공적으로 이미지 다운로드 완료: {current_url}")

                    img = Image.open(BytesIO(response.content))

                else:
                    # 로컬 파일 경로로 이미지 열기
                    img = Image.open(current_url)

                # 이미지 전처리: 흑백 변환 및 대비 강화
                img = img.convert("L")  # 이미지를 흑백으로 변환
                img = ImageEnhance.Contrast(img).enhance(2)  # 대비 강화

                # 이미지 크기 가져오기
                width, height = img.size

                # 상단 15% 영역 크롭
                top_cropped_img = img.crop((0, 0, width, int(height * 0.15)))  # 상단 15% 영역
                top_cropped_img.save("top_cropped_img.jpg")  # 임시 저장

                # 하단 15% 영역 크롭
                bottom_cropped_img = img.crop((0, int(height * 0.85), width, height))  # 하단 15% 영역
                bottom_cropped_img.save("bottom_cropped_img.jpg")  # 임시 저장

                # Google Cloud Vision API를 사용해 텍스트 감지
                def detect_text(image_path):
                    """
                    Google Cloud Vision API를 통해 이미지에서 텍스트 감지.
                    
                    Args:
                        image_path (str): 텍스트를 감지할 이미지 파일 경로.

                    Returns:
                        str: 감지된 텍스트. 텍스트가 없으면 빈 문자열 반환.
                    """
                    with open(image_path, 'rb') as image_file:
                        content = image_file.read()

                    image = vision.Image(content=content)
                    response = client.text_detection(image=image)
                    texts = response.text_annotations
                    return texts[0].description.strip() if texts else ''

                # 상단 텍스트 감지
                top_text = detect_text("top_cropped_img.jpg")
                print(f"상단 추출된 텍스트: '{top_text}'")

                # 하단 텍스트 감지
                bottom_text = detect_text("bottom_cropped_img.jpg")
                print(f"하단 추출된 텍스트: '{bottom_text}'")

                # 텍스트 정리 및 필터링: 불필요한 문자 제거
                def clean_text(text):
                    """
                    텍스트에서 알파벳, 숫자, 한글만 남기고 의미 없는 문자를 제거.
                    
                    Args:
                        text (str): 원본 텍스트.

                    Returns:
                        str: 필터링된 텍스트.
                    """
                    clean = re.sub(r'[^A-Za-z0-9가-힣]', '', text)
                    return clean if len(clean) > 1 else ''  # 두 글자 이상인 경우만 반환

                # 텍스트 필터링
                filtered_top_text = clean_text(top_text)
                filtered_bottom_text = clean_text(bottom_text)

                # 상단 또는 하단 텍스트가 존재하는지 확인
                if filtered_top_text or filtered_bottom_text:
                    print(f"감지된 텍스트: 상단: {filtered_top_text}, 하단: {filtered_bottom_text}")
                    # 상단과 하단 텍스트를 결합하여 반환
                    return f"상단: {filtered_top_text}, 하단: {filtered_bottom_text}".strip()
                else:
                    print("텍스트를 감지하지 못함 또는 의미 없는 텍스트")
                    return ''  # 텍스트가 없는 경우 빈 문자열 반환

            except requests.exceptions.SSLError as e:
                # HTTPS 에러 발생 시 HTTP로 전환하여 재시도
                if try_https_first and current_url.startswith("https://"):
                    print(f"HTTPS 연결 실패. HTTP로 전환하여 재시도합니다")
                    current_url = current_url.replace("https://", "http://")
                    try_https_first = False  # HTTP로 전환했으므로 플래그 업데이트
                else:
                    # HTTPS 및 HTTP 모두 실패 시 예외 발생
                    print("HTTPS 및 HTTP 모두 연결 실패")
                    raise

    except Exception as e:
        # 예외 발생 시 로그 출력 및 False 반환
        print(f"Error processing image {image_url}: {e}")
        return False






# 백업코드 : 필터링 90이상 

# def is_text_in_image(image_url):
#     try:
#         # URL에서 이미지를 다운로드
#         if image_url.startswith('http'):
#             response = requests.get(image_url)
#             img = Image.open(BytesIO(response.content))
#         else:
#             # 로컬 파일 경로에서 이미지 불러오기
#             img = Image.open(image_url)

#         # 이미지 전처리: 흑백으로 변환하여 대비를 강화
#         img = img.convert("L")  # 흑백 변환
#         img = ImageEnhance.Contrast(img).enhance(2)  # 대비 강화

#         # 이미지의 크기 측정
#         width, height = img.size

#         # 상단 15% 영역
#         top_cropped_img = img.crop((0, 0, width, int(height * 0.15)))  # 상단 15% 크롭
#         top_cropped_img.save("top_cropped_img.jpg")  # 임시 저장

#         # 하단 15% 영역
#         bottom_cropped_img = img.crop((0, int(height * 0.85), width, height))  # 하단 15% 크롭
#         bottom_cropped_img.save("bottom_cropped_img.jpg")  # 임시 저장

#         def detect_text(image_path):
#             """Google Cloud Vision API를 사용해 텍스트 감지"""
#             with open(image_path, 'rb') as image_file:
#                 content = image_file.read()

#             image = vision.Image(content=content)
#             response = client.text_detection(image=image)
#             texts = response.text_annotations
#             return texts[0].description.strip() if texts else ''

#         # 상단 15% OCR 처리
#         top_text = detect_text("top_cropped_img.jpg")
#         print(f"상단 추출된 텍스트: '{top_text}'")

#         # 하단 15% OCR 처리
#         bottom_text = detect_text("bottom_cropped_img.jpg")
#         print(f"하단 추출된 텍스트: '{bottom_text}'")

#         # 텍스트 정리 및 필터링: 알파벳, 숫자, 한글만 남기고, 의미 없는 문자 제거
#         def clean_text(text):
#             # 알파벳, 숫자, 한글만 남기고, 의미 없는 문자 제거
#             clean = re.sub(r'[^A-Za-z0-9가-힣]', '', text)
#             return clean if len(clean) > 1 else ''

#         # 텍스트 필터링
#         filtered_top_text = clean_text(top_text)
#         filtered_bottom_text = clean_text(bottom_text)

#         # 상단 혹은 하단 텍스트가 두 글자 이상인지 확인
#         if filtered_top_text or filtered_bottom_text:
#             print(f"걸러진 텍스트: 상단: {filtered_top_text}, 하단: {filtered_bottom_text}")
#             return True  # 상단 또는 하단에 유효한 텍스트가 있으면 "글자 있음"
#         else:
#             print("텍스트를 감지하지 못함 또는 의미 없는 텍스트")
#             return False  # 유효한 텍스트가 없으면 "글자 없음"

#     except Exception as e:
#         # 예외 발생 시 False 반환 (이미지 문제 또는 다운로드 실패)
#         print(f"Error processing image {image_url}: {e}")
#         return False