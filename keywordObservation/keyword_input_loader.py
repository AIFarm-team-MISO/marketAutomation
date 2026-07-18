from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from keywordObservation.keyword_observation_paths import (
    KEYWORD_INPUT_DIR,
)


class KeywordInputLoaderError(
    RuntimeError
):
    pass


def _normalize_keyword(
    value: Any,
) -> str:
    return " ".join(
        str(value).split()
    )


def _normalize_header(
    value: Any,
) -> str:
    return " ".join(
        str(value).split()
    )


def find_keyword_excel_files(
    *,
    input_directory: Path = (
        KEYWORD_INPUT_DIR
    ),
    supported_extensions: list[str] | None = None,
) -> list[Path]:
    extensions = {
        extension.lower()
        for extension in (
            supported_extensions
            or [
                ".xlsx",
                ".xls",
                ".xlsm",
            ]
        )
    }

    input_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    result: list[Path] = []

    for path in sorted(
        input_directory.iterdir(),
        key=lambda item: (
            item.name.casefold()
        ),
    ):
        if not path.is_file():
            continue

        if path.name.startswith(
            "~$"
        ):
            continue

        if path.suffix.lower() not in (
            extensions
        ):
            continue

        result.append(path)

    return result


def load_keywords_from_input_folder(
    *,
    input_directory: Path = (
        KEYWORD_INPUT_DIR
    ),
    keyword_column: str = "키워드",
    supported_extensions: list[str] | None = None,
) -> dict[str, Any]:
    """
    data/keyword_inputs 폴더의 모든 엑셀파일에서
    첫 번째 시트와 '키워드' 열만 읽는다.

    파일 간 중복도 제거하며 최초로 발견된 표기를 유지한다.
    """
    normalized_column = (
        _normalize_header(
            keyword_column
        )
    )

    files = find_keyword_excel_files(
        input_directory=(
            input_directory
        ),
        supported_extensions=(
            supported_extensions
        ),
    )

    result: dict[str, Any] = {
        "input_directory": str(
            input_directory
        ),
        "files_found": [
            str(path)
            for path in files
        ],
        "readable_files": [],
        "missing_column_files": [],
        "read_errors": [],
        "total_rows": 0,
        "blank_rows": 0,
        "duplicate_rows": 0,
        "keywords": [],
        "sources_by_keyword": {},
    }

    seen_keys: set[str] = set()

    for path in files:
        try:
            dataframe = pd.read_excel(
                path,
                sheet_name=0,
                dtype=object,
            )

        except Exception as error:
            result[
                "read_errors"
            ].append(
                {
                    "file": str(path),
                    "error": str(error),
                }
            )
            continue

        normalized_headers = {
            _normalize_header(
                column
            ): column
            for column in dataframe.columns
        }

        actual_column = (
            normalized_headers.get(
                normalized_column
            )
        )

        if actual_column is None:
            result[
                "missing_column_files"
            ].append(
                str(path)
            )
            continue

        result[
            "readable_files"
        ].append(
            str(path)
        )

        values = dataframe[
            actual_column
        ].tolist()

        result[
            "total_rows"
        ] += len(values)

        for value in values:
            if pd.isna(value):
                result[
                    "blank_rows"
                ] += 1
                continue

            keyword = (
                _normalize_keyword(
                    value
                )
            )

            if not keyword:
                result[
                    "blank_rows"
                ] += 1
                continue

            duplicate_key = (
                keyword.casefold()
            )

            if duplicate_key in seen_keys:
                result[
                    "duplicate_rows"
                ] += 1

                for stored_keyword in result[
                    "keywords"
                ]:
                    if (
                        stored_keyword.casefold()
                        != duplicate_key
                    ):
                        continue

                    source_paths = result[
                        "sources_by_keyword"
                    ].setdefault(
                        stored_keyword,
                        [],
                    )

                    if str(path) not in (
                        source_paths
                    ):
                        source_paths.append(
                            str(path)
                        )

                    break

                continue

            seen_keys.add(
                duplicate_key
            )

            result[
                "keywords"
            ].append(
                keyword
            )

            result[
                "sources_by_keyword"
            ][
                keyword
            ] = [
                str(path)
            ]

    return result
