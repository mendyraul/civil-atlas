import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { EntityDetail } from '../../../components/catalog/EntityDetail';
import { SiteShell } from '../../../components/atlas/SiteShell';
import { entityAliases, fetchWorld } from '../../../lib/atlas';

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params; const world = await fetchWorld(); const item = world.civilizations.find((entry) => entry.slug === slug);
  return item ? { title: `${item.displayName} | Civil Atlas`, description: item.summary, alternates: { canonical: `/civilizations/${slug}` }, keywords: entityAliases[item.id] } : {};
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params; const world = await fetchWorld(); const item = world.civilizations.find((entry) => entry.slug === slug); if (!item) notFound();
  return <SiteShell title={item.displayName} subtitle="Civilization record"><EntityDetail entity={item} world={world} /></SiteShell>;
}
