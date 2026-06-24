import { CatalogVariantPage } from "@/features/catalog/catalog-pages";
import { AppShell } from "@/shared/components/app-shell";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <CatalogVariantPage id={id} />
    </AppShell>
  );
}
