# 열린도구 Alternatives

학교에서 이미 쓰는 유료·상용 앱을 대신할 수 있는 오픈소스 대안을 소개하는 정보 공유 사이트입니다.

## 프로젝트 개요

교사에게 필요한 것은 "무엇을 믿고 쓸지, 어떻게 설치하고 수업에 쓰는지, 계속 업데이트되는지"에 대한 한국어 정보입니다. 이 사이트는:

- **출처가 명확한 정보**: 모든 사실에는 원 출처 URL과 확인 시각이 포함됩니다
- **학교 맥락 반영**: 학생 기기, 관리자 권한, 오프라인 환경, HWP 지원 등 학교 환경을 고려합니다
- **솔직한 안내**: 부분 대체나 대안이 없는 영역도 명확히 알립니다

## 주요 기능

### 대상 앱 카테고리
- 영상·오디오: CapCut, 반디캠, 오캠 등
- 이미지·디자인: Adobe Photoshop, Illustrator 등
- 문서·오피스: 한컴오피스, Visio 등
- 압축·유틸리티: 알집, 알캡처 등

### 역할별 진입점
- **담임·교과 교사**: 수업 활용 중심
- **정보부장·전산 담당**: 일괄 배포, 관리자 권한, 오프라인 환경
- **행정·교무**: 문서·PDF·HWP 호환

## 기술 스택

- **프레임워크**: Astro 6
- **런타임**: Node.js 22+
- **콘텐츠 관리**: Astro Content Collections + Zod 스키마
- **배포**: Cloudflare Pages (예정)

## 개발 환경 설정

### 요구사항
- Node.js 22 이상
- npm 10 이상

### 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 타입 체크
npm run check
```

## 프로젝트 구조

```
.
├── src/
│   ├── content/
│   │   ├── tools/           # 오픈소스 도구 데이터
│   │   ├── school-apps/     # 학교 앱(기준 앱) 데이터
│   │   └── changes/         # 변경 이력
│   ├── content.config.ts    # Content Collections 스키마
│   ├── components/          # Astro 컴포넌트
│   ├── pages/              # 페이지
│   └── layouts/            # 레이아웃
├── design/
│   └── mockup-html/        # HTML 디자인 시안
├── scripts/
│   ├── verify.py           # 데이터 검증 스크립트
│   └── convert-seed.py     # 씨앗 데이터 변환
└── public/                 # 정적 파일
```

## 데이터 모델

모든 사실(fact)은 다음 구조를 따릅니다:

```typescript
interface Fact<T> {
  value: T;
  sources: Source[];        // 1개 이상 필수
  status: 'verified' | 'unverified' | 'conflict' | 'stale';
  lastVerified: string | null;
}

interface Source {
  url: string;              // 원 출처
  fetchedAt: string;        // 확인 시각(ISO)
  excerpt?: string;         // 근거 문장
  method: 'github-api' | 'release-assets' | 'official-site' | 'readme' | 'procurement-data' | 'manual-seed';
}
```

### 검증 규칙

**중요**: `manual-seed` 출처만 있는 사실은 `verified` 상태가 될 수 없습니다. 이 규칙은 Zod 스키마로 강제되며, 빌드 시 검증됩니다.

## CI/CD

GitHub Actions를 통해 다음 작업이 자동으로 실행됩니다:

- **타입 체크**: `astro check`
- **빌드 검증**: `astro build`
- **데이터 검증**: `scripts/verify.py` (있는 경우)

## 배포 (Cloudflare Pages)

Cloudflare Pages 배포를 위한 설정:

- **빌드 명령**: `npm run build`
- **빌드 출력 디렉토리**: `dist`
- **Node 버전**: 22

수동 배포 단계는 저장소 소유자가 Cloudflare Pages 대시보드에서 진행합니다.

## 운영 원칙

1. **판정하지 않고 사실만 쓴다**: "학교에 적합", "안전함" 같은 보증 표현 대신 출처가 명확한 사실을 제공합니다
2. **기준은 교사가 아는 앱**: CapCut 대신, 알집 대신 등 익숙한 앱을 기준으로 합니다
3. **안 되는 것도 솔직하게**: 부분 대체나 대안 없음을 명확히 표시합니다
4. **출처 없는 사실은 게시하지 않음**: 모든 사실은 원 출처를 가져야 합니다

## 기여하기

이 프로젝트는 1단계 구축 중입니다. 기여 가이드는 추후 공개될 예정입니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 공개됩니다 (예정).

## 연락처

- 저장소 관리자: @scottnaddle
- 이슈 및 제안: [GitHub Issues](https://github.com/scottnaddle/open-tools-alternatives/issues)

---

**주의**: 이 사이트는 학교 적합성이나 법적 판단을 제공하지 않습니다. 학습지원 소프트웨어 선정 시에는 교육부 가이드라인과 학교 절차를 따라야 합니다.
