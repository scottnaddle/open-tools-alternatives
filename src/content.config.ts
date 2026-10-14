// PLAN.md 7.2 모델을 Zod로 옮김. 씨앗 데이터는 전부 unverified / manual-seed.
import { defineCollection, reference, z } from 'astro:content';
import { glob } from 'astro/loaders';
import type { ZodTypeAny } from 'zod';

const Source = z.object({
  url: z.string().url(),
  fetchedAt: z.string().datetime({ offset: true }),
  excerpt: z.string().optional(),
  method: z.enum(['github-api', 'release-assets', 'official-site', 'readme', 'procurement-data', 'manual-seed']),
});
const fact = <T extends ZodTypeAny>(v: T) =>
  z.object({
    value: v,
    sources: z.array(Source).min(1),
    status: z.enum(['verified', 'unverified', 'conflict', 'stale']),
    lastVerified: z.string().nullable(),
  }).refine(
    (f) => f.status !== 'verified' || f.sources.some((s) => s.method !== 'manual-seed'),
    { message: 'manual-seed 출처만 있는 사실은 verified 일 수 없음' },
  );

const Difficulty = z.enum(['쉬움', '보통', '어려움', '서버 구축']);
const Level = z.enum(['거의 대체', '부분 대체']);
const Support = z.enum(['yes', 'partial', 'no']);
const UsageScope = z.enum(['personal', 'demo', 'offline-install', 'student-use-check']);

const tools = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/tools' }),
  schema: z.object({
    name: z.string(),
    category: z.string(),
    notes: z.array(z.string()).default([]),
    schoolUse: fact(z.string()),
    usageMode: fact(z.enum(['pc', 'web', 'server'])),
    installDifficulty: fact(Difficulty),
    platforms: fact(z.object({
      windows: Support, macos: Support, linux: Support,
      web: z.enum(['official', 'self-host', 'partial', 'no']),
      mobileWeb: Support, android: Support, ios: Support,
    })),
    license: fact(z.string().nullable()),
    officialSite: fact(z.string().url().nullable()),
    github: z.object({
      repo: z.string(), stars: z.number().int(), lastPush: z.string(), archived: z.boolean(),
      latestRelease: z.object({ tag: z.string(), date: z.string(), url: z.string().url() }).nullable(),
      fetchedAt: z.string(),
      official: z.object({ host: z.string().url(), lastActivity: z.string(), license: z.string().nullable().optional(),
        latestRelease: z.object({ tag: z.string(), date: z.string(), url: z.string().url(), fromTag: z.boolean().optional() }).nullable().optional(),
        fetchedAt: z.string() }).optional(),
    }),
    pendingLicense: z.object({ value: z.string(), note: z.string(), plainKo: z.string().optional(), proposedAt: z.string(), earliestApply: z.string(), sources: z.array(Source).min(1) }).optional(),
    licenseNote: z.object({ note: z.string(), plainKo: z.string().optional() }).optional(),
    verification: z.object({ runId: z.string(), at: z.string(), unresolved: z.array(z.string()), notes: z.array(z.string()) }).optional(),
    health: z.enum(['active', 'slowing', 'stale', 'archived']),
    // v4 추가 필드 (PLAN 7.2, 7.4)
    features: fact(z.array(z.string())).optional(),
    tags: z.array(z.string()).default([]),
    koreanUI: fact(Support).optional(),
    hwp: fact(z.object({ read: Support, write: Support })).optional(),
    network: fact(z.enum(['offline', 'first-run', 'online', 'external-server'])).optional(),
    account: fact(z.enum(['none', 'optional', 'required'])).optional(),
    studentData: fact(z.enum(['none', 'local-only', 'sent-to-server'])).optional(),
    minAge: fact(z.number().int().nullable()).optional(),
    adminRequired: fact(z.enum(['no', 'yes', 'portable-available'])).optional(),
    massDeploy: fact(z.object({ msi: Support, winget: Support, silent: Support })).optional(),
    minRequirements: fact(z.string().nullable()).optional(),
    csap: fact(z.enum(['yes', 'no', 'n/a', 'unknown'])).optional(),
    privacyPolicyUrl: fact(z.string().url().nullable()).optional(),
    usageScope: z.array(UsageScope).default(['personal']), // 파생값, 빌드 시 계산
  }).refine(
    (tool) => {
      // usageScope 규칙 검증 (PLAN 7.4): student-use-check가 있으면 필수 필드가 verified여야 함
      if (tool.usageScope.includes('student-use-check')) {
        const hasStudentData = tool.studentData && tool.studentData.status === 'verified';
        const hasAccount = tool.account && tool.account.status === 'verified';
        const hasMinAge = tool.minAge && tool.minAge.status === 'verified';
        return hasStudentData || hasAccount || hasMinAge;
      }
      return true;
    },
    { message: 'student-use-check 태그가 있으면 studentData, account, minAge 중 하나는 verified 상태여야 함' }
  ),
});

