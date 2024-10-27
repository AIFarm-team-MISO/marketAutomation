import pytesseract
from PIL import Image, ImageEnhance, ImageOps

# Tesseract 경로 설정 (Windows 사용자만 해당)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지에 텍스트가 있는지 판별하는 함수 (로컬 파일 경로에서 이미지 불러오기)
def is_text_in_image(image_path):
    try:
        # 로컬 파일 경로에서 이미지 불러오기
        img = Image.open(image_path)

        # 이미지 전처리: 흑백으로 변환, 대비 강화, 색 반전
        img = img.convert("L")  # 흑백 변환
        img = ImageEnhance.Contrast(img).enhance(2)  # 대비 강화
        img = ImageOps.invert(img)  # 색상 반전 (흰 텍스트를 검은 배경으로 만들기)

        # Tesseract 설정 (psm 6: 가로 쓰기 블록에 적합)
        custom_config = r'--oem 3 --psm 6'

        # OCR을 사용하여 이미지에서 텍스트 추출
        text = pytesseract.image_to_string(img, config=custom_config)

        # 텍스트가 있는지 여부를 확인
        if text.strip():
            print(f"추출된 텍스트: {text.strip()}")
            return True
        else:
            print("텍스트를 감지하지 못함")
            return False
    except Exception as e:
        # 예외 발생 시 False 반환 (이미지 문제 또는 다운로드 실패)
        print(f"Error processing image {image_path}: {e}")
        return False

# 테스트 이미지 로컬 경로 (경로를 Raw 문자열로 설정)
image_path = r'F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일\이미지필터링\7_12p_cdcase_listimg_02.jpg'

# 함수 실행 예시
is_text_in_image(image_path)
