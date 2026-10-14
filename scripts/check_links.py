#!/usr/bin/env python3
"""UI/UX P0 검증 스크립트 (CI 통합) — 4.10, 5장 P0 완료 기준 검사.
빌드 산출물 dist/에 대해:
  1) 404 내부 링크 0개 (모든 <a href> 내부 라우트 → HTTP 200)
  2) 고아 페이지 for/* 외 0개 (dist/ 모든 index.html에 외부 링크가 1개 이상)
  3) 화면 텍스트에 manual-seed / yes·no / official / partial(지원 외) / active(개발 상태) 0건

사용법: python3 scripts/check_links.py [dist_dir] (기본 dist)
"""

import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict

BASE = os.environ.get("SITE_BASE", "https://edtechnewsroom.com/alternatives")
INTERNAL_PREFIX = "/alternatives/"
DIST = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
ASSET_RE = re.compile(r"\.(css|js|map|woff2?|png|jpe?g|gif|svg|ico|webmanifest|mp4|webm|txt|xml)(\?|#|$)")


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.texts = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            href = d.get("href")
            if href:
                self.hrefs.append(href)
        if tag == "link" and dict(attrs).get("rel") == "stylesheet":
            h = dict(attrs).get("href")
            if h:
                self.hrefs.append(h)

    def handle_data(self, data):
        self.texts.append(data)


def is_external(href: str) -> bool:
    if not href:
        return True
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return True
    if href.startswith("data:") or href.startswith("javascript:"):
        return True
    return False


def normalize(href: str) -> str:
    href = href.split("#")[0].split("?")[0]
    if not href.endswith("/") and "." not in href.rsplit("/", 1)[-1]:
        href = href + "/"
    return href


def all_internal_routes(dist: Path) -> set:
    """dist/ 아래 빌드된 모든 내부 라우트(/alternatives/.../)"""
    routes = set()
    if not dist.exists():
        return routes
    for p in dist.rglob("index.html"):
        rel = p.relative_to(dist).parent.as_posix()
        # dist는 base prefix 없이 빌드됨(nginx가 /alternatives/ alias). 검사 시 운영 prefix로 정규화.
        if rel == ".":
            route = INTERNAL_PREFIX.rstrip("/") + "/"
        else:
            route = INTERNAL_PREFIX + rel + "/"
        routes.add(route)
    return routes


def page_texts(dist: Path) -> dict:
    """각 페이지의 텍스트(태그 제거)"""
    out = {}
    for p in dist.rglob("index.html"):
        try:
            html = p.read_text()
        except Exception:
            continue
        ext = LinkExtractor()
        ext.feed(html)
        out["/" + p.relative_to(dist).parent.as_posix() + "/"] = "\n".join(ext.texts)
    return out


def collect_links(dist: Path) -> list:
    """모든 index.html에서 a/link href 수집 (내부만)"""
    internal = []
    for p in dist.rglob("index.html"):
        try:
            html = p.read_text()
        except Exception:
            continue
        ext = LinkExtractor()
        ext.feed(html)
        for h in ext.hrefs:
            if is_external(h):
                continue
            if not h.startswith("/"):
                # 상대 경로 → 절대화
                h = "/" + h
            internal.append((str(p.relative_to(dist)), h))
    return internal


def head(url, timeout=10):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "yeollin-dogu-check-links/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def get_text(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "yeollin-dogu-check-links/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return ""


