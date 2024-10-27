import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import requests
from io import BytesIO
import re
from PIL import Image

# Tesseract 경로 설정 (Windows 사용자만 해당)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# 이미지에 텍스트가 있는지 판별하는 함수 (한 줄 텍스트 중점)
def is_text_in_image(image_url):
    try:
        # URL에서 이미지를 다운로드
        if image_url.startswith('http'):
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
        else:
            # 로컬 파일 경로에서 이미지 불러오기
            img = Image.open(image_url)

        # 이미지의 크기 측정
        width, height = img.size

        # 상단 10% 영역
        top_cropped_img = img.crop((0, 0, width, int(height * 0.10)))  # 상단 10% 크롭

        # 하단 10% 영역
        bottom_cropped_img = img.crop((0, int(height * 0.90), width, height))  # 하단 10% 크롭

        # Tesseract 설정 (psm 7: 한 줄 텍스트에 적합)
        custom_config = r'--oem 3 --psm 7'

        # 상단 10% OCR 처리
        top_text = pytesseract.image_to_string(top_cropped_img, config=custom_config).strip()
        print(f"상단 추출된 텍스트: '{top_text}'")

        # 하단 10% OCR 처리
        bottom_text = pytesseract.image_to_string(bottom_cropped_img, config=custom_config).strip()
        print(f"하단 추출된 텍스트: '{bottom_text}'")

        # 텍스트 정리 및 필터링: 불필요한 특수문자 제거, 최소 두 글자 이상, 의미 없는 패턴 필터링
        def clean_text(text):
            # 알파벳, 숫자, 한글만 남기고, 의미 없는 문자 제거
            clean = re.sub(r'[^A-Za-z0-9가-힣]', '', text)
            return clean if len(clean) > 1 else ''

        # 텍스트 필터링
        filtered_top_text = clean_text(top_text)
        filtered_bottom_text = clean_text(bottom_text)

        # 의미 없는 일반적인 텍스트 패턴 제거 (예: ee, Oo 등)
        meaningless_patterns = ['ee', 'oo', 'Oo', '—', '-', '_', '||', '===']

        def is_meaningful(text):
            # 패턴에 해당하지 않고 두 글자 이상이면 의미 있는 텍스트로 간주
            if any(pattern in text.lower() for pattern in meaningless_patterns):
                return False
            return len(text) > 1

        # 상단 혹은 하단 텍스트가 의미 있는지 확인
        if is_meaningful(filtered_top_text) or is_meaningful(filtered_bottom_text):
            print(f"걸러진 텍스트: 상단: {filtered_top_text}, 하단: {filtered_bottom_text}")
            return True  # 상단 또는 하단에 유효한 텍스트가 있으면 "글자 있음"
        else:
            print("텍스트를 감지하지 못함 또는 의미 없는 텍스트")
            return False  # 유효한 텍스트가 없으면 "글자 없음"

    except Exception as e:
        # 예외 발생 시 False 반환 (이미지 문제 또는 다운로드 실패)
        print(f"Error processing image {image_url}: {e}")
        return False





# def is_text_in_image(image_url):
#     try:
#         # URL에서 이미지를 다운로드
#         if image_url.startswith('http'):
#             response = requests.get(image_url)
#             img = Image.open(BytesIO(response.content))
#         else:
#             # 로컬 파일 경로에서 이미지 불러오기
#             img = Image.open(image_url)

#         # 이미지 전처리: 흑백으로 변환, 대비 강화, 밝기 조정 및 노이즈 제거
#         img = img.convert("L")  # 흑백 변환
#         img = ImageEnhance.Contrast(img).enhance(3)  # 대비 강화 (값을 3으로 올림)
#         img = ImageEnhance.Brightness(img).enhance(2)  # 밝기 조정 (값을 2로 올림)
#         img = img.filter(ImageFilter.GaussianBlur(1))  # 가우시안 블러로 노이즈 제거

#         # 필요 시 이미지의 하단 30%만 잘라서 처리
#         width, height = img.size
#         cropped_img = img.crop((0, int(height * 0.7), width, height))

#         # Tesseract 설정 (psm 7: 한 줄 텍스트에 적합)
#         custom_config = r'--oem 3 --psm 7'

#         # OCR을 사용하여 이미지에서 텍스트 추출
#         text = pytesseract.image_to_string(cropped_img, config=custom_config).strip()

#         # 추출된 텍스트 로그 출력
#         print(f"추출된 텍스트: '{text}'")

#         # 알파벳, 숫자, 한글이 있는지 확인 (특수 문자만 있는 경우는 제외)
#         if re.search(r'[A-Za-z0-9가-힣]', text):
#             print(f"걸러진 텍스트: {text}")
#             return True  # 알파벳, 숫자, 한글이 있으면 "글자 있음"
#         else:
#             print("텍스트를 감지하지 못함 또는 의미 없는 텍스트")
#             return False  # 알파벳, 숫자, 한글이 없으면 "글자 없음"
#     except Exception as e:
#         # 예외 발생 시 False 반환 (이미지 문제 또는 다운로드 실패)
#         print(f"Error processing image {image_url}: {e}")
#         return False