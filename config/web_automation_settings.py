import os

# ============================================================
# 스마트스토어 리뷰 필터링 설정
# ============================================================

SMARTSTORE_REVIEW_ACTIVE_MARKET = "today_dameum"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "onestop_living"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "onestop_living"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "salim_gijun"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "pajama_channel"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "tool_monster"
# SMARTSTORE_REVIEW_ACTIVE_MARKET = "nature"

SMARTSTORE_REVIEW_MARKETS = {
    "onestop_living": {
        "market_name": "onestop_living",
        "market_display_name": "원스톱리빙",
    },
    "today_dameum": {
        "market_name": "today_dameum",
        "market_display_name": "오늘담음",
    },
    "salim_gijun": {
        "market_name": "salim_gijun",
        "market_display_name": "살림기준",
    },
    "pajama_channel": {
        "market_name": "pajama_channel",
        "market_display_name": "파자마채널",
    },
    "tool_monster": {
        "market_name": "tool_monster",
        "market_display_name": "툴몬스터",
    },
    "nature": {
        "market_name": "nature",
        "market_display_name": "네스쳐",
    },
}


def get_smartstore_review_market_config(market_key=None):
    """
    스마트스토어 리뷰 필터링용 마켓 설정을 반환한다.
    """

    if market_key is None:
        market_key = SMARTSTORE_REVIEW_ACTIVE_MARKET

    if market_key not in SMARTSTORE_REVIEW_MARKETS:
        raise ValueError(
            f"등록되지 않은 스마트스토어 리뷰 필터링 마켓입니다: {market_key}"
        )

    return SMARTSTORE_REVIEW_MARKETS[market_key]


def get_smartstore_review_market_config(market_key=None):
    """
    스마트스토어 리뷰 필터링용 마켓 설정을 반환한다.
    """

    if market_key is None:
        market_key = SMARTSTORE_REVIEW_ACTIVE_MARKET

    if market_key not in SMARTSTORE_REVIEW_MARKETS:
        raise ValueError(
            f"등록되지 않은 스마트스토어 리뷰 필터링 마켓입니다: {market_key}"
        )

    return SMARTSTORE_REVIEW_MARKETS[market_key]

# =========================================================
# 0. 엑셀파일 경로
# =========================================================


REVIEW_PRODUCTS_PATH = (
    r"F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일"
    r"\6.리뷰필터링파일"
)

# =========================================================
# 1. 프로젝트 경로
# =========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


# =========================================================
# 2. 웹자동화 전용 폴더
# =========================================================
# 기존:
# WEB_AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "web_automation_data")
#
# 변경:
# F:\marketAutomation\utils\web_automation\web_automation_data

WEB_AUTOMATION_DIR = os.path.join(
    PROJECT_ROOT,
    "utils",
    "web_automation",
    "web_automation_data"
)

CHROME_PROFILE_ROOT = os.path.join(
    WEB_AUTOMATION_DIR,
    "chrome_profiles"
)

DEFAULT_DOWNLOAD_DIR = os.path.join(
    WEB_AUTOMATION_DIR,
    "downloads"
)


# =========================================================
# 2. Selenium Chrome 공통 설정
# =========================================================

CHROME_OPTIONS = {
    "start_maximized": False,

    # 브라우저 창 크기
    "window_width": 1500,
    "window_height": 1000,
    "window_position_x": 0,
    "window_position_y": 0,

    "enable_logging": True,
    "disable_gpu": True,
    "allow_running_insecure_content": True,
    "disable_automation_controlled": True,
    "headless": False,

    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "download_prompt": False,
    "safe_browsing": False,
    "allow_automatic_downloads": True,

    "use_chrome_profile": True,
}


# =========================================================
# 3. 공통 대기 시간 설정
# =========================================================

WAIT_SETTINGS = {
    "page_load_wait": 10,
    "element_wait": 10,
    "clickable_wait": 5,
    "after_login_wait": 10,
    "after_login_extra_sleep": 1,
    "default_sleep": 1,
}


# =========================================================
# 4. 공통 로그인 버튼 후보
# =========================================================
# 사이트별 로그인 버튼이 다를 수 있으므로
# 일반적으로 많이 쓰는 selector 후보를 공통으로 둔다.

COMMON_LOGIN_BUTTON_SELECTORS = [
    ("css", "button[type='submit']"),
    ("css", "input[type='submit']"),
    ("css", ".login_btn"),
    ("css", ".btn_login"),
    ("css", ".btn-login"),
    ("css", ".loginBtn"),
    ("css", ".btnLogin"),
    ("xpath", "//button[contains(text(), '로그인')]"),
    ("xpath", "//input[@value='로그인']"),
    ("xpath", "//a[contains(text(), '로그인')]"),
]