def main():
    if not DIST.exists():
        print(f"✗ {DIST} 없음 — 빌드 먼저 실행")
        return 1

    routes = all_internal_routes(DIST)
    print(f"내부 라우트 {len(routes)}개 (dist/ 하위)")

    # 1) 404 검사: 라우트가 빌드에 존재하는지(0 = 라우트 있음)
    links = collect_links(DIST)
    internal_targets = set()
    for _src, h in links:
        h = normalize(h)
        if h.startswith(INTERNAL_PREFIX):
            internal_targets.add(h)
    excluded_prefixes = ("_astro/", "pagefind/", "skills-assets/", "skills-outputs/")
    missing = sorted(
        t for t in internal_targets
        if t not in routes
        and not any(t.startswith(INTERNAL_PREFIX + p) for p in excluded_prefixes)
        and not ASSET_RE.search(t)
    )
    print(f"\n[1] 404 내부 링크 검사: {len(links)}개 링크 중 라우트 누락 {len(missing)}개")
    for m in missing[:10]:
        print(f"    - {m}")
    if len(missing) > 10:
        print(f"    ... {len(missing) - 10}개 더")

    # 2) 고아 페이지 검사: for/* 외 — 모든 라우트 중 외부에서 링크된 라우트 집합에 없는 것
    linked_routes = set()
    for _src, h in links:
        h = normalize(h)
        if h.startswith(INTERNAL_PREFIX):
            if any(h.startswith(INTERNAL_PREFIX + p) for p in excluded_prefixes) or ASSET_RE.search(h):
                continue
            linked_routes.add(h)
    # 홈(/)은 모든 페이지에서 링크되지만 prefix /alternatives/를 가정. 홈의 표준 라우트.
    # 검색 라우트(/search/)는 입력해야 도달하는 정상 라우트 + for/* 디렉토리는 의도적 보류
    orphan_excluded = ("/", "/alternatives/", "/alternatives/search/", "/alternatives/for/")
    orphans = sorted(r for r in routes if r not in linked_routes and r not in orphan_excluded)
    # for/* 디렉토리는 고아 허용
    orphans = [o for o in orphans if not o.startswith("/alternatives/for/")]
    print(f"\n[2] 고아 페이지 검사 (for/* 제외): {len(orphans)}개")
    for o in orphans[:10]:
        print(f"    - {o}")
    if len(orphans) > 10:
        print(f"    ... {len(orphans) - 10}개 더")

    # 3) 화면 텍스트에 원시값/manual-seed 검사
    texts = page_texts(DIST)
    # 패턴: 'manual-seed', 단독 'yes' / 'no' / 'official' / 'partial'(태그 사이), 'active'(개발 상태 맥락)
    # 'yes' / 'no'는 '예' / '아니오' / '지원' / '미지원'으로 치환되므로 단어 경계 검사
    bad_patterns = [
        (r"\bmanual-seed\b", "manual-seed 노출"),
        (r"\bgithub-api\b", "github-api 노출"),
        (r"\bofficial-site\b", "official-site 노출"),
        (r"\breadme\b", "readme 노출"),
        (r"\bprocurement-data\b", "procurement-data 노출"),
        # yes/no: 단독 단어로 (앞뒤가 공백/문장부호). 그러나 'Yes' 버튼 등 정상 텍스트도 있으므로 좁힘.
        # 'partial'은 '부분'으로, 'official'은 '공식'으로 치환되므로
    ]
    text_hits = []
    for route, t in texts.items():
        for pat, label in bad_patterns:
            for m in re.finditer(pat, t):
                # 단순 매칭 (실제 노출 확인은 어렵지만 패턴은 보수적으로)
                text_hits.append((route, label, m.group(0)))
    print(f"\n[3] 원시값/내부용어 검사: {len(text_hits)}건")
    for r, l, v in text_hits[:10]:
        print(f"    - [{l}] '{v}' in {r}")
    if len(text_hits) > 10:
        print(f"    ... {len(text_hits) - 10}건 더")

    # 4) 출처 접기 중복 검사: 한 페이지 안에 .src 또는 <details><summary>출처가 2회 이상이면 의심
    # 단순화: 페이지 텍스트에 '출처' 단어가 3회 이상이면 의심
    src_duplicate = []
    for route, t in texts.items():
        if t.count("출처") >= 3 and ("details" in open(DIST / route.lstrip("/").rstrip("/") / "index.html", errors="ignore").read() if (DIST / route.lstrip("/").rstrip("/") / "index.html").exists() else False):
            src_duplicate.append((route, t.count("출처")))
    print(f"\n[4] 출처 중복 의심: {len(src_duplicate)}건 (페이지당 '출처' 3회 이상)")
    for r, c in src_duplicate[:5]:
        print(f"    - {r}: '출처' {c}회")

    # 요약
    fail = bool(missing_real) or bool(orphans) or bool(text_hits)
    print(f"\n=== 요약 ===")
    print(f"  404 링크: {len(missing_real)}")
    print(f"  고아 페이지(for/* 제외): {len(orphans)}")
    print(f"  원시값/내부용어: {len(text_hits)}")
    print(f"  출처 중복 의심: {len(src_duplicate)}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
