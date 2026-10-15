import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';
import { displayRaw, FIELD_KO } from '../lib/facts';

const ORIGIN = 'https://edtechnewsroom.com/alternatives/';

function abs(path: string): string {
  return new URL(path.replace(/^\//, ''), ORIGIN).href;
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

export const GET: APIRoute = async (context) => {
  const tools = await getCollection('tools');
  const skills = await getCollection('skills');
  const changes = await getCollection('changes');
  const toolName = new Map(tools.map((t) => [t.id, t.data.name]));
  const skillName = new Map(skills.map((s) => [s.id, s.data.name]));
  const skillBySlug = new Map(skills.map((s) => [s.data.slug, s.data.name]));

  const changeItems = changes
    .map((c) => {
      const parsed = parseTarget(c.data.target);
      const name = parsed
        ? (parsed.kind === 'skills'
          ? (skillName.get(parsed.id) || skillBySlug.get(parsed.id) || parsed.id)
          : (toolName.get(parsed.id) || parsed.id))
        : c.data.target;
      const label = parsed ? fieldLabel(parsed.field) : '값';
      const when = c.data.at.slice(0, 10);
      const link = parsed?.kind === 'skills'
        ? abs(`skills/${parsed.id}/`)
        : parsed?.kind === 'tools'
          ? abs(`tools/${parsed.id}/`)
          : abs('changes/');
      const source = c.data.sources[0]?.url;
      return {
        title: `${name} ${label} ${displayRaw(c.data.before)} → ${displayRaw(c.data.after)}`,
        description: `${when} 확인. ${name}의 ${label} 값이 바뀌었습니다.${source ? ` 출처: ${source}` : ''}`,
        pubDate: new Date(c.data.at),
        link,
        categories: ['변경'],
        customData: `<guid isPermaLink="false">change:${c.id}</guid>`,
      };
    })
    .filter((item) => !Number.isNaN(item.pubDate.getTime()))
    .sort((a, b) => b.pubDate.getTime() - a.pubDate.getTime())
    .slice(0, 40);

  const toolItems = tools.map((t) => {
    const checked = t.data.github.fetchedAt || t.data.github.lastPush;
    const pubDate = new Date(checked);
    return {
      title: `도구: ${t.data.name}`,
      description: t.data.schoolUse.value,
      pubDate: Number.isNaN(pubDate.getTime()) ? new Date('2026-10-13T00:00:00Z') : pubDate,
      link: abs(`tools/${t.id}/`),
      categories: ['도구'],
      customData: `<guid isPermaLink="false">tool:${t.id}</guid>`,
    };
  });

  const skillItems = skills.map((s) => ({
    title: `오픈스킬: ${s.data.name}`,
    description: s.data.description,
    pubDate: new Date(`${s.data.dateChecked}T00:00:00Z`),
    link: abs(`skills/${s.data.slug}/`),
    categories: ['스킬'],
    customData: `<guid isPermaLink="false">skill:${s.data.slug}</guid>`,
  }));

  const items = [...changeItems, ...toolItems, ...skillItems]
    .sort((a, b) => b.pubDate.getTime() - a.pubDate.getTime());

  return rss({
    title: '열린도구 변경',
    description: '학교 앱 대안·오픈스킬의 확인된 변경과 현재 소개 목록입니다.',
    site: 'https://edtechnewsroom.com/alternatives/',
    trailingSlash: true,
    customData: '<language>ko</language>',
    items,
  });
};
