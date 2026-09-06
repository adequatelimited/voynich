/** Canonical object order only. Do not normalize research text, code or manuscript spaces. */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== 'object') { const encoded = JSON.stringify(value); if (encoded === undefined) throw new Error('Unsupported canonical value'); return encoded; }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`).join(',')}}`;
}
export async function sha256(value: string | Uint8Array): Promise<string> {
  const data = typeof value === 'string' ? new TextEncoder().encode(value) : value;
  const bytes = new Uint8Array(data); const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(x => x.toString(16).padStart(2, '0')).join('');
}
export const hashObject = (value: unknown) => sha256(canonicalJson(value));
