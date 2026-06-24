import { AppShell } from "@/shared/components/app-shell";
import { CatalogPage } from "@/features/catalog/catalog-pages";

export default function Page() {
  return (
    <AppShell>
      <CatalogPage />
    </AppShell>
  );
}
