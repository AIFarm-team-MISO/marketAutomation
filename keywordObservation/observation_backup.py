from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


# =========================================================
# 직접 실행과 모듈 실행 모두 지원
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from keywordObservation.observation_integrity import (
    check_observation_file,
)

from keywordObservation.observation_store import (
    DATA_DIR,
    OBSERVATION_FILE,
    ObservationStoreError,
)


# =========================================================
# 백업 경로
# =========================================================

BACKUP_DIR = DATA_DIR / "backup"

BACKUP_FILE_PREFIX = (
    "naver_shopping_observations"
)


def _get_current_iso_datetime() -> str:
    """
    현재 지역 시간대가 포함된 ISO 날짜를 반환한다.
    """
    return (
        datetime.now()
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )


def _get_backup_timestamp() -> str:
    """
    백업 파일명에 사용할 날짜 문자열을 만든다.

    예:
        20260717_105500
    """
    return (
        datetime.now()
        .astimezone()
        .strftime("%Y%m%d_%H%M%S")
    )


def calculate_file_sha256(
    file_path: Path | str,
) -> str:
    """
    일반 파일의 SHA-256 해시를 계산한다.
    """
    target_path = Path(file_path)

    sha256 = hashlib.sha256()

    try:
        with target_path.open(
            mode="rb",
        ) as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(
                    chunk
                )

    except OSError as error:
        raise ObservationStoreError(
            (
                "파일 해시 계산에 실패했습니다: "
                f"{target_path}"
            )
        ) from error

    return sha256.hexdigest()


def calculate_gzip_content_sha256(
    file_path: Path | str,
) -> str:
    """
    gzip 파일을 압축 해제하면서
    내부 원본 내용의 SHA-256을 계산한다.
    """
    target_path = Path(file_path)

    sha256 = hashlib.sha256()

    try:
        with gzip.open(
            target_path,
            mode="rb",
        ) as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(
                    chunk
                )

    except (
        OSError,
        EOFError,
        gzip.BadGzipFile,
    ) as error:
        raise ObservationStoreError(
            (
                "압축 백업파일 검증에 실패했습니다: "
                f"{target_path}"
            )
        ) from error

    return sha256.hexdigest()


