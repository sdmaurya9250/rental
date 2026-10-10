# SEO implementation checklist

## Changes made

- Added build-time prerendering for the home page, contact, help, policy pages, and the not-found page. Login is a popup on Home; `/login` redirects to the Home popup. The account dashboard, booking flows, and API-backed profile screens remain client-rendered and marked `noindex` because they depend on the signed-in user or live data.
- Added route-aware title, description, canonical, Open Graph, and Twitter metadata through the reusable `Seo` component. The generated public pages have one H1, one canonical URL, and one description tag.
- Added Organization, WebSite, and FAQPage JSON-LD to the home page.
- Added the sitemap generator and `robots.txt`; the sitemap lists the public, indexable pages.
- Added a branded not-found page and configured its static output as `dist/404.html`.
- Removed the standalone login screen; `/login` now redirects to Home and opens the shared login popup. Registration can open the same popup with `/?auth=register`.
- Added image alternative text, intrinsic width and height, and lazy loading to profile images. The home hero image is high priority.
- Signup now offers Finder or provider roles only; accounts with an older combined role follow Finder behavior.
- Kept `npm run dev` on Vite. The build now runs `vite-react-ssg build` and then generates the sitemap.
- Added `vite-react-ssg` as a dev dependency. It creates static HTML from the React Router routes. Its current release imports the React Router v6 server entry point, so `react-router-dom` was aligned to `^6.30.1`; the app uses the compatible route APIs.
- No custom web fonts are loaded by this project; it uses system fonts, so there is no `@font-face` declaration to set `font-display` on.

## Files touched

- `package.json`, `package-lock.json`, `vite.config.js`, `index.html`
- `.firebase/hosting.ZGlzdA.cache` (updated build/hosting cache)
- `src/App.jsx`, `src/main.jsx`, `src/auth/auth.js`, `src/components/Seo.jsx`
- `src/pages/Home.jsx`, `src/pages/ContactPage.jsx`, `src/pages/HelpPage.jsx`, `src/pages/PrivacyPolicyPage.jsx`, `src/pages/RefundPolicyPage.jsx`, `src/pages/TermsAndConditionsPage.jsx`, `src/pages/NotFoundPage.jsx`, `src/pages/InfoPageLayout.jsx`; removed `src/pages/Login.jsx`
- `src/pages/DashboardPage.jsx`, `src/pages/ProfilePage.jsx`, `src/pages/BookingsList.jsx`, `src/pages/BookingsList copy.jsx`, `src/pages/AvailabilityPage.jsx`, `src/pages/MainContent.jsx`, `src/pages/MyProfilePage.jsx`, `src/pages/MessagesPage.jsx`
- `src/components/AuthModal.jsx`, `src/components/Sidebar.jsx`, `src/components/TopBar.jsx`, `src/components/PersonRow.jsx`
- `public/robots.txt`, `scripts/generate-sitemap.js`

## Manual steps before/after deployment

- Verify the site in Google Search Console and submit `https://rentcopartner.com/sitemap.xml`.
- Replace the current Open Graph image (`/Joyful_South_Asian_Couple_Small.png`) with a final branded social preview image. Update `Seo.jsx` and `index.html` to the new image path.
- Configure hosting to serve the generated flat HTML routes (for example, `/contact` from `contact.html`) and return `404.html` with HTTP status 404 for unknown URLs. Keep the SPA fallback available for signed-in client routes.
- Companion profile URLs are API-backed and require a known profile ID, so they are not prerendered or included in the sitemap. If profiles should be publicly indexed, provide a public profile catalog/static IDs and decide which profile data is safe to expose.
- Connect the Contact form to a real support endpoint or mail service; its current submit handler only logs form values in the browser.
- Confirm the contact phone/email and homepage metrics (member, booking, and rating counts) are current and approved for publication.
- If a custom web font is added later, set `font-display: swap` in its `@font-face` rule.

## Build and development verification

- `npm run build` completed and generated HTML for seven routes, including `dist/index.html`, the public help/contact/policy pages, and `dist/404.html`. There is no standalone `dist/login.html` page.
- Generated HTML was checked for rendered page text, one H1, one canonical, and a 140–160 character meta description. `npm run dev` started successfully and returned HTTP 200 for the Vite entry points.
- npm reported 3 dependency audit findings (2 moderate, 1 high) during installation; review with `npm audit` as part of routine dependency maintenance.

To confirm the home-page content is present in generated HTML:

```sh
rg -l -g '*.html' "Find Your Perfect|What is RentCoPartner" dist
```
