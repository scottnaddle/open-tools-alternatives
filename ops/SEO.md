# 검색 노출 — 소유자가 할 일

사이트 주소는 `https://edtechnewsroom.com/alternatives/` 입니다. 페이지 제목, 설명, canonical, Open Graph, JSON-LD, 사이트맵, 피드는 빌드에 들어 있습니다. 아래는 저장소 밖에서 소유자가 한 번 해 주는 일입니다.

피드 주소: `https://edtechnewsroom.com/alternatives/feed.xml`  
사이트맵: `https://edtechnewsroom.com/alternatives/sitemap-index.xml`

## 1. 도메인 루트 robots.txt

Google, Naver, Daum은 `https://edtechnewsroom.com/robots.txt` 만 읽습니다. `/alternatives/robots.txt` 는 배포되지만 검색엔진의 공식 robots 파일이 아닙니다.

뉴스룸 루트 robots.txt를 **지우지 말고** 아래를 덧붙입니다. 이미 `Disallow: /` 가 있으면 `/alternatives/` 가 같이 막히므로, 그 아래에 Allow를 넣습니다.

```
User-agent: *
Allow: /alternatives/

User-agent: Yeti
Allow: /alternatives/

User-agent: Daum
Allow: /alternatives/

Sitemap: https://edtechnewsroom.com/alternatives/sitemap-index.xml
```

`Yeti`는 네이버 수집 로봇, `Daum`은 다음 수집 로봇 이름입니다. nginx에서 이 파일을 도메인 루트로 제공하면 됩니다. `/alternatives/` 정적 파일 교체만으로는 루트 robots가 바뀌지 않습니다.

## 2. 소유 확인 메타 태그

확인 코드는 저장소에 넣지 않습니다. GitHub 저장소 **Variables**(시크릿이 아님. 값은 HTML에 공개됩니다)에 넣고, 배포 빌드가 읽습니다.

| 변수 | 메타 이름 | 콘솔 |
|---|---|---|
| `PUBLIC_GOOGLE_SITE_VERIFICATION` | `google-site-verification` | [Google Search Console](https://search.google.com/search-console) |
| `PUBLIC_NAVER_SITE_VERIFICATION` | `naver-site-verification` | [네이버 서치어드바이저](https://searchadvisor.naver.com) |
| `PUBLIC_DAUM_SITE_VERIFICATION` | `daum-site-verification` | 다음이 메타 태그를 줄 때만 |

속성 유형은 URL 접두어 `https://edtechnewsroom.com/alternatives/` 로 등록합니다. 그러면 이 사이트의 `<head>` 메타로 확인됩니다. 도메인 전체나 `https://edtechnewsroom.com/` 로 등록하면 확인 파일은 뉴스룸 루트에 두어야 하며, 이 저장소 배포만으로는 되지 않습니다.

변수를 저장한 뒤 `deploy.yml`을 한 번 다시 실행해야 메타가 운영 HTML에 들어갑니다. 비어 있으면 태그를 출력하지 않습니다.

## 3. Google Search Console

1. 속성 추가 → URL 접두어 `https://edtechnewsroom.com/alternatives/`
2. HTML 태그 확인을 고르고, content 값만 `PUBLIC_GOOGLE_SITE_VERIFICATION`에 넣습니다.
3. 재배포 후 확인을 누릅니다.
4. 사이트맵에 `https://edtechnewsroom.com/alternatives/sitemap-index.xml` 을 제출합니다.

## 4. 네이버 서치어드바이저

1. [searchadvisor.naver.com](https://searchadvisor.naver.com)에서 사이트 추가. 주소는 `https://edtechnewsroom.com/alternatives/`
2. HTML 메타 태그의 content 값만 `PUBLIC_NAVER_SITE_VERIFICATION`에 넣습니다.
3. 재배포 후 소유 확인.
4. 요청 → 사이트맵 제출에 같은 sitemap-index 주소를 넣습니다.
5. 루트 robots.txt에 `User-agent: Yeti` / `Allow: /alternatives/` 가 있는지 확인합니다.

HTML 파일 확인을 고르면 그 파일은 도메인 루트 또는 안내된 경로에 두어야 합니다. 메타 태그 방식이 이 저장소와 맞습니다.

## 5. Daum 웹마스터 도구

1. [webmaster.daum.net](https://webmaster.daum.net/) 에서 PIN을 만들고 사이트 URL로 로그인합니다. PIN은 비밀번호이므로 저장소나 채팅에 남기지 않습니다.
2. 수집 요청(또는 사이트맵 제출)에 `https://edtechnewsroom.com/alternatives/sitemap-index.xml` 을 넣습니다. 사이트맵 안 URL의 호스트는 `edtechnewsroom.com` 이어야 합니다.
3. 루트 robots.txt에 `User-agent: Daum` / `Allow: /alternatives/` 를 넣습니다.
4. 다음이 메타 태그를 요구하면 content를 `PUBLIC_DAUM_SITE_VERIFICATION`에 넣고 재배포합니다. 기본 절차는 PIN과 사이트맵입니다.

수집은 바로 반영되지 않을 수 있습니다. `site:edtechnewsroom.com/alternatives/` 로 노출 여부를 봅니다.

## 6. 피드

`https://edtechnewsroom.com/alternatives/feed.xml` 은 RSS 2.0입니다. 항목은 최근 변경 40건과, 지금 소개 중인 도구·스킬입니다.

- `guid`가 `change:…` 이면 확인으로 값이 바뀐 기록입니다.
- `guid`가 `tool:…` / `skill:…` 이면 소개 페이지입니다. 매 배포마다 새 글이 아닙니다.

소셜 자동 발행은 이 피드를 읽고, 처음 본 `guid`만 올리세요. 별 수처럼 자주 바뀌는 `change:` 항목까지 모두 올리면 글이 많아집니다. 외부로 글을 보내기 전에 초안을 만들고 승인받습니다.

## 7. 빌드에 이미 들어 있는 것

- `lang="ko"`. hreflang은 한국어만 있으므로 넣지 않습니다.
- 페이지마다 다른 한국어 `<title>`과 `meta description`, canonical.
- Open Graph / Twitter 카드와 `dist/og/*.png` (1200×630, 빌드 때 생성).
- 도구 페이지 `SoftwareApplication`, 학교 앱 페이지 `ItemList`, `BreadcrumbList`, 홈 `WebSite`+`SearchAction`(` /search/?q=` , Pagefind).
- 본문 글꼴 CSS는 화면을 막지 않도록 늦게 읽습니다. 본문 스타일시트는 그대로 먼저 적용됩니다.
