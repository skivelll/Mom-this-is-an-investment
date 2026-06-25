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
  useCollectionContents,
  useCollections,
  useWishlistDetailed,
} from "@/shared/api/hooks";
import { canEditCatalog, useMe } from "@/shared/auth/use-auth";
import { ItemDisplay } from "@/shared/components/item-display";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";
import { date, normalizeTitle } from "@/shared/lib/format";
import type { CatalogVariant, CollectionItemDetailed, WishlistItemDetailed } from "@/shared/types/domain";

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
  const [hideInCollection, setHideInCollection] = useState(false);
  const [hideInWishlist, setHideInWishlist] = useState(false);
  const [hideInBoth, setHideInBoth] = useState(false);
  const { data: categories = [] } = useCategories();
  const variants = useCatalogVariants({ query: query || undefined, category_id: categoryId || undefined });
  const items = useCatalogItems({ query: query || undefined, category_id: categoryId || undefined });
  const collections = useCollections();
  const collectionContents = useCollectionContents({});
  const wishlist = useWishlistDetailed({});
  const { data: me } = useMe();
  const collectionItems = collectionContents.data ?? [];
  const wishlistItems = wishlist.data ?? [];
  const visibleVariants = (variants.data ?? []).filter((variant) => {
    const inCollection = collectionItems.some((item) => item.catalog_variant_id === variant.id);
    const inWishlist = wishlistItems.some((item) => item.catalog_variant_id === variant.id);

    if (hideInBoth && inCollection && inWishlist) return false;
    if (hideInCollection && inCollection) return false;
    if (hideInWishlist && inWishlist) return false;
    return true;
  });

  return (
    <AppSection
      title="Каталог"
      subtitle="Найдите предмет, добавьте его в коллекцию или wishlist. Если предмета нет, создайте заявку."
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
        <div className="mt-4 flex flex-wrap gap-3">
          <CatalogFilterCheckbox
            checked={hideInCollection}
            label="Не показывать то, что уже в коллекции"
            onChange={setHideInCollection}
          />
          <CatalogFilterCheckbox
            checked={hideInWishlist}
            label="Не показывать то, что уже в wishlist"
            onChange={setHideInWishlist}
          />
          <CatalogFilterCheckbox
            checked={hideInBoth}
            label="Не показывать то, что уже и в коллекции, и в wishlist"
            onChange={setHideInBoth}
          />
        </div>
      </Panel>

      {canEditCatalog(me?.role) ? <CatalogCreatePanel /> : null}

      <div className="grid gap-5">
        <Panel>
          <h2 className="font-display text-2xl uppercase">Предметы</h2>
          {variants.error ? <ErrorMessage error={variants.error} /> : null}
          <div className="mt-4 grid gap-3">
            {visibleVariants.map((variant) => (
              <CatalogSearchResult
                key={variant.id}
                variant={variant}
                collections={collections.data ?? []}
                collectionMatches={collectionItems.filter(
                  (item) => item.catalog_variant_id === variant.id,
                )}
                wishlistMatches={wishlistItems.filter(
                  (item) => item.catalog_variant_id === variant.id,
                )}
              />
            ))}
            {variants.data?.length === 0 ? (
              <EmptyState
                title="Ничего не нашли"
                text="Создайте заявку: модератор превратит её в item/variant каталога."
                href={`/requests/new?title=${encodeURIComponent(query)}`}
                action="Создать заявку"
              />
            ) : null}
            {variants.data && variants.data.length > 0 && visibleVariants.length === 0 ? (
              <EmptyState
                title="Всё скрыто фильтрами"
                text="Отключите один из фильтров наличия, чтобы снова увидеть предметы."
              />
            ) : null}
          </div>
        </Panel>
        {canEditCatalog(me?.role) ? <Panel>
          <h2 className="font-display text-2xl uppercase">Базовые записи каталога</h2>
          <div className="mt-4 grid gap-3">
            {items.data?.map((item) => (
              <Link className="rounded-lg border-2 border-border p-3 transition hover:bg-background" href={`/catalog/items/${item.id}`} key={item.id}>
                <p className="font-black">{item.canonical_title}</p>
                <p className="text-sm text-muted">{item.release_year ?? "год неизвестен"}</p>
              </Link>
            ))}
          </div>
        </Panel> : null}
      </div>
    </AppSection>
  );
}

function CatalogFilterCheckbox({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 rounded-lg border-2 border-border bg-background px-3 py-2 text-sm font-bold">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      {label}
    </label>
  );
}

