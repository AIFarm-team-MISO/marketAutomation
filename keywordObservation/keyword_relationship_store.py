from __future__ import annotations

import json
from typing import Any

from keywordObservation.keyword_observation_paths import (
    KEYWORD_RELATIONSHIPS_FILE,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
)


DEFAULT_KEYWORD_RELATIONSHIPS = {
    "version": "1.0",
    "description": (
        "키워드의 별칭·상위키워드·관련키워드를 수동으로 관리합니다. "
        "문자열 포함만으로 자동 관계를 만들지 않습니다."
    ),
    "relationships": {},
}



def ensure_keyword_relationships_file() -> None:
    if KEYWORD_RELATIONSHIPS_FILE.exists():
        return

    KEYWORD_RELATIONSHIPS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    KEYWORD_RELATIONSHIPS_FILE.write_text(
        json.dumps(
            DEFAULT_KEYWORD_RELATIONSHIPS,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )



def load_keyword_relationships() -> dict[str, Any]:
    ensure_keyword_relationships_file()

    try:
        loaded = json.loads(
            KEYWORD_RELATIONSHIPS_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_KEYWORD_RELATIONSHIPS)

    if not isinstance(loaded, dict):
        return dict(DEFAULT_KEYWORD_RELATIONSHIPS)

    return loaded



def resolve_keyword_scope(
    keyword: str,
) -> dict[str, Any]:
    normalized = normalize_keyword(keyword)
    loaded = load_keyword_relationships()
    relationships = loaded.get("relationships", {})

    if not isinstance(relationships, dict):
        relationships = {}

    canonical = normalized
    relation = relationships.get(canonical, {})

    if not isinstance(relation, dict):
        relation = {}

    if not relation:
        for candidate, candidate_relation in relationships.items():
            if not isinstance(candidate_relation, dict):
                continue

            aliases = [
                normalize_keyword(alias)
                for alias in candidate_relation.get("aliases", [])
            ]

            if normalized.casefold() in {
                alias.casefold()
                for alias in aliases
            }:
                canonical = normalize_keyword(candidate)
                relation = candidate_relation
                break

    return {
        "input_keyword": normalized,
        "canonical_keyword": canonical,
        "aliases": [
            normalize_keyword(value)
            for value in relation.get("aliases", [])
            if normalize_keyword(value)
        ],
        "parent_keyword": normalize_keyword(
            relation.get("parent_keyword", "")
        ),
        "related_keywords": [
            normalize_keyword(value)
            for value in relation.get("related_keywords", [])
            if normalize_keyword(value)
        ],
    }
