// 검색 노출용 제목·설명·구조화 데이터. 문구는 이미 있는 사실(이름, 학교 활용, 대안 요약)만 쓴다.

export const SITE_ORIGIN = 'https://edtechnewsroom.com';
export const SITE_NAME = '열린도구';

export function absUrl(base: string, path: string, site: URL | string = SITE_ORIGIN): string {
  const prefix = base.endsWith('/') ? base : `${base}/`;
  return new URL(`${prefix}${path.replace(/^\//, '')}`, site).href;
}

export function cut(text: string, max: number): string {
  const t = text.replace(/\s+/g, ' ').trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1).trimEnd()}…`;
}

export function appSeoTitle(appName: string, toolNames: string[]): string {
  const first = toolNames[0] || '오픈소스';
  const extra = toolNames.length > 1 ? ` 외 ${toolNames.length - 1}개` : '';
  return `${appName} 대신 쓸 무료 프로그램 – ${first}${extra}`;
}

export function appSeoDescription(appName: string, toolNames: string[], summary: string): string {
  const names = toolNames.join(', ');
  return cut(`${appName} 대신 쓸 무료 프로그램: ${names}. ${summary}`, 150);
}

export type Crumb = { name: string; url: string };

export function breadcrumbLd(items: Crumb[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      item: it.url,
    })),
  };
}

export function websiteLd(homeUrl: string, searchUrl: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_NAME,
    url: homeUrl,
    inLanguage: 'ko',
    description: '학교에서 쓰는 유료 앱 대신 쓸 무료 오픈소스와 수업용 스킬을 정리합니다.',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${searchUrl}?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}

export function softwareLd(opts: {
  name: string;
  url: string;
  description: string;
  category: string;
  operatingSystem: string;
  license: string | null;
}): Record<string, unknown> {
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: opts.name,
    url: opts.url,
    description: opts.description,
    applicationCategory: opts.category,
    operatingSystem: opts.operatingSystem,
    inLanguage: 'ko',
    isAccessibleForFree: true,
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'KRW' },
  };
  if (opts.license) data.license = opts.license;
  return data;
}

export function itemListLd(name: string, items: { name: string; url: string }[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name,
    itemListOrder: 'https://schema.org/ItemListOrderAscending',
    numberOfItems: items.length,
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      url: it.url,
    })),
  };
}

export function osLabel(p: {
  windows: string; macos: string; linux: string; web: string; android: string; ios: string;
}): string {
  const bits: string[] = [];
  if (p.windows === 'yes') bits.push('Windows');
  if (p.macos === 'yes') bits.push('macOS');
  if (p.linux === 'yes') bits.push('Linux');
  if (p.web === 'official' || p.web === 'self-host') bits.push('Web');
  if (p.android === 'yes') bits.push('Android');
  if (p.ios === 'yes') bits.push('iOS');
  return bits.join(', ') || '확인 중';
}