const schoolApps = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/school-apps' }),
  schema: z.object({
    name: z.string(),
    category: z.string(),
    icon: z.string(),
    source: z.enum(['procurement', 'field']),
    bundle: z.number().int().min(1).max(6),
    procurementNote: fact(z.string()).nullable(),
    gap: fact(z.string()).nullable(),
    alternatives: z.array(z.object({
      tool: reference('tools'),
      level: fact(Level),
      installDifficulty: Difficulty,
      summary: z.string(),
    })).min(1),
    // 학교 앱별 기능 비교 매트릭스(선택). 1차 출처가 확인된 기능만 채움. 없으면 페이지에서 "한 줄" 안내.
    featureMatrix: z.array(z.object({
      name: z.string(),
      sourceUrl: z.string().url().optional(),
    })).optional(),
  }),
});

// ChangeRecord (PLAN 7.2) — /changes 와 롤백 근거. 아직 레코드 없음.
const changes = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/changes' }),
  schema: z.object({
    at: z.string(), agent: z.string(), runId: z.string(), target: z.string(),
    before: z.unknown(), after: z.unknown(), sources: z.array(Source),
    tier: z.enum(['A', 'B', 'C']), gates: z.array(z.string()), commit: z.string(),
  }),
});

// 스킬 라이선스 허용목록 (ops/RESEARCH.md 4절 규칙과 동일하게 유지).
// 없음(null)·AGPL·NOASSERTION·비OSI(CC-BY-SA 등)는 게시하지 않는다. scripts/check_skills.py와 목록 일치 필수.
export const ALLOWED_SKILL_LICENSES = [
  'MIT', 'Apache-1.1', 'Apache-2.0',
  'BSD-1-Clause', 'BSD-2-Clause', 'BSD-2-Clause-FreeBSD', 'BSD-3-Clause',
  'GPL-2.0', 'GPL-2.0-only', 'GPL-2.0-or-later', 'GPL-3.0', 'GPL-3.0-only', 'GPL-3.0-or-later',
  'LGPL-2.1', 'LGPL-2.1-only', 'LGPL-2.1-or-later', 'LGPL-3.0', 'LGPL-3.0-only', 'LGPL-3.0-or-later',
  'MPL-1.1', 'MPL-2.0', 'ISC', 'Unlicense', 'CC0-1.0', '0BSD', 'Zlib', 'Artistic-2.0', 'EPL-2.0',
];

