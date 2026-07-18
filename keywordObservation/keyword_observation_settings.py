from __future__ import annotations

import json
from typing import Any

from keywordObservation.keyword_observation_paths import (
    SETTINGS_FILE,
)


DEFAULT_SETTINGS: dict[str, Any] = {
    "settings_version": "1.0",
    "api_collection_enabled": True,
    "display_count": 20,
    "default_sort": "sim",
    "keyword_column": "키워드",
    "supported_excel_extensions": [
        ".xlsx",
        ".xls",
        ".xlsm",
    ],
    "skip_existing_on_dictionary_add": True,
    "bulk_collection_delay_seconds": 0.5,
    "bulk_output_mode": "compact",
}


class KeywordObservationSettingsError(
    RuntimeError
):
    pass


def _write_default_settings() -> None:
    SETTINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SETTINGS_FILE.write_text(
        json.dumps(
            DEFAULT_SETTINGS,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_keyword_observation_settings(
) -> dict[str, Any]:
    """
    data/keyword_observation_settings.json을 읽고
    누락된 값에는 기본값을 적용한다.
    """
    if not SETTINGS_FILE.exists():
        _write_default_settings()

    try:
        loaded = json.loads(
            SETTINGS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise KeywordObservationSettingsError(
            (
                "키워드 관찰사전 설정파일을 "
                f"읽지 못했습니다: {error}"
            )
        ) from error

    if not isinstance(
        loaded,
        dict,
    ):
        raise KeywordObservationSettingsError(
            "설정파일의 최상위 값은 JSON 객체여야 합니다."
        )

    settings = dict(
        DEFAULT_SETTINGS
    )

    settings.update(
        loaded
    )

    try:
        settings[
            "display_count"
        ] = max(
            1,
            int(
                settings.get(
                    "display_count",
                    20,
                )
            ),
        )

        settings[
            "bulk_collection_delay_seconds"
        ] = max(
            0.0,
            float(
                settings.get(
                    "bulk_collection_delay_seconds",
                    0.5,
                )
            ),
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise KeywordObservationSettingsError(
            (
                "설정파일의 숫자값 형식이 "
                f"올바르지 않습니다: {error}"
            )
        ) from error

    settings[
        "api_collection_enabled"
    ] = bool(
        settings.get(
            "api_collection_enabled",
            True,
        )
    )

    settings[
        "skip_existing_on_dictionary_add"
    ] = bool(
        settings.get(
            "skip_existing_on_dictionary_add",
            True,
        )
    )

    settings[
        "keyword_column"
    ] = str(
        settings.get(
            "keyword_column",
            "키워드",
        )
    ).strip() or "키워드"

    settings[
        "default_sort"
    ] = str(
        settings.get(
            "default_sort",
            "sim",
        )
    ).strip() or "sim"

    extensions = settings.get(
        "supported_excel_extensions",
        [
            ".xlsx",
            ".xls",
            ".xlsm",
        ],
    )

    if not isinstance(
        extensions,
        list,
    ):
        extensions = [
            ".xlsx",
            ".xls",
            ".xlsm",
        ]

    settings[
        "supported_excel_extensions"
    ] = [
        (
            extension
            if str(
                extension
            ).startswith(".")
            else "." + str(
                extension
            )
        ).lower()
        for extension in extensions
        if str(
            extension
        ).strip()
    ]

    return settings
