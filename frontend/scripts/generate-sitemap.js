import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const baseUrl = 'https://rentcopartner.com';
const publicRoutes = [
  '/',
  '/privacy-policy',
  '/terms-and-conditions',
  '/refund-policy',
  '/contact',
  '/help',
];

const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${publicRoutes
  .map((route) => `  <url><loc>${baseUrl}${route}</loc></url>`)
  .join('\n')}\n</urlset>\n`;

const distDirectory = resolve('dist');
await mkdir(distDirectory, { recursive: true });
for (const fileName of await readdir(distDirectory)) {
  if (!fileName.endsWith('.html')) continue;
  const filePath = resolve(distDirectory, fileName);
  const html = await readFile(filePath, 'utf8');
  const cleaned = html
    .replace(/<title(?![^>]*data-rh)[^>]*>[\s\S]*?<\/title>/gi, '')
    .replace(/<meta(?![^>]*data-rh)(?=[^>]*(?:name="description"|property="og:[^"]+"|name="twitter:[^"]+"))[^>]*>/gi, '')
    .replace(/<link(?![^>]*data-rh)(?=[^>]*rel="canonical")[^>]*>/gi, '');
  if (cleaned !== html) await writeFile(filePath, cleaned, 'utf8');
}
await writeFile(resolve(distDirectory, 'sitemap.xml'), xml, 'utf8');
