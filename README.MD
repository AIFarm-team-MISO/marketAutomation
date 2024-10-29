# 상품순환파일 만들기 자동화

## 이미지 처리 프로세싱
현재 '이미지필터링' 경로의 모든파일을 순환파일로 만듬(단. xls 파일 처리위주로 만들어짐)
해당파일의 '목록이미지' 열의 행을 리스트로 만들어 이미지필터링(이미지에 문자가 있는지)후
문자있음, 문자없음 을 구별 정렬하여 output.xls 파일을 생성 (순환에 쓰일파일)
이후 '필터링url모음파일.xlsx'를 만들어 필터링 내용을 저장
문자있음, 문자없음 탭을 만들어 각각 저장
파일이 만들어진 이후에는 이미지 필터링전 모음파일의 내용이 없는것만 필터링을 하게됨


## 설치 
https://github.com/UB-Mannheim/tesseract/wiki 설치

python -m venv myenv
myenv\Scripts\activate

pip install pytesseract Pillow requests
pip install pandas openpyxl
pip install openpyxl
pip install xlrd
pip install xlrd openpyxl
pip install xlwt



## 파일구조
marketAutomation/
│
├── main.py                                  # 메인 실행 파일
├── config/                                  # 설정 및 환경 파일 폴더
│   └── settings.py                          # 설정 파일 (크롬드라이버 경로 등)
├── imageFilter/                             # 이미지 필터링 관련 폴더
│   ├── ocr/                                 # OCR 관련 모듈
│   │   └── ocr_checker.py                   # 이미지에서 텍스트 여부를 판별하는 기능
│   ├── ocr_google/
│   │   └── myImageFiltering.py              # 구글 비전 API 사용한 OCR 처리
│   └── excel/                               # 엑셀 파일 처리 관련 모듈
│   │   ├── file_handler.py                  # 엑셀 파일 읽기/저장 처리
│   │   ├── image_processing.py              # 이미지 URL 처리 (OCR 및 필터링 로직)
│   │   ├── url_filter.py                    # 필터링된 URL 저장 처리
│   │   ├── excel_handler.py                 # 전체 엑셀 파일을 처리하는 메인 파일
│   │   └── excel_utils.py                   # 엑셀 관련 함수 통합 (정렬, 열 추가, 필터링 등)
│   │ 
├── rotationAuto/               # 상품 순환 자동화 관련 폴더
│   ├── login/                               # 로그인 관련 모듈
│   │   └── zsm_login.py                    # zsm 로그인 및 메인 페이지로 이동하는 기능
│   ├── workflow/                            # 페이지 이동 및 버튼 클릭 등의 워크플로우 처리
│   │   └── page_workflow.py                # 페이지 이동 및 버튼 클릭 작업 처리
│   └── driver/                              # 드라이버 초기화 관련 모듈
│       └── driver_init.py                   # 드라이버 초기화 모듈
│
├── productNaming/                           # 상품명 가공 관련 폴더
│   ├── name_handler.py                      # 상품명 가공 로직 메인 파일
│   └── naming_utils.py                      # 가공에 필요한 유틸리티 함수 모음
│
│
└── utils/                                   # 유틸리티 함수 폴더
  └── url_checker.py                       # URL 처리 및 로그 출력


Tesseract 경로, 엑셀 경로 및 파일 확장자는 config/settings.py 파일에서 변경할 수 있습니다.
OCR 관련 로직은 ocr/ocr_checker.py에서 수정 가능합니다.
엑셀 관련 로직(열 변경, 저장 경로 변경 등)은 excel/excel_handler.py에서 수정 가능합니다.
로그 출력을 변경하거나, 다른 형태로 확장하려면 utils/url_checker.py에서 수정 가능합니다.

- 순환자동화
현재 로그인이후 엑셀다운로드에서 막힘. 
일단 다운로드까지 기다리고 폴더에 .crdownload 파일이 생성되면
브라우저의 다운로드 아이콘을 클릭후 계속 다운로드로 수동으로 다운로드 되도록 설정하자 

## 패키지 설치 
pip install selenium
pip install webdriver-manager