function CatalogSearchResult({
  variant,
  collections,
  collectionMatches,
  wishlistMatches,
}: {
  variant: CatalogVariant;
  collections: { id: string; name: string }[];
  collectionMatches: CollectionItemDetailed[];
  wishlistMatches: WishlistItemDetailed[];
}) {
  const [collectionId, setCollectionId] = useState("");
  const addToWishlist = useApiMutation(mutations.addWishlistItem, [["wishlist"], ["wishlist-detailed"]]);
  const addToCollection = useApiMutation(
    ({ collectionId, payload }: { collectionId: string; payload: Record<string, unknown> }) =>
      mutations.addCollectionItem(collectionId, payload),
    [["collections"], ["collection-contents"]],
  );

  return (
    <div className="rounded-lg border-2 border-border p-3">
      <div className="grid gap-3 lg:grid-cols-[1fr_360px] lg:items-start">
        <Link href={`/catalog/variants/${variant.id}`} className="block hover:text-accent">
          <ItemDisplay
            item={{
              item_title: variant.item_title ?? variant.canonical_title,
              variant_label: variant.variant_label,
            }}
            titleClassName="text-xl"
          />
          <CatalogPresence collectionMatches={collectionMatches} wishlistMatches={wishlistMatches} />
        </Link>
        <div className="grid gap-2 md:grid-cols-[1fr_auto_auto] lg:grid-cols-1">
          <select className="ink-input" value={collectionId} onChange={(event) => setCollectionId(event.target.value)}>
            <option value="">Выберите коллекцию</option>
            {collections.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
          <button
            className="ink-button"
            disabled={!collectionId}
            onClick={() => addToCollection.mutate({ collectionId, payload: { catalog_variant_id: variant.id, quantity: 1 } })}
          >
            В коллекцию
          </button>
          <button className="ink-button" onClick={() => addToWishlist.mutate({ catalog_variant_id: variant.id, priority: 10 })}>
            В wishlist
          </button>
        </div>
      </div>
      {addToWishlist.error ? <ErrorMessage error={addToWishlist.error} /> : null}
      {addToCollection.error ? <ErrorMessage error={addToCollection.error} /> : null}
    </div>
  );
}

function CatalogPresence({
  collectionMatches,
  wishlistMatches,
}: {
  collectionMatches: CollectionItemDetailed[];
  wishlistMatches: WishlistItemDetailed[];
}) {
  if (collectionMatches.length === 0 && wishlistMatches.length === 0) return null;

  const collectionGroups = groupCollectionPresence(collectionMatches);
  const wishlistGroups = groupWishlistPresence(wishlistMatches);

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {collectionGroups.map((item) => (
        <span key={item.collectionId} className="rounded-full border-2 border-success px-3 py-1 text-xs font-black uppercase text-success">
          В коллекции {item.collectionName} x{item.count}
        </span>
      ))}
      {wishlistGroups.map((item) => (
        <span key={item.status} className="rounded-full border-2 border-warning px-3 py-1 text-xs font-black uppercase text-warning">
          В wishlist {wishlistStatusLabel(item.status)} x{item.count}
        </span>
      ))}
    </div>
  );
}

function groupCollectionPresence(items: CollectionItemDetailed[]) {
  const groups = new Map<string, { collectionId: string; collectionName: string; count: number }>();
  items.forEach((item) => {
    const current = groups.get(item.collection_id);
    if (current) {
      current.count += item.quantity;
      return;
    }
    groups.set(item.collection_id, {
      collectionId: item.collection_id,
      collectionName: item.collection_name,
      count: item.quantity,
    });
  });
  return Array.from(groups.values());
}

function groupWishlistPresence(items: WishlistItemDetailed[]) {
  const groups = new Map<WishlistItemDetailed["status"], { status: WishlistItemDetailed["status"]; count: number }>();
  items.forEach((item) => {
    const current = groups.get(item.status);
    if (current) {
      current.count += 1;
      return;
    }
    groups.set(item.status, { status: item.status, count: 1 });
  });
  return Array.from(groups.values());
}

function wishlistStatusLabel(status: WishlistItemDetailed["status"]) {
  if (status === "pending_moderation") return "ждёт добавления";
  if (status === "active") return "active";
  if (status === "purchased") return "куплено";
  if (status === "archived") return "архив";
  if (status === "rejected") return "отклонено";
  return status;
}

export function CatalogItemPage({ id }: { id: string }) {
  const item = useCatalogItem(id);
  const variants = useCatalogVariants({ query: item.data?.canonical_title });

  if (item.error) return <WrappedError error={item.error} />;
  if (!item.data) return <WrappedLoading />;

  return (
    <AppSection title={item.data.canonical_title} subtitle={item.data.description ?? "Карточка предмета."}>
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={item.data.status} />
          <span className="font-bold text-muted">Год: {item.data.release_year ?? "не указан"}</span>
        </div>
      </Panel>
      <Panel>
        <h2 className="font-display text-2xl uppercase">Доступные издания</h2>
        <div className="mt-4 grid gap-3">
          {variants.data?.map((variant) => (
            <Link className="rounded-lg border-2 border-border p-3 font-bold hover:bg-background" href={`/catalog/variants/${variant.id}`} key={variant.id}>
              <ItemDisplay item={{ item_title: variant.item_title ?? variant.canonical_title, variant_label: variant.variant_label }} />
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
  const addToWishlist = useApiMutation(mutations.addWishlistItem, [["wishlist"], ["wishlist-detailed"]]);
  const addToCollection = useApiMutation(
    ({ collectionId, payload }: { collectionId: string; payload: Record<string, unknown> }) =>
      mutations.addCollectionItem(collectionId, payload),
    [["collections"], ["collection-contents"]],
  );
  const [collectionId, setCollectionId] = useState("");

  if (variant.error) return <WrappedError error={variant.error} />;
  if (!variant.data) return <WrappedLoading />;

  const displayItem = {
    item_title: variant.data.item_title ?? variant.data.canonical_title,
    variant_label: variant.data.variant_label,
  };

  return (
    <AppSection title={displayItem.item_title} subtitle={displayItem.variant_label ?? "Предмет из каталога."}>
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <Panel>
          <ItemDisplay item={displayItem} titleClassName="text-2xl" />
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={variant.data.status} />
            <span className="font-bold text-muted">Дата релиза: {date(variant.data.release_date)}</span>
          </div>
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

function WrappedError({ error }: { error: unknown }) {
  return <ErrorMessage error={error} />;
}

function WrappedLoading() {
  return <EmptyState title="Загрузка" text="Достаём карточку с полки." />;
}
