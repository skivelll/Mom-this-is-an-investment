"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  mutations,
  useApiMutation,
  useCatalogItem,
  useCatalogItems,
  useCatalogVariant,
  useCatalogVariants,
  useCategories,
  useCollections,
} from "@/shared/api/hooks";
import { canEditCatalog, useMe } from "@/shared/auth/use-auth";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";
import { date, normalizeTitle } from "@/shared/lib/format";

const itemSchema = z.object({
  category_id: z.string().min(1, "Выберите категорию."),
  canonical_title: z.string().min(1, "Название обязательно."),
  normalized_title: z.string().min(1, "Нормализованное название обязательно."),
  description: z.string().optional(),
  release_year: z.coerce.number().int().min(1800).max(3000).optional().or(z.literal("")),
  status: z.enum(["draft", "active", "archived"]),
});

const variantSchema = z.object({
  catalog_item_id: z.string().min(1, "Выберите item."),
  canonical_title: z.string().min(1, "Название обязательно."),
  normalized_title: z.string().min(1, "Нормализованное название обязательно."),
  sku: z.string().optional(),
  barcode: z.string().optional(),
  release_date: z.string().optional(),
  status: z.enum(["draft", "active", "archived"]),
});

export function CatalogPage() {
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const { data: categories = [] } = useCategories();
  const variants = useCatalogVariants({ query: query || undefined, category_id: categoryId || undefined });
  const items = useCatalogItems({ query: query || undefined, category_id: categoryId || undefined });
  const { data: me } = useMe();

  return (
    <AppSection
      title="Каталог"
      subtitle="Ищем по вариантам каталога, но рядом показываем базовые items: это удобно для создания новых editions."
    >
      <Panel>
        <div className="grid gap-3 md:grid-cols-[1fr_220px]">
          <input className="ink-input" placeholder="Chainsaw Man, Batman, Null Point..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <select className="ink-input" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="">Все категории</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </Panel>

      {canEditCatalog(me?.role) ? <CatalogCreatePanel /> : null}

      <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <h2 className="font-display text-2xl uppercase">Варианты</h2>
          {variants.error ? <ErrorMessage error={variants.error} /> : null}
          <div className="mt-4 grid gap-3">
            {variants.data?.map((variant) => (
              <Link className="rounded-lg border-2 border-border p-3 transition hover:bg-background" href={`/catalog/variants/${variant.id}`} key={variant.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-black">{variant.canonical_title}</p>
                    <p className="text-sm text-muted">SKU: {variant.sku ?? "не указан"} · barcode: {variant.barcode ?? "нет"}</p>
                  </div>
                  <StatusBadge status={variant.status} />
                </div>
              </Link>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl uppercase">Items</h2>
          <div className="mt-4 grid gap-3">
            {items.data?.map((item) => (
              <Link className="rounded-lg border-2 border-border p-3 transition hover:bg-background" href={`/catalog/items/${item.id}`} key={item.id}>
                <p className="font-black">{item.canonical_title}</p>
                <p className="text-sm text-muted">{item.release_year ?? "год неизвестен"}</p>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </AppSection>
  );
}

export function CatalogItemPage({ id }: { id: string }) {
  const item = useCatalogItem(id);
  const variants = useCatalogVariants({ query: item.data?.canonical_title });

  if (item.error) return <WrappedError error={item.error} />;
  if (!item.data) return <WrappedLoading />;

  return (
    <AppSection title={item.data.canonical_title} subtitle={item.data.description ?? "Базовая карточка объекта каталога."}>
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={item.data.status} />
          <span className="font-bold text-muted">Год: {item.data.release_year ?? "не указан"}</span>
          <span className="font-bold text-muted">Category ID: {item.data.category_id}</span>
        </div>
      </Panel>
      <Panel>
        <h2 className="font-display text-2xl uppercase">Похожие варианты</h2>
        <div className="mt-4 grid gap-3">
          {variants.data?.map((variant) => (
            <Link className="rounded-lg border-2 border-border p-3 font-bold hover:bg-background" href={`/catalog/variants/${variant.id}`} key={variant.id}>
              {variant.canonical_title}
            </Link>
          ))}
        </div>
      </Panel>
    </AppSection>
  );
}

export function CatalogVariantPage({ id }: { id: string }) {
  const variant = useCatalogVariant(id);
  const collections = useCollections();
  const addToWishlist = useApiMutation(mutations.addWishlistItem, [["wishlist"]]);
  const addToCollection = useApiMutation(
    ({ collectionId, payload }: { collectionId: string; payload: Record<string, unknown> }) =>
      mutations.addCollectionItem(collectionId, payload),
    [["collections"]],
  );
  const [collectionId, setCollectionId] = useState("");

  if (variant.error) return <WrappedError error={variant.error} />;
  if (!variant.data) return <WrappedLoading />;

  return (
    <AppSection title={variant.data.canonical_title} subtitle="Конкретное издание/вариант: то, что попадает в коллекцию или wishlist.">
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={variant.data.status} />
            <span className="font-bold text-muted">Дата релиза: {date(variant.data.release_date)}</span>
          </div>
          <dl className="mt-5 grid gap-3 md:grid-cols-2">
            <Meta label="Catalog item" value={variant.data.catalog_item_id} />
            <Meta label="SKU" value={variant.data.sku ?? "не указан"} />
            <Meta label="Barcode" value={variant.data.barcode ?? "не указан"} />
            <Meta label="Normalized" value={variant.data.normalized_title} />
          </dl>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl uppercase">Действия</h2>
          <button
            className="ink-button mt-4 w-full"
            onClick={() => addToWishlist.mutate({ catalog_variant_id: variant.data.id, priority: 10, status: "active" })}
          >
            В wishlist
          </button>
          <select className="ink-input mt-4" value={collectionId} onChange={(event) => setCollectionId(event.target.value)}>
            <option value="">Выберите коллекцию</option>
            {collections.data?.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
          <button
            className="ink-button mt-3 w-full"
            disabled={!collectionId}
            onClick={() => addToCollection.mutate({ collectionId, payload: { catalog_variant_id: variant.data.id, quantity: 1 } })}
          >
            В коллекцию
          </button>
          {addToWishlist.error ? <ErrorMessage error={addToWishlist.error} /> : null}
          {addToCollection.error ? <ErrorMessage error={addToCollection.error} /> : null}
        </Panel>
      </div>
    </AppSection>
  );
}

function CatalogCreatePanel() {
  const { data: categories = [] } = useCategories();
  const itemForm = useForm<z.infer<typeof itemSchema>>({
    resolver: zodResolver(itemSchema),
    defaultValues: { category_id: "", canonical_title: "", normalized_title: "", description: "", release_year: "", status: "active" },
  });
  const variantForm = useForm<z.infer<typeof variantSchema>>({
    resolver: zodResolver(variantSchema),
    defaultValues: { catalog_item_id: "", canonical_title: "", normalized_title: "", sku: "", barcode: "", release_date: "", status: "active" },
  });
  const createItem = useApiMutation(mutations.createCatalogItem, [["catalog-items"]]);
  const createVariant = useApiMutation(mutations.createCatalogVariant, [["catalog-variants"]]);

  return (
    <Panel>
      <h2 className="font-display text-2xl uppercase">Создать item / variant</h2>
      <div className="mt-4 grid gap-5 lg:grid-cols-2">
        <form className="grid gap-3" onSubmit={itemForm.handleSubmit((values) => createItem.mutate(values))}>
          <select className="ink-input" {...itemForm.register("category_id")}>
            <option value="">Категория</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
          <FieldError message={itemForm.formState.errors.category_id?.message} />
          <input className="ink-input" placeholder="Название item" {...itemForm.register("canonical_title", { onChange: (event) => itemForm.setValue("normalized_title", normalizeTitle(event.target.value)) })} />
          <input className="ink-input" placeholder="normalized_title" {...itemForm.register("normalized_title")} />
          <input className="ink-input" placeholder="Год релиза" {...itemForm.register("release_year")} />
          <textarea className="ink-input min-h-24" placeholder="Описание" {...itemForm.register("description")} />
          <button className="ink-button">Создать item</button>
        </form>
        <form className="grid gap-3" onSubmit={variantForm.handleSubmit((values) => createVariant.mutate(values))}>
          <input className="ink-input" placeholder="Catalog item ID" {...variantForm.register("catalog_item_id")} />
          <input className="ink-input" placeholder="Название variant" {...variantForm.register("canonical_title", { onChange: (event) => variantForm.setValue("normalized_title", normalizeTitle(event.target.value)) })} />
          <input className="ink-input" placeholder="normalized_title" {...variantForm.register("normalized_title")} />
          <input className="ink-input" placeholder="SKU" {...variantForm.register("sku")} />
          <input className="ink-input" placeholder="Barcode" {...variantForm.register("barcode")} />
          <input className="ink-input" type="date" {...variantForm.register("release_date")} />
          <button className="ink-button">Создать variant</button>
        </form>
      </div>
      {createItem.error ? <ErrorMessage error={createItem.error} /> : null}
      {createVariant.error ? <ErrorMessage error={createVariant.error} /> : null}
    </Panel>
  );
}

function AppSection({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      <div className="grid gap-5">{children}</div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-black uppercase text-muted">{label}</dt>
      <dd className="break-all font-bold">{value}</dd>
    </div>
  );
}

function WrappedError({ error }: { error: unknown }) {
  return <ErrorMessage error={error} />;
}

function WrappedLoading() {
  return <EmptyState title="Загрузка" text="Достаём карточку с полки." />;
}
