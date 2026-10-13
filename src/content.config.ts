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
    license: z.string().nullable(),
    sourceUrl: z.string().url(),
    dateChecked: z.string(),
    previewType: z.enum(['iframe', 'image', 'none']).optional(),
    previewPath: z.string().optional(),
    github: z.object({
      repo: z.string(),
      stars: z.number().int(),
      createdAt: z.string(),
      license: z.string().nullable(),
    }),
  }),
});

export const collections = { tools, schoolApps, changes, skills };
