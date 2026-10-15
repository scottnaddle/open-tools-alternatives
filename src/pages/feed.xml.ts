import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';
import { execFileSync } from 'node:child_process';
import { displayRaw, FIELD_KO } from '../lib/facts';

const ORIGIN = 'https://edtechnewsroom.com/alternatives/';

// 일일 검증이 숫자·시각만 갱신하는 필드. 소셜 피드에 넣지 않는다.
const NOISE_FIELDS = new Set([
  'stars', 'lastPush', 'latestRelease', 'fetchedAt', 'dateChecked', 'createdAt',
]);

type Kind = 'new' | 'update';

type FeedItem = {
  title: string;
  description: string;
  pubDate: Date;
  link: string;
  category: Kind;
  guid: string;
};

function abs(path: string): string {
  return new URL(path.replace(/^\//, ''), ORIGIN).href;
}

function xmlText(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function brief(text: string): string {
  const flat = text.replace(/\s+/g, ' ').trim();
  const sentences = flat.split(/(?<=[.!?。])\s+/).filter(Boolean);
  const joined = sentences.length > 2 ? sentences.slice(0, 2).join(' ') : flat;
  if (joined.length <= 180) return joined;
  const cut = joined.slice(0, 180);
  const space = cut.lastIndexOf(' ');
  return `${(space > 120 ? cut.slice(0, space) : cut).trim()}…`;
}

function fieldLabel(field: string): string {
  const last = field.split('.').pop() || field;
  return FIELD_KO[last] || FIELD_KO[field] || field;
}

function parseTarget(target: string): { kind: string; id: string; field: string } | null {
  const slash = target.indexOf('/');
  const dot = target.indexOf('.');
  if (slash < 0 || dot < slash) return null;
  return {
    kind: target.slice(0, slash),
    id: target.slice(slash + 1, dot),
    field: target.slice(dot + 1),
  };
}

function isNumber(value: unknown): boolean {
  if (typeof value === 'number') return Number.isFinite(value);
  return typeof value === 'string' && /^-?\d+(\.\d+)?$/.test(value.trim());
}

function isDate(value: unknown): boolean {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}(T[\d:.+Z-]+)?$/.test(value.trim());
}

function isRelease(value: unknown): boolean {
  return !!value && typeof value === 'object' && !Array.isArray(value) && 'tag' in value;
}

function isVersionString(value: unknown): boolean {
  return typeof value === 'string' && /^v?\d+\.\d+/.test(value.trim());
}

/** scripts/check_links.py 의 피드 검사와 같은 기준이다. */
function stable(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => stable(item)).join(',')}]`;
  const obj = value as Record<string, unknown>;
  return `{${Object.keys(obj).sort().map((key) => `${JSON.stringify(key)}:${stable(obj[key])}`).join(',')}}`;
}

function isNoise(field: string, before: unknown, after: unknown): boolean {
  const last = field.split('.').pop() || field;
  if (NOISE_FIELDS.has(last)) return true;
  if (isNumber(before) && isNumber(after)) return true;
  if (isDate(before) && isDate(after)) return true;
  if (isRelease(before) || isRelease(after)) return true;
  if (isVersionString(before) && isVersionString(after)) return true;
  return false;
}

function addedAt(relPath: string): Date {
  let out = '';
  try {
    out = execFileSync(
      'git',
      ['log', '--follow', '--diff-filter=A', '--format=%aI', '--', relPath],
      { encoding: 'utf8' },
    ).trim();
  } catch {
    throw new Error(`피드 날짜: git 이력을 읽지 못했습니다 (${relPath}). checkout은 fetch-depth: 0 이어야 합니다.`);
  }
  const lines = out.split('\n').map((line) => line.trim()).filter(Boolean);
  const iso = lines[lines.length - 1];
  if (!iso) {
    throw new Error(`피드 날짜: ${relPath} 을 처음 넣은 커밋이 없습니다. shallow clone이면 fetch-depth: 0 으로 다시 받으세요.`);
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`피드 날짜: ${relPath} 의 시각을 해석하지 못했습니다 (${iso})`);
  }
  return date;
}

export const GET: APIRoute = async () => {
  const tools = await getCollection('tools');
  const skills = await getCollection('skills');
  const apps = await getCollection('schoolApps');
  const changes = await getCollection('changes');
  const toolById = new Map(tools.map((tool) => [tool.id, tool]));
  const skillById = new Map(skills.map((skill) => [skill.id, skill]));

  const items: FeedItem[] = [];

  for (const tool of tools) {
    items.push({
      title: `새 도구: ${tool.data.name}`,
      description: brief(tool.data.schoolUse.value),
      pubDate: addedAt(`src/content/tools/${tool.id}.json`),
      link: abs(`tools/${tool.id}/`),
      category: 'new',
      guid: `new:tool:${tool.id}`,
    });
  }

  for (const skill of skills) {
    items.push({
      title: `새 오픈스킬: ${skill.data.name}`,
      description: brief(skill.data.description),
      pubDate: addedAt(`src/content/skills/${skill.id}.json`),
      link: abs(`skills/${skill.data.slug}/`),
      category: 'new',
      guid: `new:skill:${skill.data.slug}`,
    });
  }

  for (const app of apps) {
    const gap = app.data.gap?.value?.trim();
    const line = app.data.alternatives[0]?.summary?.trim() ?? '';
    items.push({
      title: `새 페이지: ${app.data.name} 대안`,
      description: brief(gap || line || `${app.data.name} 대안을 소개합니다.`),
      pubDate: addedAt(`src/content/school-apps/${app.id}.json`),
      link: abs(`apps/${app.id}/`),
      category: 'new',
      guid: `new:app:${app.id}`,
    });
  }

  const seenChange = new Set<string>();
  const ordered = [...changes].sort((a, b) => {
    const delta = new Date(a.data.at).getTime() - new Date(b.data.at).getTime();
    return delta || a.id.localeCompare(b.id);
  });
  for (const change of ordered) {
    const parsed = parseTarget(change.data.target);
    if (!parsed || isNoise(parsed.field, change.data.before, change.data.after)) continue;
    const fingerprint = `${change.data.target}\0${stable(change.data.before)}\0${stable(change.data.after)}`;
    if (seenChange.has(fingerprint)) continue;
    seenChange.add(fingerprint);
    const when = new Date(change.data.at);
    if (Number.isNaN(when.getTime())) continue;
    const label = fieldLabel(parsed.field);
    if (parsed.kind === 'tools') {
      const tool = toolById.get(parsed.id);
      if (!tool) continue;
      items.push({
        title: `${tool.data.name} ${label} 변경`,
        description: brief(`${tool.data.name}의 ${label} 값이 바뀌었습니다. ${displayRaw(change.data.before)}에서 ${displayRaw(change.data.after)}입니다.`),
        pubDate: when,
        link: abs(`tools/${tool.id}/`),
        category: 'update',
        guid: `update:${change.id}`,
      });
    } else if (parsed.kind === 'skills') {
      const skill = skillById.get(parsed.id);
      if (!skill) continue;
      items.push({
        title: `${skill.data.name} ${label} 변경`,
        description: brief(`${skill.data.name}의 ${label} 값이 바뀌었습니다. ${displayRaw(change.data.before)}에서 ${displayRaw(change.data.after)}입니다.`),
        pubDate: when,
        link: abs(`skills/${skill.data.slug}/`),
        category: 'update',
        guid: `update:${change.id}`,
      });
    }
  }

  items.sort((a, b) => b.pubDate.getTime() - a.pubDate.getTime() || a.guid.localeCompare(b.guid));

  return rss({
    title: '열린도구 새 소식',
    description: '새로 올라온 도구·오픈스킬·학교 앱 페이지와, 내용이 바뀐 기록입니다. 숫자나 날짜만 바뀐 확인 기록은 넣지 않습니다.',
    site: 'https://edtechnewsroom.com/alternatives/',
    trailingSlash: true,
    customData: '<language>ko</language>',
    items: items.map((item) => ({
      title: item.title,
      description: item.description,
      pubDate: item.pubDate,
      link: item.link,
      categories: [item.category],
      customData: `<guid isPermaLink="false">${xmlText(item.guid)}</guid>`,
    })),
  });
};
