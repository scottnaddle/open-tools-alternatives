#!/usr/bin/env python3
"""UI/UX P0 검증 스크립트 (CI 통합).
빌드 산출물 dist/에 대해 실패(exit 1):
  1) 내부 링크 404
  2) 고아 페이지 (for/* 제외)
  3) 보이는 원시값·내부 용어 (tools/compare/apps/changes 포함)
  4) 같은 섹션 안의 출처 접기 중복
  5) 자리표시 '주요 기능 1'
  6) example 4축·'예시 데이터'·확인 단정 문구·'반영 여부를 알려' 공개
  7) 피드: new/update만, 별 수·버전·확인 시각 제외, guid·페이지 주소·한두 줄 요약

사용법: python3 scripts/check_links.py [dist_dir] (기본 dist)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

BASE = os.environ.get("SITE_BASE", "https://edtechnewsroom.com/alternatives")
INTERNAL_PREFIX = "/alternatives/"
ROOT = Path(__file__).resolve().parents[1]
DIST = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
# src/pages/feed.xml.ts 의 NOISE 판정과 같게 유지한다.
NOISE_FIELDS = {"stars", "lastPush", "latestRelease", "fetchedAt", "dateChecked", "createdAt"}
ASSET_RE = re.compile(r"\.(css|js|map|woff2?|png|jpe?g|webp|gif|svg|ico|webmanifest|mp4|webm|txt|xml)(\?|#|$)")


class LinkExtractor(HTMLParser):
    """보이는 텍스트만 모은다. script/style과 출처 인용문(details.src 안의 긴 발췌)은 따로 표시."""

    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.texts = []
        self._skip = 0
        self._src_depth = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        if tag == "details" and "src" in (d.get("class") or "").split():
            self._src_depth += 1
        if tag == "a":
            href = d.get("href")
            if href:
                self.hrefs.append(href)
        if tag == "link" and d.get("rel") == "stylesheet":
            h = d.get("href")
            if h:
                self.hrefs.append(h)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
        if tag == "details" and self._src_depth:
            self._src_depth -= 1

    def handle_data(self, data):
        if self._skip:
            return
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


# readme는 GitHub URL의 #readme 앵커에 그대로 있으므로, # 나 / 바로 뒤는 제외한다.
INTERNAL_RE = re.compile(
    r"\b(manual-seed|github-api|official-site|release-assets|procurement-data)\b|(?<![#/\w])readme(?!\w)"
)
ENUM_RE = re.compile(r"(?<![A-Za-z0-9-])(yes|no|official|partial|active)(?![A-Za-z0-9-])")
PLACEHOLDER_RE = re.compile(r"주요 기능\s*\d+")
PROMISE_RE = re.compile(r"반영 여부를 알려")
EXAMPLE_LABEL = "예시 데이터"
FALSE_CLAIM = "모든 값은 원 출처로 확인한 사실"


def visible_text(html: str) -> str:
    ext = LinkExtractor()
    ext.feed(html)
    return "\n".join(ext.texts)


def raw_value_hits(text: str) -> list[tuple[str, str]]:
    """내부 토큰은 어디서든, yes/no/official/partial/active는 값으로 보일 때만.

    출처 발췌처럼 'official website'가 문장 안에 있는 경우는 원문 인용이므로 빼지 않는다.
    한 텍스트 덩어리가 4단어 미만일 때만 enum을 본다.
    """
    hits = []
    for chunk in text.split("\n"):
        piece = chunk.strip()
        if not piece:
            continue
        for m in INTERNAL_RE.finditer(piece):
            hits.append((m.group(1) or m.group(0), "내부 용어"))
        if len(piece.split()) >= 4:
            continue
        for m in ENUM_RE.finditer(piece):
            hits.append((m.group(1), "원시값"))
    return hits


SECTION_TAGS = {"tr", "td", "li", "article", "section", "p"}
VOID_TAGS = {"link", "meta", "img", "br", "input", "hr", "source", "area", "base", "col", "embed", "wbr"}


class SourceSectionParser(HTMLParser):
    """섹션(tr/td/li/article/section/p) 안에 details.src가 2개 이상이면 중복.

    HTMLParser는 void 태그(<link>, <br>)를 닫지 않으므로, 스택은 짝이 맞는 태그만 쌓는다.
    """

    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, int | None]] = []
        self.seq = 0
        self.counts: dict[int, int] = {}
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        if tag in ("script", "style"):
            self._skip += 1
        section_id = None
        if tag in SECTION_TAGS:
            self.seq += 1
            section_id = self.seq
            self.counts[section_id] = 0
        self.stack.append((tag, section_id))
        if self._skip:
            return
        d = dict(attrs)
        if tag == "details" and "src" in (d.get("class") or "").split():
            for _tag, sid in reversed(self.stack):
                if sid is not None:
                    self.counts[sid] += 1
                    break

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_startendtag(self, tag, attrs):
        return


def duplicate_source_sections(html: str) -> int:
    parser = SourceSectionParser()
    parser.feed(html)
    return sum(1 for n in parser.counts.values() if n >= 2)


def example_axis_entries() -> list[tuple[str, str, bool]]:
    """(kind, title, example) — example 기본값은 true."""
    rows = []
    for kind in ("cases", "lessons", "reviews"):
        folder = Path(f"src/content/{kind}")
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            rows.append((kind, data.get("title") or "", bool(data.get("example", True))))
    return rows


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

    # 3) 원시값 — 도구·비교·앱·변경 이력을 포함한 정식 페이지. script/style은 제외.
    #    예전 검사는 /tools/ 와 /changes/ 를 빼서 inkscape의 active, 변경 이력의 github-api를 놓쳤다.
    text_hits = []
    placeholder_hits = []
    promise_hits = []
    example_label_hits = []
    false_claim_hits = []
    html_by_route = {}
    for p in DIST.rglob("index.html"):
        rel = p.relative_to(DIST).as_posix()
        if rel.startswith("pagefind/") or "/pagefind/" in rel:
            continue
        html = p.read_text(errors="ignore")
        route = "/" + str(p.relative_to(DIST).parent.as_posix()) + "/"
        if route == "/./":
            route = "/"
        html_by_route[route] = html
        text = visible_text(html)
        for token, label in raw_value_hits(text):
            text_hits.append((route, label, token))
        if PLACEHOLDER_RE.search(text):
            placeholder_hits.append(route)
        if PROMISE_RE.search(text):
            promise_hits.append(route)
        if EXAMPLE_LABEL in text:
            example_label_hits.append(route)
        if FALSE_CLAIM in text:
            false_claim_hits.append(route)
    print(f"\n[3] 원시값/내부용어 검사: {len(text_hits)}건 (tools·compare·apps·changes 포함)")
    for r, l, v in text_hits[:12]:
        print(f"    - [{l}] '{v}' in {r}")
    if len(text_hits) > 12:
        print(f"    ... {len(text_hits) - 12}건 더")

    # 4) 출처 접기 중복: 같은 섹션(tr/li/article/section) 안에 details.src가 2개 이상.
    #    /changes/ 처럼 변경마다 출처가 하나인 목록은 통과한다. '출처' 단어 횟수는 세지 않는다.
    src_duplicate = []
    for route, html in html_by_route.items():
        n = duplicate_source_sections(html)
        if n:
            src_duplicate.append((route, n))
    print(f"\n[4] 출처 접기 중복(섹션당 2개 이상): {len(src_duplicate)}건")
    for r, c in src_duplicate[:8]:
        print(f"    - {r}: {c}개 섹션")

    print(f"\n[5] 자리표시 '주요 기능 N': {len(placeholder_hits)}건")
    for r in placeholder_hits[:8]:
        print(f"    - {r}")

    # 6) example:true 4축은 공개 빌드에 없다. 비어 있으면 /cases 등 메뉴 링크도 없다.
    axis = example_axis_entries()
    leaked_titles = []
    empty_axis_links = []
    built_empty_axis = []
    for kind, title, is_example in axis:
        if not is_example or not title:
            continue
        for route, html in html_by_route.items():
            if title in visible_text(html):
                leaked_titles.append((kind, title, route))
    public_by_kind = {}
    for kind in ("cases", "lessons", "reviews"):
        rows = [row for row in axis if row[0] == kind]
        public_by_kind[kind] = any(not row[2] for row in rows) if rows else False
        built = (DIST / kind).exists()
        if built and rows and not public_by_kind[kind]:
            built_empty_axis.append(kind)
    axis_href = re.compile(r"/alternatives/(cases|lessons|reviews)/")
    for route, html in html_by_route.items():
        ext = LinkExtractor()
        ext.feed(html)
        for href in ext.hrefs:
            m = axis_href.search(href if href.startswith("/") else "/" + href)
            if not m:
                continue
            kind = m.group(1)
            if not public_by_kind.get(kind):
                empty_axis_links.append((route, href))
    print(f"\n[6] 예시 4축 공개 노출: 제목 {len(leaked_titles)} · 빈 축 링크 {len(empty_axis_links)} · 빈 축 빌드 {len(built_empty_axis)}")
    for kind, title, route in leaked_titles[:6]:
        print(f"    - {kind} '{title}' in {route}")
    print(f"\n[7] '예시 데이터' 라벨: {len(example_label_hits)} · 확인 사실 단정 문구: {len(false_claim_hits)} · '반영 여부를 알려': {len(promise_hits)}")

    # 8) 검색 노출: 페이지마다 제목·설명·canonical·OG 이미지, 피드·사이트맵·robots.
    seo_miss = []
    og_missing = []
    canon_miss = []
    title_re = re.compile(r"<title>([^<]*)</title>")
    desc_re = re.compile(r'<meta name="description" content="([^"]*)"')
    canon_re = re.compile(r'<link rel="canonical" href="([^"]+)"')
    og_re = re.compile(r'<meta property="og:image" content="([^"]+)"')
    for p in DIST.rglob("index.html"):
        rel = p.relative_to(DIST).as_posix()
        if rel.startswith("pagefind/") or "/pagefind/" in rel:
            continue
        html = p.read_text(errors="ignore")
        parent = p.relative_to(DIST).parent.as_posix()
        route = INTERNAL_PREFIX if parent == "." else INTERNAL_PREFIX + parent + "/"
        title = title_re.search(html)
        desc = desc_re.search(html)
        canon = canon_re.search(html)
        og = og_re.search(html)
        if not title or not title.group(1).strip() or not desc or not desc.group(1).strip() or not canon or not og:
            seo_miss.append(route)
            continue
        if canon.group(1) != BASE.rstrip("/") + route and canon.group(1) != BASE + route.removeprefix(INTERNAL_PREFIX):
            # BASE 는 https://edtechnewsroom.com/alternatives (끝 슬래시 없음일 수 있음)
            expected = "https://edtechnewsroom.com" + route
            if canon.group(1) != expected:
                canon_miss.append((route, canon.group(1), expected))
        og_path = og.group(1).split("?")[0]
        if og_path.startswith("https://edtechnewsroom.com/alternatives/"):
            rel_file = og_path.removeprefix("https://edtechnewsroom.com/alternatives/")
            if not (DIST / rel_file).is_file():
                og_missing.append(rel_file)
    feed_problems = check_feed()
    feed_ok = not feed_problems
    sitemap_ok = (DIST / "sitemap-index.xml").is_file()
    robots_ok = (DIST / "robots.txt").is_file()
    print(f"\n[8] SEO: 메타 빠짐 {len(seo_miss)} · canonical {len(canon_miss)} · OG 파일 {len(og_missing)} · feed 문제 {len(feed_problems)} · sitemap {sitemap_ok} · robots {robots_ok}")
    for problem in feed_problems[:12]:
        print(f"    - feed {problem}")
    for r in seo_miss[:8]:
        print(f"    - meta {r}")
    for r, got, exp in canon_miss[:8]:
        print(f"    - canonical {r}: {got} != {exp}")
    for r in og_missing[:8]:
        print(f"    - og {r}")

    fail = bool(missing) or bool(orphans) or bool(text_hits) or bool(src_duplicate) or bool(placeholder_hits)
    fail = fail or bool(leaked_titles) or bool(empty_axis_links) or bool(built_empty_axis)
    fail = fail or bool(example_label_hits) or bool(false_claim_hits) or bool(promise_hits)
    fail = fail or bool(seo_miss) or bool(canon_miss) or bool(og_missing) or not feed_ok or not sitemap_ok or not robots_ok
    print(f"\n=== 요약 ===")
    print(f"  404 링크: {len(missing)}")
    print(f"  고아 페이지(for/* 제외): {len(orphans)}")
    print(f"  원시값/내부용어: {len(text_hits)}")
    print(f"  출처 접기 중복 섹션: {len(src_duplicate)}")
    print(f"  자리표시: {len(placeholder_hits)}")
    print(f"  예시 4축 노출: {len(leaked_titles) + len(empty_axis_links) + len(built_empty_axis)}")
    print(f"  예시 데이터 라벨: {len(example_label_hits)}")
    print(f"  SEO 메타/canonical/OG: {len(seo_miss) + len(canon_miss) + len(og_missing)}")
    return 1 if fail else 0


def _num(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return isinstance(value, str) and re.fullmatch(r"-?\d+(\.\d+)?", value.strip()) is not None


def _date(value):
    return isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}(T[\d:.+Z-]+)?", value.strip()) is not None


def _release(value):
    return isinstance(value, dict) and "tag" in value


def _version(value):
    return isinstance(value, str) and re.match(r"v?\d+\.\d+", value.strip()) is not None


def change_is_noise(field, before, after):
    last = field.split(".")[-1]
    if last in NOISE_FIELDS:
        return True
    if _num(before) and _num(after):
        return True
    if _date(before) and _date(after):
        return True
    if _release(before) or _release(after):
        return True
    if _version(before) and _version(after):
        return True
    return False


def git_added_at(rel):
    out = subprocess.check_output(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", rel],
        cwd=ROOT,
        text=True,
    ).strip()
    lines = [line for line in out.splitlines() if line.strip()]
    if not lines:
        return None
    return datetime.fromisoformat(lines[-1])


def check_feed():
    """소셜 피드 규격. 문제 문자열 목록을 반환한다."""
    problems = []
    path = DIST / "feed.xml"
    if not path.is_file():
        return ["feed.xml 없음"]
    root = ET.parse(path).getroot()
    channel = root.find("channel")
    if channel is None:
        return ["feed.xml channel 없음"]
    items = channel.findall("item")
    seen = {}
    origin = "https://edtechnewsroom.com/alternatives/"

    def page_file(link):
        if not link.startswith(origin):
            return None
        rel = link[len(origin):]
        if not rel.endswith("/"):
            return None
        return DIST / rel / "index.html"

    for item in items:
        guid = (item.findtext("guid") or "").strip()
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        cats = [(c.text or "").strip() for c in item.findall("category")]
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not link or not desc or not guid or not pub:
            problems.append(f"필드 빠짐 {guid or title or link}")
            continue
        if cats != ["new"] and cats != ["update"]:
            problems.append(f"category {guid}: {cats}")
        if guid in seen:
            problems.append(f"guid 중복 {guid}")
        seen[guid] = pub
        if not guid.startswith(("new:tool:", "new:skill:", "new:app:", "update:")):
            problems.append(f"guid 형식 {guid}")
        if (guid.startswith("new:") and cats != ["new"]) or (guid.startswith("update:") and cats != ["update"]):
            problems.append(f"guid와 category 불일치 {guid} {cats}")
        if "\n" in desc or len(desc) > 200:
            problems.append(f"요약이 한두 줄을 넘음 {guid} ({len(desc)})")
        dest = page_file(link)
        if dest is None or not dest.is_file():
            problems.append(f"페이지 없음 {link}")
        try:
            parsedate_to_datetime(pub)
        except (TypeError, ValueError):
            problems.append(f"날짜 해석 실패 {guid}")

    expected = {}
    for folder, kind in (("tools", "tool"), ("skills", "skill"), ("school-apps", "app")):
        for file in (ROOT / "src" / "content" / folder).glob("*.json"):
            data = json.loads(file.read_text())
            if kind == "skill":
                key = data["slug"]
            else:
                key = file.stem
            expected[f"new:{kind}:{key}"] = f"src/content/{folder}/{file.name}"
    for guid, rel in expected.items():
        if guid not in seen:
            problems.append(f"새 페이지 빠짐 {guid}")
            continue
        added = git_added_at(rel)
        if added is None:
            problems.append(f"추가 커밋 없음 {rel} (fetch-depth: 0)")
            continue
        try:
            published = parsedate_to_datetime(seen[guid])
        except (TypeError, ValueError):
            continue
        if abs(published.timestamp() - added.timestamp()) > 2:
            problems.append(f"new 날짜가 추가 커밋과 다름 {guid}")

    # 피드는 빌드 때 커밋된 변경만 넣는다. verify.py 는 그 다음 CI 단계에서
    # 라이선스 차이 같은 새 변경 기록을 작업 트리에 쓴다. 그 파일은 피드에 없으므로 실패로 보지 않는다.
    tracked = subprocess.check_output(
        ["git", "ls-files", "--", "src/content/changes"],
        cwd=ROOT,
        text=True,
    )
    change_files = [ROOT / line.strip() for line in tracked.splitlines() if line.strip().endswith(".json")]
    records = []
    for file in change_files:
        data = json.loads(file.read_text())
        target = data.get("target", "")
        slash = target.find("/")
        dot = target.find(".")
        if slash < 0 or dot < slash:
            continue
        kind, cid, field = target[:slash], target[slash + 1:dot], target[dot + 1:]
        page_exists = False
        if kind == "tools":
            page_exists = (ROOT / "src" / "content" / "tools" / f"{cid}.json").is_file()
        elif kind == "skills":
            page_exists = (ROOT / "src" / "content" / "skills" / f"{cid}.json").is_file()
        try:
            at = datetime.fromisoformat(data["at"])
        except (TypeError, ValueError):
            continue
        records.append((at, file.stem, target, field, data.get("before"), data.get("after"), page_exists))
    records.sort(key=lambda row: (row[0], row[1]))
    kept = set()
    for at, stem, target, field, before, after, page_exists in records:
        guid = f"update:{stem}"
        noise = change_is_noise(field, before, after)
        fingerprint = (target, json.dumps(before, sort_keys=True, ensure_ascii=False), json.dumps(after, sort_keys=True, ensure_ascii=False))
        duplicate = fingerprint in kept
        if not noise and page_exists and not duplicate:
            kept.add(fingerprint)
            if guid not in seen:
                problems.append(f"내용 변경 빠짐 {guid} ({target})")
        elif guid in seen:
            problems.append(f"숫자·날짜·중복 변경이 피드에 있음 {guid} ({target})")
    return problems


if __name__ == "__main__":
    sys.exit(main())