## 크롬드라이버 최신버전 설치 
from webdriver_manager.chrome import ChromeDriverManager
driver_path = ChromeDriverManager().install()
print(f"path : {driver_path}")
path : C:\Users\Administrator\.wdm\drivers\chromedriver\win64\130.0.6723.58\chromedriver-win32/chromedriver.exe


## 진행상황
- 10/20
F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일\이미지필터링 으로 파일경로를 정하고 
파일경로에 있는 파일을 기준으로 변경하였음.

- 10/21
엑셀파일 다운로드가 제대로 되지않음
파일경로를 설정하여도 파일경로가 먹히지 않음. (된적도 있었기 때문에 한글문제는 아닌듯한데 확인필요)

- 10/23
이미지필터링
Google Cloud Vision API 로 사용하기로 결정
일단은 이번에 만들어진 순환파일들로 테스트 해보고 되겠다 싶으면 (현재 테스트중)

필터링된 url을 저장하는 모음url엑셀파일을 만들었음

할일 10/24 >> 
1. 모음url엑셀파일이 있는경우 없는것만 필터링, 중복처리 - 완료
2. 글자있음 정렬 해결하기 - 행전체가 정렬되어야 함 -완료

할일 10 /25 >>
1. 링크모음 파일과 비교해서 이전에 문자있음 이력이 있는지 판별해 이력이 있는경우 목록있음 
으로 표시하여 이미지필터에 들어가지 않는 것으로 변경됨
2. 단지 글자없음의 경우 이력이 남지 않아 계속 필터링 될수 밖에 없으므로 이걸 어떻게 해결할것인가
문제는 output 파일이 있어야 되고(이미지 있음과 없음의) 그에 맞는 링크들도 있어야 되기때문에 
해결이 어렵다. 그래서 일단 output파일을 변경하기로 함
기존 url열을 활용하지 않고 새로운 열을 만들어 그곳에 이내용들을 정리
그렇게 하면 순환도 가능하고 이력도 남길수 있을듯..
- 우선 output파일의 변경 하기 
내일 다시 생각해보고 하나씩 적용해보자. 


- 진행상황 10/27
현재 '이미지필터링' 경로의 모든파일을 순환파일로 만듬(단. xls 파일 처리위주로 만들어짐)
해당파일의 '목록이미지' 열의 행을 리스트로 만들어 이미지필터링(이미지에 문자가 있는지)후
문자있음, 문자없음 을 구별 정렬하여 output.xls 파일을 생성 (순환에 쓰일파일)
이후 '필터링url모음파일.xlsx'를 만들어 필터링 내용을 저장
문자있음, 문자없음 탭을 만들어 각각 저장
파일이 만들어진 이후에는 이미지 필터링전 모음파일의 내용이 없는것만 필터링을 하게됨

버전 0.1로 릴리즈(나중에 돌아오기 위한 태그)
git tag -a v0.1 -m "버전 0.1 릴리즈"
git push origin v0.1
* 이후 이버전으로 돌아오는것은 그때가서 다시 확인해보자. 

##  이후 할일 
1. 새로운 버전으로 순환파일을 적용해 순환해보고 오류 확인
2. 로그인 이후 파일다운로드 픽스
3. 다운로드 받은 파일 순환파일 만들기
5. 최초 로그인전 번호등을 입력해 해당 순환파일 모두를 다운받아 처리하게 만들기 

* 위의 내용들은 이후 상품명가공과 카테고리작업이후 속행예정

# 상품명가공 자동화 시작 (10/29)


## 진행상황
상품명 가공 및 복사: 상품명을 읽고 새 열에 배치하여 데이터를 재구성.
색상 적용 기능: 특정 조건에 따라 색상을 지정해 상품의 구분을 용이하게 처리.
정렬 기능 분리 및 개선: 정렬과 색상 적용을 상황에 맞게 분리해, 필요한 기능을 유연하게 호출할 수 있도록 개선.
출력 파일 생성: 모든 작업을 수행한 후 output 파일로 저장하여, 최종 결과를 검토할 수 있게 구조화.


