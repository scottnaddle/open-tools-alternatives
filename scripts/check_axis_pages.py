#!/usr/bin/env python3
"""4축(현장사례/수업지도안/심층리뷰) 콘텐츠 게이트 — src/content/{cases,lessons,reviews}/*.json
위반 시 exit 1로 CI/빌드 실패. 규칙 근거: ops/RESEARCH.md 4절 + AGENTS.md 원칙 1·2 (출처 강제).
허용 method: skills/tools와 일치."""

import json
import re
import sys
from pathlib import Path

ALLOWED_METHODS = {
    "github-api", "release-assets", "official-site", "readme",
    "procurement-data", "manual-seed",
}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)$")


def check(path: Path, kind: str) -> list[str]:
    errors = []
    try:
        d = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{kind}/{path.name}: JSON 파싱 실패 ({e})"]
    slug = path.stem

    # 공통
    if not d.get("title"):
        errors.append(f"{kind}/{slug}: title 없음")
    if not DATE.match(d.get("dateChecked") or ""):
        errors.append(f"{kind}/{slug}: dateChecked가 YYYY-MM-DD 형식 아님: {d.get('dateChecked')}")
    if not DATETIME.match(d.get("fetchedAt") or ""):
        errors.append(f"{kind}/{slug}: fetchedAt가 ISO datetime 형식 아님: {d.get('fetchedAt')}")

    src = d.get("sourceUrl") or ""
    if not (src.startswith("http://") or src.startswith("https://")):
        errors.append(f"{kind}/{slug}: sourceUrl이 http(s)로 시작하지 않음")
    m = d.get("sourceMethod")
    if m not in ALLOWED_METHODS:
        errors.append(f"{kind}/{slug}: sourceMethod '{m}'이 허용 목록에 없음 (수동 게시: manual-seed만 가능, 그 외 verified 불가)")

    # example=true면 "예시 데이터" 배지 강제 (솔직한 한계 원칙)
    if d.get("example") and "예시 데이터" not in (d.get("badges") or []):
        errors.append(f"{kind}/{slug}: example=true인데 badges에 '예시 데이터' 없음 — 솔직한 한계 원칙(AGENTS.md 2)")

    # tool.sourceUrl 일치
    tool = d.get("tool") or {}
    if tool.get("sourceUrl") and tool["sourceUrl"] != src:
        errors.append(f"{kind}/{slug}: tool.sourceUrl과 sourceUrl 불일치")

    # kind별
    if kind in ("cases", "lessons"):
        for k in ("grade", "unit", "schoolContext", "summary"):
            if not d.get(k):
                errors.append(f"{kind}/{slug}: {k} 없음")
    if kind == "lessons":
        if not d.get("duration"):
            errors.append(f"{kind}/{slug}: duration 없음 (예: '40분')")
    if kind == "reviews":
        if not (tool.get("license") or "").strip():
            errors.append(f"{kind}/{slug}: tool.license 없음 — 심층리뷰는 라이선스 표기 필수")

    return errors


def main() -> int:
    all_errors = []
    counts = {}
    for kind in ("cases", "lessons", "reviews"):
        d = Path(f"src/content/{kind}")
        if not d.exists():
            continue
        files = sorted(d.glob("*.json"))
        counts[kind] = len(files)
        for f in files:
            all_errors.extend(check(f, kind))
    if all_errors:
        print("❌ 4축 페이지 게이트 위반:")
        for e in all_errors:
            print(f"  - {e}")
        print(f"\n총 {len(all_errors)}건. 규칙: AGENTS.md 원칙 1·2. 데이터 수정 후 다시 실행하세요.")
        return 1
    total = sum(counts.values())
    parts = ", ".join(f"{k} {v}개" for k, v in counts.items() if v)
    print(f"✓ 4축 페이지 게이트 검증 통과 ({total}개 — {parts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
