import os
from datetime import datetime

class Logger:
    def __init__(self, log_file="debug.log", enable_console=True):
        """
        Logger 클래스 초기화
        :param log_file: 로그 파일 경로
        :param enable_console: 콘솔 출력 활성화 여부
        """
        self.log_file = log_file
        self.enable_console = enable_console
        self.emojis = {
            "기본상품명": "📝",
            "제품군": "🛒",
            "메인키워드": "🔑",
            "고정키워드": "📌",
            "용도": "🛠️ ",
            "사양": "⚙️ ",
            "스타일": "🎨",
            "기타 카테고리": "📂",
            "연관검색어": "🔍",
            "브랜드키워드": "🏷️ ",
            "음식 카테고리 체크": "🍴",
            "이미지 필터링": "🖼️",
            "상품명 가공": "🛒",
            "도매토피아 가공": "🏷️",
            "순환 파일 테스트": "🔄",
            "모든 마켓 폴더 생성": "🔄",
            "스마트스토어": "💚",
            "옥션/지마켓": "💙",
            "11번가": "❤️",
            "고도몰": "⚪"

        }

        # 로그 파일 열기
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_file_handle = open(log_file, "a", encoding="utf-8")

    def __del__(self):
        if self.log_file_handle:
            self.log_file_handle.close()

    def _get_emoji(self, text):
        """
        텍스트에서 이모지를 추출하는 메서드.
        :param text: 이모지를 찾을 텍스트
        :return: 매핑된 이모지 문자열
        """
        return next((emoji for key, emoji in self.emojis.items() if key in text), "")

    def log(self, message, data=None, level="INFO", emoji_key=None, include_emoji=True):
        """
        메시지를 로그 파일과 콘솔에 출력
        :param message: 출력할 메시지 (기본 텍스트, 여러 줄 가능)
        :param data: 추가 데이터 (ex: 변수 값 등)
        :param level: 로그 레벨 (INFO, DEBUG, ERROR 등)
        :param emoji_key: 이모지 키 (self.emojis에서 가져옴)
        :param include_emoji: 이모지를 포함할지 여부
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = self.emojis.get(emoji_key, "") if include_emoji else ""  # 명시적으로 지정된 이모지
        emoji = emoji if not message.startswith(emoji) else ""  # 메시지에 이미 포함된 경우 중복 방지

        # 메시지와 추가 데이터를 조합
        full_message = f"{message}{data}" if data else message

        # 여러 줄 메시지 처리
        lines = full_message.split("\n")
        formatted_lines = [f"[{timestamp}] [{level}] {emoji} {line}".strip() for line in lines]

        # 콘솔 출력
        if self.enable_console:
            for line in formatted_lines:
                print(line)

        # 로그 파일 저장
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write("\n".join(formatted_lines) + "\n")

    def log_choices(self, choices, messege=None):
        """
        선택지를 로그와 콘솔에 출력하는 메서드.
        :param choices: 선택지 딕셔너리 (key: 선택 번호, value: 선택 항목)
        """
        self.log_separator(char="=", level="INFO")

        self.log(f"< {messege} > 작업을 선택!", level="INFO")
        for key, value in choices.items():
            emoji = self._get_emoji(value)
            self.log(f"{key}. {emoji} {value}", level="INFO")

    def log_list(self, title, data, level="DEBUG"):
        """
        리스트 데이터를 한 줄씩 출력하도록 로그에 기록.
        :param title: 출력 제목
        :param data: 리스트 데이터
        :param level: 로그 레벨
        """
        emoji = self._get_emoji(title)
        if title.startswith(emoji):
            emoji = ""  # 제목에 이미 이모지가 포함된 경우 빈 문자열로 설정

        if data:
            self.log(f"{emoji} {title}:".strip(), level=level)  # 제목 출력
            for item in data:
                self.log(f"  - {item}", level=level)  # 리스트의 각 항목 출력
        else:
            self.log(f"{emoji} {title}: 없음".strip(), level=level)

    def log_separator(self, char="=", length=100, level="INFO", title=None):
        """
        로그에 구분선을 추가하는 메서드
        :param char: 구분선에 사용할 문자 (기본값: '=')
        :param length: 구분선 길이 (기본값: 100)
        :param level: 로그 레벨
        :param title: 구분선 제목 (선택적)
        """
        separator = char * length
        if title:
            emoji = self._get_emoji(title)
            emoji = emoji if not title.startswith(emoji) else ""  # 중복 방지
            self.log(f"{emoji} {title}", level=level)
        self.log(separator, level=level)

    def log_dict(self, title, data, level="DEBUG"):
        """
        딕셔너리 데이터를 보기 쉽게 포맷팅하여 로그에 출력.
        :param title: 출력 제목
        :param data: 딕셔너리 데이터
        :param level: 로그 레벨
        """

        if data is None:
            self.log(f"{title}: 데이터가 None입니다.", level="WARNING")
            return
    
        emoji = self._get_emoji(title)
        if title.startswith(emoji):
            emoji = ""  # 중복 방지

        self.log(f"{emoji} {title}:", level=level, include_emoji=False)

        for key, value in data.items():
            item_emoji = self.emojis.get(key, "")
            item_emoji = item_emoji if not key.startswith(item_emoji) else ""  # 중복 방지

            if isinstance(value, list):
                formatted_value = ", ".join(value) if value else "없음"
            else:
                formatted_value = value if value else "없음"

            self.log(f"    {item_emoji} {key}: {formatted_value}".strip(), level=level)

    def log_processed_data(self, basic_product_names, make_naver_names, title="최종 상품명가공 리스트", level="INFO"):
        """
        기본상품명과 가공된 상품명을 보기 쉽게 포맷팅하여 로그에 출력.
        :param basic_product_names: 기본상품명 리스트
        :param make_naver_names: 최적화된 상품명 리스트
        :param title: 로그 제목
        :param level: 로그 레벨
        """
        self.log_separator(title=title, char="=", level=level)

        for i, basic_name in enumerate(basic_product_names, start=1):
            # 가공상품명과 기본상품명을 연결
            processed_name = make_naver_names[i - 1] if i - 1 < len(make_naver_names) else "없음"

            # 로그 출력
            self.log(f"🔑 기본상품명{i} → {basic_name}", level=level)
            self.log(f"    - 가공상품명 -> {processed_name}", level=level)

        self.log_separator(char="=", level=level)




