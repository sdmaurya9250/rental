import { Head } from 'vite-react-ssg';
import { useLocation } from 'react-router-dom';

const SITE_URL = 'https://rentcopartner.com';
const DEFAULT_IMAGE = `${SITE_URL}/Joyful_South_Asian_Couple_Small.png`;

export default function Seo({
  title = 'Find a Rental Companion | RentCoPartner',
  description = 'Explore RentCoPartner profiles for social and lifestyle companionship. Review listed services, availability and rates before sending a booking request.',
  canonical,
  ogImage = DEFAULT_IMAGE,
  type = 'website',
  noIndex = false,
}) {
  const { pathname } = useLocation();
  const path = pathname;
  const canonicalUrl = canonical || `${SITE_URL}${path === '/' ? '/' : path.replace(/\/$/, '')}`;
  const imageUrl = ogImage.startsWith('http') ? ogImage : `${SITE_URL}${ogImage.startsWith('/') ? '' : '/'}${ogImage}`;

  return (
    <Head>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="robots" content={noIndex ? 'noindex, nofollow' : 'index, follow'} />
      <link rel="canonical" href={canonicalUrl} />
      <meta property="og:type" content={type} />
      <meta property="og:site_name" content="RentCoPartner" />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:image" content={imageUrl} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={imageUrl} />
    </Head>
  );
}