const skills = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/skills' }),
  schema: z.object({
    name: z.string(),
    slug: z.string(),
    description: z.string(),
    category: z.enum(['수업자료·발표', '그림·도해', '영상·미디어', '데이터·차트', '교사 업무·글쓰기', '웹·앱 만들기', '기타']),
    usageScope: z.enum(['수업용', '교사 개인용']),
    installNeeded: z.boolean(),
    apiKeyNeeded: z.boolean(),
    license: z.string().nullable().refine(
      (v) => v !== null && (ALLOWED_SKILL_LICENSES as readonly string[]).includes(v),
      { message: '라이선스가 허용목록(OSI 계열)에 없음 — AGPL·NOASSERTION·라이선스 없음·비OSI는 게시 금지' },
    ),
    sourceUrl: z.string().url(),
    dateChecked: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'dateChecked는 YYYY-MM-DD 형식'),
    previewType: z.enum(['iframe', 'image', 'none']).optional(),
    previewPath: z.string().optional(),
    // 미리보기 제작 방식 (AGENTS.md 원칙 1·2: 출처 표기 없는 데모는 게시하지 않는다)
    previewMethod: z.enum(['self-made', 'official-example']).optional(),
    previewNote: z.string().optional(),
    github: z.object({
      repo: z.string(),
      stars: z.number().int(),
      createdAt: z.string(),
      license: z.string().nullable(),
    }),
  }).refine(
    (s) => !s.previewType || s.previewType === 'none' || !!s.previewPath,
    { message: 'previewType이 iframe/image면 previewPath가 필요함' },
  ).refine(
    (s) => s.sourceUrl.replace(/^https?:\/\/github\.com\//, '').replace(/\/+$/, '').toLowerCase() === s.github.repo.toLowerCase(),
    { message: 'sourceUrl과 github.repo가 일치하지 않음' },
  ),
});

// 4축 페이지 — Stage 3 데이터 모델 (edzip.kr 차용 IA: 현장사례/수업지도안/심층리뷰)
// 회귀: Base.astro의 4 navLinks map이 깨지는 케이스(2026-10-13)와 별개. 스키마는 빌드 시 1회 평가되며 안전.
// 원칙: 출처 필수, manual-seed는 verified 불가(tools와 동일), example=true면 "예시 데이터" 배지 강제
const Method = z.enum(['github-api', 'release-assets', 'official-site', 'readme', 'procurement-data', 'manual-seed']);

const cases = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/cases' }),
  schema: z.object({
    title: z.string(),
    grade: z.string(),            // 예: "중3"
    unit: z.string(),             // 예: "포물선 운동"
    schoolContext: z.string(),    // 예: "중학교 1인 1PC 컴퓨터실"
    tool: z.object({ slug: z.string(), sourceUrl: z.string().url() }),
    summary: z.string(),
    sourceUrl: z.string().url(),  // 사례의 1차 출처(보통 공식 저장소)
    sourceMethod: Method,
    fetchedAt: z.string().datetime({ offset: true }),
    dateChecked: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'dateChecked는 YYYY-MM-DD 형식'),
    example: z.boolean().default(true),  // true면 페이지에 "예시 데이터" 배지 강제
    badges: z.array(z.string()).default([]),
  }),
});

const lessons = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/lessons' }),
  schema: z.object({
    title: z.string(),
    grade: z.string(),
    unit: z.string(),
    duration: z.string(),         // 예: "40분"
    schoolContext: z.string(),
    tool: z.object({ slug: z.string(), sourceUrl: z.string().url() }),
    summary: z.string(),
    sourceUrl: z.string().url(),
    sourceMethod: Method,
    fetchedAt: z.string().datetime({ offset: true }),
    dateChecked: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'dateChecked는 YYYY-MM-DD 형식'),
    example: z.boolean().default(true),
    badges: z.array(z.string()).default([]),
  }),
});

const reviews = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/reviews' }),
  schema: z.object({
    title: z.string(),
    tool: z.object({ slug: z.string(), sourceUrl: z.string().url(), license: z.string() }),
    summary: z.string(),
    sourceUrl: z.string().url(),
    sourceMethod: Method,
    fetchedAt: z.string().datetime({ offset: true }),
    dateChecked: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'dateChecked는 YYYY-MM-DD 형식'),
    example: z.boolean().default(true),
    badges: z.array(z.string()).default([]),
  }),
});

export const collections = { tools, schoolApps, changes, skills, cases, lessons, reviews };