def _atomic_write_json(
    target_path: Path,
    data: dict[str, Any],
) -> None:
    """
    JSON 파일을 임시파일에 먼저 저장한 뒤
    최종 파일로 교체한다.
    """
    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path: Path | None = None

    try:
        file_descriptor, temporary_name = (
            tempfile.mkstemp(
                dir=target_path.parent,
                prefix=(
                    f".{target_path.stem}_"
                ),
                suffix=".tmp",
            )
        )

        os.close(
            file_descriptor
        )

        temporary_path = Path(
            temporary_name
        )

        with temporary_path.open(
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

            file.write("\n")
            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(
            temporary_path,
            target_path,
        )

    except (
        OSError,
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()

            except OSError:
                pass

        raise ObservationStoreError(
            (
                "백업정보 JSON 저장에 실패했습니다: "
                f"{target_path}"
            )
        ) from error


def _load_json_safely(
    file_path: Path,
) -> dict[str, Any] | None:
    """
    JSON 파일을 안전하게 읽는다.
    """
    if not file_path.exists():
        return None

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            loaded_data = json.load(
                file
            )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(
        loaded_data,
        dict,
    ):
        return None

    return loaded_data


def find_existing_backup_by_hash(
    source_sha256: str,
    backup_directory: Path | str = (
        BACKUP_DIR
    ),
) -> tuple[Path, Path] | None:
    """
    같은 원본 해시를 가진 기존 백업을 찾는다.

    Returns
    -------
    tuple | None
        백업 gzip 경로,
        백업정보 JSON 경로
    """
    target_directory = Path(
        backup_directory
    )

    if not target_directory.exists():
        return None

    for metadata_path in sorted(
        target_directory.glob(
            "*.meta.json"
        ),
        reverse=True,
    ):
        metadata = _load_json_safely(
            metadata_path
        )

        if metadata is None:
            continue

        saved_sha256 = str(
            metadata.get(
                "source_sha256",
                "",
            )
        ).strip()

        if saved_sha256 != source_sha256:
            continue

        backup_file_name = str(
            metadata.get(
                "backup_file_name",
                "",
            )
        ).strip()

        if not backup_file_name:
            continue

        backup_path = (
            target_directory
            / backup_file_name
        )

        if backup_path.exists():
            return (
                backup_path,
                metadata_path,
            )

    return None


def _write_gzip_backup(
    source_path: Path,
    backup_path: Path,
) -> None:
    """
    JSONL 파일을 gzip으로 압축해 저장한다.
    """
    backup_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path: Path | None = None

    try:
        file_descriptor, temporary_name = (
            tempfile.mkstemp(
                dir=backup_path.parent,
                prefix=(
                    f".{backup_path.stem}_"
                ),
                suffix=".tmp",
            )
        )

        os.close(
            file_descriptor
        )

        temporary_path = Path(
            temporary_name
        )

        with source_path.open(
            mode="rb",
        ) as source_file:
            with gzip.open(
                temporary_path,
                mode="wb",
                compresslevel=9,
            ) as backup_file:
                shutil.copyfileobj(
                    source_file,
                    backup_file,
                    length=1024 * 1024,
                )

        os.replace(
            temporary_path,
            backup_path,
        )

    except OSError as error:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()

            except OSError:
                pass

        raise ObservationStoreError(
            (
                "JSONL 압축 백업에 실패했습니다: "
                f"{backup_path}"
            )
        ) from error


def create_observation_backup(
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
    backup_directory: Path | str = (
        BACKUP_DIR
    ),
    force: bool = False,
    allow_integrity_errors: bool = False,
) -> dict[str, Any]:
    """
    관찰이력 JSONL을 gzip 파일로 백업한다.

    같은 내용의 백업이 이미 존재하면
    force=False일 때 새로 만들지 않는다.

    Parameters
    ----------
    file_path
        백업할 JSONL 파일.

    backup_directory
        백업파일 저장 폴더.

    force
        같은 내용의 백업이 있어도 새로 생성한다.

    allow_integrity_errors
        무결성 오류가 있어도 백업을 허용한다.
    """
    source_path = Path(
        file_path
    )

    target_directory = Path(
        backup_directory
    )

    if not source_path.exists():
        raise ObservationStoreError(
            (
                "백업할 관찰이력 파일이 없습니다: "
                f"{source_path}"
            )
        )

    try:
        source_size = (
            source_path.stat().st_size
        )

    except OSError as error:
        raise ObservationStoreError(
            (
                "관찰이력 파일 정보를 읽지 못했습니다: "
                f"{source_path}"
            )
        ) from error

    if source_size == 0:
        raise ObservationStoreError(
            (
                "관찰이력 파일이 비어 있어 "
                "백업을 생성하지 않습니다."
            )
        )

    # -----------------------------------------------------
    # 백업 전 무결성 검사
    # -----------------------------------------------------

    integrity_result = (
        check_observation_file(
            file_path=source_path
        )
    )

    error_count = int(
        integrity_result.get(
            "error_count",
            0,
        )
    )

    warning_count = int(
        integrity_result.get(
            "warning_count",
            0,
        )
    )

    if (
        error_count > 0
        and not allow_integrity_errors
    ):
        raise ObservationStoreError(
            (
                "무결성 검사에서 오류가 발견되어 "
                "백업을 중단했습니다. "
                f"오류 수: {error_count}"
            )
        )

    # -----------------------------------------------------
    # 원본 해시 계산
    # -----------------------------------------------------

    source_sha256 = (
        calculate_file_sha256(
            source_path
        )
    )

    # -----------------------------------------------------
    # 같은 내용의 백업 확인
    # -----------------------------------------------------

    if not force:
        existing_backup = (
            find_existing_backup_by_hash(
                source_sha256=(
                    source_sha256
                ),
                backup_directory=(
                    target_directory
                ),
            )
        )

        if existing_backup is not None:
            backup_path, metadata_path = (
                existing_backup
            )

            return {
                "created": False,
                "skipped_reason": (
                    "same_content_backup_exists"
                ),
                "source_path": str(
                    source_path
                ),
                "backup_path": str(
                    backup_path
                ),
                "metadata_path": str(
                    metadata_path
                ),
                "source_size_bytes": (
                    source_size
                ),
                "backup_size_bytes": (
                    backup_path.stat().st_size
                ),
                "source_sha256": (
                    source_sha256
                ),
                "integrity_error_count": (
                    error_count
                ),
                "integrity_warning_count": (
                    warning_count
                ),
            }

    # -----------------------------------------------------
    # 백업파일명 생성
    # -----------------------------------------------------

    target_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_timestamp = (
        _get_backup_timestamp()
    )

    hash_prefix = source_sha256[:12]

    backup_file_name = (
        f"{BACKUP_FILE_PREFIX}_"
        f"{backup_timestamp}_"
        f"{hash_prefix}.jsonl.gz"
    )

    backup_path = (
        target_directory
        / backup_file_name
    )

    metadata_path = (
        target_directory
        / (
            f"{BACKUP_FILE_PREFIX}_"
            f"{backup_timestamp}_"
            f"{hash_prefix}.meta.json"
        )
    )

    # -----------------------------------------------------
    # 압축 백업 생성
    # -----------------------------------------------------

    _write_gzip_backup(
        source_path=source_path,
        backup_path=backup_path,
    )

    # -----------------------------------------------------
    # 백업 내용 검증
    # -----------------------------------------------------

    backup_content_sha256 = (
        calculate_gzip_content_sha256(
            backup_path
        )
    )

    if (
        backup_content_sha256
        != source_sha256
    ):
        try:
            backup_path.unlink()

        except OSError:
            pass

        raise ObservationStoreError(
            (
                "백업파일 검증 결과 원본과 "
                "해시가 일치하지 않습니다."
            )
        )

    try:
        backup_size = (
            backup_path.stat().st_size
        )

    except OSError:
        backup_size = 0

    metadata = {
        "backup_version": "1.0",

        "created_at": (
            _get_current_iso_datetime()
        ),

        "source_path": str(
            source_path.resolve()
        ),

        "backup_file_name": (
            backup_file_name
        ),

        "source_size_bytes": (
            source_size
        ),

        "backup_size_bytes": (
            backup_size
        ),

        "source_sha256": (
            source_sha256
        ),

        "backup_content_sha256": (
            backup_content_sha256
        ),

        "integrity": {
            "is_healthy": bool(
                integrity_result.get(
                    "is_healthy",
                    False,
                )
            ),

            "record_count": int(
                integrity_result.get(
                    "record_count",
                    0,
                )
            ),

            "keyword_count": int(
                integrity_result.get(
                    "keyword_count",
                    0,
                )
            ),

            "error_count": (
                error_count
            ),

            "warning_count": (
                warning_count
            ),

            "schema_versions": (
                integrity_result.get(
                    "schema_versions",
                    {},
                )
            ),

            "status_counts": (
                integrity_result.get(
                    "status_counts",
                    {},
                )
            ),
        },
    }

    try:
        _atomic_write_json(
            target_path=metadata_path,
            data=metadata,
        )

    except ObservationStoreError:
        try:
            backup_path.unlink()

        except OSError:
            pass

        raise

    return {
        "created": True,
        "skipped_reason": "",
        "source_path": str(
            source_path
        ),
        "backup_path": str(
            backup_path
        ),
        "metadata_path": str(
            metadata_path
        ),
        "source_size_bytes": (
            source_size
        ),
        "backup_size_bytes": (
            backup_size
        ),
        "source_sha256": (
            source_sha256
        ),
        "integrity_error_count": (
            error_count
        ),
        "integrity_warning_count": (
            warning_count
        ),
    }


def print_backup_result(
    result: dict[str, Any],
) -> None:
    """
    백업결과를 콘솔에 출력한다.
    """
    print(
        "=" * 100
    )

    print(
        "네이버 쇼핑 관찰이력 백업"
    )

    print(
        "=" * 100
    )

    print(
        "원본 파일: "
        f"{result.get('source_path', '')}"
    )

    print(
        "원본 크기: "
        f"{int(result.get('source_size_bytes', 0)):,} bytes"
    )

    print(
        "원본 SHA-256: "
        f"{result.get('source_sha256', '')}"
    )

    print(
        "무결성 오류: "
        f"{int(result.get('integrity_error_count', 0))}"
    )

    print(
        "무결성 경고: "
        f"{int(result.get('integrity_warning_count', 0))}"
    )

    if result.get(
        "created"
    ):
        print(
            "처리 결과: 새 백업 생성"
        )

    else:
        print(
            "처리 결과: 동일한 내용의 백업이 이미 있어 생략"
        )

    print(
        "백업 파일: "
        f"{result.get('backup_path', '')}"
    )

    print(
        "백업정보 파일: "
        f"{result.get('metadata_path', '')}"
    )

    print(
        "압축 크기: "
        f"{int(result.get('backup_size_bytes', 0)):,} bytes"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "네이버 쇼핑 관찰이력 JSONL "
            "압축 백업"
        )
    )

    parser.add_argument(
        "--source",
        default=str(
            OBSERVATION_FILE
        ),
        help=(
            "백업할 JSONL 파일 경로"
        ),
    )

    parser.add_argument(
        "--backup-dir",
        default=str(
            BACKUP_DIR
        ),
        help=(
            "백업파일을 저장할 폴더"
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "동일한 내용의 백업이 있어도 "
            "새로 생성"
        ),
    )

    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help=(
            "무결성 오류가 있어도 백업 허용"
        ),
    )

    arguments = parser.parse_args()

    try:
        result = create_observation_backup(
            file_path=arguments.source,
            backup_directory=(
                arguments.backup_dir
            ),
            force=arguments.force,
            allow_integrity_errors=(
                arguments.allow_errors
            ),
        )

    except ObservationStoreError as error:
        print(
            f"[ERROR] {error}"
        )

        raise SystemExit(1)

    print_backup_result(
        result
    )


if __name__ == "__main__":
    main()