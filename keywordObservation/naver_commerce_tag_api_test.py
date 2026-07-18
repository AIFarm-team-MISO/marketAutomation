from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from keywordObservation.naver_tag_client import (
    NaverTagClient,
)


TEST_KEYWORD = "테이프"



def main() -> None:
    client = NaverTagClient()
    result = client.search_recommend_tags(TEST_KEYWORD)

    print(f"추천 태그 조회 키워드: {result['keyword']}")
    print(f"추천 태그 수: {result['result_count']}개")
    print(f"HTTP 상태: {result['status_code']}")
    print(f"Trace ID: {result['trace_id']}")

    for index, tag in enumerate(result["tags"], start=1):
        print(
            f"{index:>2}. "
            f"code={tag.get('code')} / "
            f"text={tag.get('text')}"
        )


if __name__ == "__main__":
    main()
