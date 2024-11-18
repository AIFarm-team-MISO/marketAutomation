from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class KeywordInfo:
    """
    KeywordInfo 클래스는 메인 키워드와 각 카테고리의 보조 키워드를 담는 데이터 클래스입니다.
    
    Attributes:
        main_keyword (str): 메인 키워드.
        fixed_keywords (List[str]): 항상 포함되어야 하는 고정 키워드 목록.
        use (List[str]): 용도에 해당하는 보조 키워드 목록.
        spec (List[str]): 사양에 해당하는 보조 키워드 목록.
        style (List[str]): 스타일에 해당하는 보조 키워드 목록.
        extra (List[str]): 기타 카테고리에 해당하는 추가 정보.
    """
    main_keyword: str = ""
    fixed_keywords: List[str] = field(default_factory=list)  # 고정 키워드가 메인 키워드 아래로 이동
    use: List[str] = field(default_factory=list)
    spec: List[str] = field(default_factory=list)
    style: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)

    def get_categories(self) -> Dict[str, List[str]]:
        """KeywordInfo 객체의 모든 카테고리를 딕셔너리 형태로 반환합니다."""
        return {
            "용도": self.use,
            "사양": self.spec,
            "스타일": self.style,
            "기타 카테고리": self.extra,
            "고정 키워드": self.fixed_keywords  # 고정 키워드도 반환에 포함
        }

    def add_keywords(self, use=None, spec=None, style=None, extra=None, fixed=None):
        """중복 없이 키워드를 추가하는 메서드."""
        if use:
            self.use.extend([u for u in use if u not in self.use])
        if spec:
            self.spec.extend([s for s in spec if s not in self.spec])
        if style:
            self.style.extend([st for st in style if st not in self.style])
        if extra:
            self.extra.extend([e for e in extra if e not in self.extra])
        if fixed:
            self.fixed_keywords.extend([f for f in fixed if f not in self.fixed_keywords])  # 고정 키워드 추가


@dataclass
class SubKeywordInfo:
    """
    SubKeywordInfo 클래스는 메인 키워드가 제외된 순수 보조 키워드를 담는 데이터 클래스입니다.
    """
    fixed_keywords: List[str] = field(default_factory=list)  # 고정 키워드가 맨 위로 이동
    use: List[str] = field(default_factory=list)
    spec: List[str] = field(default_factory=list)
    style: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)


@dataclass
class ProductInfo:
    """
    ProductInfo 클래스는 상품의 기본 정보와 최적화된 정보를 담고 있는 데이터 클래스입니다.

    Attributes:
        original_name (str): 원본 상품명.
        main_keyword (str): 상품의 메인 키워드.
        fixed_keywords (str): 고정 키워드.
        use (str): 상품의 용도.
        spec (str): 상품의 사양.
        style (str): 상품의 스타일.
        extra (str): 기타 카테고리에 해당하는 추가 정보.
    """
    original_name: str = ""
    main_keyword: str = ""
    fixed_keywords: str = ""  # 고정 키워드를 메인 키워드 아래로 이동
    use: str = ""
    spec: str = ""
    style: str = ""
    extra: str = ""


@dataclass
class ProcessedProductInfo(ProductInfo):
    """
    ProcessedProductInfo 클래스는 기본 상품 정보를 확장하여 여러 가공 상품명을 관리하는 데이터 클래스입니다.
    각 가공 유형별로 여러 상품명을 저장할 수 있습니다.
    
    Attributes:
        processed_names (Dict[str, List[str]]): 가공 타입별로 여러 상품명을 담는 딕셔너리.
    """
    
    processed_names: Dict[str, List[str]] = field(default_factory=dict)

    def get_processing_types(self) -> List[str]:
        """가공명 타입 목록을 반환합니다."""
        return list(self.processed_names.keys())

    def add_processed_name(self, processing_type: str, name: str):
        """특정 가공 타입에 가공된 상품명을 추가합니다."""
        if processing_type not in self.processed_names:
            self.processed_names[processing_type] = []
        self.processed_names[processing_type].append(name)

    

    def __str__(self):
        """객체를 문자열로 변환하여 출력할 때 기본 상품명, 메인 키워드, 가공 결과를 보기 좋게 반환합니다."""
        processed_str = "\n".join(
            f"{ptype}: {', '.join(names)}" for ptype, names in self.processed_names.items()
        )
        return (f"{self.original_name} -> {self.main_keyword}\n"
                f"고정 키워드: {self.fixed_keywords}, 용도: {self.use}, 사양: {self.spec}, "
                f"스타일: {self.style}, 기타: {self.extra}\n가공 결과:\n{processed_str}")
    
    def get_processed_names(self, processing_type: str) -> List[str]:
        """특정 가공 유형의 상품명을 반환합니다."""
        return self.processed_names.get(processing_type, [])
    
    def get_fixed_keywords(self) -> List[str]:
        if isinstance(self.fixed_keywords, list):
            keywords = self.fixed_keywords
        elif isinstance(self.fixed_keywords, str):
            keywords = self.fixed_keywords.split(",")  # 쉼표로 구분된 경우 분리
        else:
            keywords = []

        # 불필요한 공백 및 특수문자 제거
        return [kw.strip(",. ") for kw in keywords]

    def remove_processed_names(self, processing_type: str):
        """특정 가공 유형의 상품명을 제거합니다."""
        if processing_type in self.processed_names:
            del self.processed_names[processing_type]