# =========================================================
# 5. 공통 검색창 후보
# =========================================================
# 이후 상품코드 검색 자동화에서 사용 예정

COMMON_SEARCH_INPUT_SELECTORS = [
    ("css", "input[name='keyword']"),
    ("css", "input[name='search']"),
    ("css", "input[name='search_str']"),
    ("css", "input[name='skeyword']"),
    ("css", "input[name='q']"),
    ("css", "input[id*='search']"),
    ("css", "input[class*='search']"),
    ("css", "input[placeholder*='검색']"),
    ("css", "input[type='search']"),
    ("css", "input[type='text']"),
]


# =========================================================
# 6. 공통 상태 판별 문구
# =========================================================
# 이후 상품 상태 판별 자동화에서 사용 예정

COMMON_NO_RESULT_WORDS = [
    "검색 결과가 없습니다",
    "검색결과가 없습니다",
    "상품이 없습니다",
    "등록된 상품이 없습니다",
    "일치하는 상품이 없습니다",
    "찾으시는 상품이 없습니다",
    "검색된 상품이 없습니다",
    "no result",
    "no products",
]

COMMON_SOLD_OUT_WORDS = [
    "품절",
    "일시품절",
    "재고없음",
    "재고 없음",
    "판매중지",
    "판매 중지",
    "판매종료",
    "판매 종료",
    "sold out",
    "out of stock",
]

COMMON_SELLING_WORDS = [
    "장바구니",
    "바로구매",
    "구매하기",
    "주문하기",
]


# =========================================================
# 7. 판매/도매처 사이트별 설정
# =========================================================
# 핵심:
# 사이트마다 다른 것은 여기에 넣고,
# sale_login_manager.py는 공통 로직만 담당한다.

SALE_SITES = {
    "3mro": {
        "site_name": "3MRO",
        

        # -------------------------------------------------
        # 기본 URL
        # -------------------------------------------------
        "main_url": "https://3mro.co.kr/shop/",
        "login_url": "https://3mro.co.kr/bbs/login.php",

        # -------------------------------------------------
        # 로그인 정보
        # 실제 운영에서는 나중에 .env로 빼는 것도 가능
        # -------------------------------------------------
        "username": "callenge2000",
        "password": "$sevenstar15$",

        # -------------------------------------------------
        # 로그인 입력창 selector
        # -------------------------------------------------
        "id_selector": ("name", "mb_id"),
        "password_selector": ("name", "mb_password"),

        # -------------------------------------------------
        # 로그인 버튼
        # 사이트 전용 selector가 있으면 COMMON 대신 별도 지정 가능
        # -------------------------------------------------

        # 로그인 버튼
        "login_button_selectors": [
        ("css", "button[type='submit'][value='로그인']"),
        ("css", "button.btn-e.btn-e-dark.btn-e-lg.btn-block"),
        ("xpath", "//button[@type='submit' and @value='로그인']"),
        ("xpath", "//button[contains(text(), '로그인')]"),
         ],


        # 버튼 클릭 실패 시 비밀번호 칸에서 Enter
        "submit_fallback": "enter_password",

        # -------------------------------------------------
        # 로그인 페이지 판단 기준
        # -------------------------------------------------
        "login_url_keywords": ["login"],
        "login_page_words": ["로그인", "아이디", "비밀번호"],

        # -------------------------------------------------
        # 로그인 성공 판단 기준
        # -------------------------------------------------
        # 중요: URL로 성공 판단하지 않기
        "success_url_keywords": [],

        # 중요: 로그인 후에만 보이는 문구만 넣기
        "success_page_words": ["로그아웃"],

        "after_login_wait_seconds": 10,
        "after_login_extra_sleep_seconds": 1,

        "force_login_when_unknown": True,

        "download_dir": os.path.join(DEFAULT_DOWNLOAD_DIR, "3mro"),
        "profile_name": "3mro",
        "headless": True,


        # -------------------------------------------------
        # 로그인 이후 검색창확인
        # -------------------------------------------------
        "search_input_selectors": [
            ("name", "sq"),
        ],
        "search_submit_method": "enter",


        # -------------------------------------------------
        # 검색 이후 결과 갯수 확인
        # -------------------------------------------------
        "search_result_count_selectors": [
            ("css", "strong.text-crimson"),
        ],

    },
}


# =========================================================
# 8. 기존 코드 호환용 alias
# =========================================================
# 기존 sale_login_manager.py에서 WHOLESALE_SITES 이름을 사용하고 있다면
# 이 alias 덕분에 그대로 사용 가능.

WHOLESALE_SITES = SALE_SITES

