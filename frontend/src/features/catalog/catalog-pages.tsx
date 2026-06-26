"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  mutations,
  useApiMutation,
  useAttributes,
  useCatalogItem,
  useCatalogMedia,
  useCatalogMediaConfig,
  useCatalogItems,
  useCatalogVariant,
  useCatalogVariants,
  useCategories,
  useCollectionContents,
  useCollections,
  useWishlistDetailed,
} from "@/shared/api/hooks";
import { canEditCatalog, canModerate, useMe } from "@/shared/auth/use-auth";
import { ItemDisplay } from "@/shared/components/item-display";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";
import { date, normalizeTitle } from "@/shared/lib/format";
import type {
  AttributeDefinition,
  CatalogAttributeValue,
  CatalogMedia,
  CatalogVariant,
  CollectionItemDetailed,
  WishlistItemDetailed,
} from "@/shared/types/domain";

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
              primary_image_url: variant.primary_image_url,
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
  const variants = useCatalogVariants({ catalog_item_id: id });
  const { data: me } = useMe();

  if (item.error) return <WrappedError error={item.error} />;
  if (!item.data) return <WrappedLoading />;

  return (
    <AppSection title={item.data.canonical_title} subtitle={item.data.description ?? "Карточка предмета."}>
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={item.data.status} />
          <span className="font-bold text-muted">Год: {item.data.release_year ?? "не указан"}</span>
        </div>
        <AttributeList attributes={item.data.attributes} />
      </Panel>
      {canModerate(me?.role) ? (
        <MediaManager catalogItemId={item.data.id} />
      ) : null}
      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-2xl uppercase">Доступные издания</h2>
          {canEditCatalog(me?.role) ? (
            <Link className="ink-button" href={`/catalog?item_id=${item.data.id}`}>
              Добавить разновидность
            </Link>
          ) : null}
        </div>
        <div className="mt-4 grid gap-3">
          {variants.data?.map((variant) => (
            <Link className="rounded-lg border-2 border-border p-3 font-bold hover:bg-background" href={`/catalog/variants/${variant.id}`} key={variant.id}>
              <ItemDisplay
                item={{
                  item_title: variant.item_title ?? variant.canonical_title,
                  variant_label: variant.variant_label,
                  primary_image_url: variant.primary_image_url,
                }}
              />
            </Link>
          ))}
          {variants.data?.length === 0 ? (
            <EmptyState
              title="Для предмета пока не добавлена разновидность"
              text="Его можно оформить, добавить изображение и позже создать конкретное издание."
            />
          ) : null}
        </div>
      </Panel>
      {canEditCatalog(me?.role) ? <CreateVariantForItemPanel itemId={item.data.id} /> : null}
    </AppSection>
  );
}

export function CatalogVariantPage({ id }: { id: string }) {
  const variant = useCatalogVariant(id);
  const collections = useCollections();
  const { data: me } = useMe();
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
    primary_image_url: variant.data.primary_image_url,
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
          <AttributeList attributes={variant.data.attributes} />
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
      {canModerate(me?.role) ? (
        <MediaManager catalogItemId={variant.data.catalog_item_id} catalogVariantId={variant.data.id} />
      ) : null}
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
  const itemCategoryId = itemForm.watch("category_id");
  const variantItemId = variantForm.watch("catalog_item_id");
  const itemAttributes = useAttributes(itemCategoryId);
  const [itemAttributeValues, setItemAttributeValues] = useState<Record<string, string | boolean>>({});
  const [variantAttributeValues, setVariantAttributeValues] = useState<Record<string, string | boolean>>({});
  const createItem = useApiMutation(mutations.createCatalogItem, [["catalog-items"]]);
  const createVariant = useApiMutation(mutations.createCatalogVariant, [["catalog-variants"]]);
  const variantItem = useCatalogItem(variantItemId);
  const variantAttributes = useAttributes(variantItem.data?.category_id);
  const availableItemAttributes = (itemAttributes.data ?? []).filter((attribute) => !attribute.is_variant_attribute);
  const availableVariantAttributes = (variantAttributes.data ?? []).filter((attribute) => attribute.is_variant_attribute);

  return (
    <Panel>
      <h2 className="font-display text-2xl uppercase">Создать item</h2>
      <div className="mt-4 grid gap-5 lg:grid-cols-2">
        <form
          className="grid gap-3"
          onSubmit={itemForm.handleSubmit((values) =>
            createItem.mutate({
              ...values,
              attributes: buildAttributePayload(availableItemAttributes, itemAttributeValues),
            })
          )}
        >
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
          <DynamicAttributeFields
            attributes={availableItemAttributes}
            values={itemAttributeValues}
            onChange={setItemAttributeValues}
          />
          <button className="ink-button" disabled={createItem.isPending}>
            {createItem.isPending ? "Создаём..." : "Создать item"}
          </button>
          {createItem.data ? (
            <div className="rounded-lg border-2 border-success p-3 text-sm font-bold text-success">
              Item создан. Теперь можно загрузить изображение или добавить разновидность.
              <div className="mt-3 flex flex-wrap gap-2">
                <Link className="ink-button" href={`/catalog/items/${createItem.data.id}`}>
                  Перейти к предмету
                </Link>
                <button
                  className="ink-button"
                  type="button"
                  onClick={() => variantForm.setValue("catalog_item_id", createItem.data.id)}
                >
                  Добавить разновидность
                </button>
              </div>
              <MediaManager catalogItemId={createItem.data.id} />
            </div>
          ) : null}
        </form>
        <form
          className="grid gap-3"
          onSubmit={variantForm.handleSubmit((values) =>
            createVariant.mutate({
              ...values,
              attributes: buildAttributePayload(availableVariantAttributes, variantAttributeValues),
            })
          )}
        >
          <h3 className="font-display text-xl uppercase">Добавить variant</h3>
          <input className="ink-input" placeholder="Catalog item ID" {...variantForm.register("catalog_item_id")} />
          <input className="ink-input" placeholder="Название variant" {...variantForm.register("canonical_title", { onChange: (event) => variantForm.setValue("normalized_title", normalizeTitle(event.target.value)) })} />
          <input className="ink-input" placeholder="normalized_title" {...variantForm.register("normalized_title")} />
          <input className="ink-input" placeholder="SKU" {...variantForm.register("sku")} />
          <input className="ink-input" placeholder="Barcode" {...variantForm.register("barcode")} />
          <input className="ink-input" type="date" {...variantForm.register("release_date")} />
          <DynamicAttributeFields
            attributes={availableVariantAttributes}
            values={variantAttributeValues}
            onChange={setVariantAttributeValues}
          />
          <button className="ink-button" disabled={createVariant.isPending}>
            {createVariant.isPending ? "Создаём..." : "Создать variant"}
          </button>
          {createVariant.data ? (
            <Link className="ink-button" href={`/catalog/variants/${createVariant.data.id}`}>
              Открыть variant
            </Link>
          ) : null}
        </form>
      </div>
      {createItem.error ? <ErrorMessage error={createItem.error} /> : null}
      {createVariant.error ? <ErrorMessage error={createVariant.error} /> : null}
    </Panel>
  );
}

function CreateVariantForItemPanel({ itemId }: { itemId: string }) {
  const item = useCatalogItem(itemId);
  const attributes = useAttributes(item.data?.category_id);
  const [values, setValues] = useState<Record<string, string | boolean>>({});
  const form = useForm<z.infer<typeof variantSchema>>({
    resolver: zodResolver(variantSchema),
    defaultValues: {
      catalog_item_id: itemId,
      canonical_title: "",
      normalized_title: "",
      sku: "",
      barcode: "",
      release_date: "",
      status: "active",
    },
  });
  const createVariant = useApiMutation(mutations.createCatalogVariant, [["catalog-variants"]]);
  const variantAttributes = (attributes.data ?? []).filter((attribute) => attribute.is_variant_attribute);

  return (
    <Panel>
      <h2 className="font-display text-2xl uppercase">Добавить разновидность</h2>
      <form
        className="mt-4 grid gap-3"
        onSubmit={form.handleSubmit((payload) =>
          createVariant.mutate({
            ...payload,
            catalog_item_id: itemId,
            attributes: buildAttributePayload(variantAttributes, values),
          })
        )}
      >
        <input className="ink-input" placeholder="Название variant" {...form.register("canonical_title", { onChange: (event) => form.setValue("normalized_title", normalizeTitle(event.target.value)) })} />
        <input className="ink-input" placeholder="normalized_title" {...form.register("normalized_title")} />
        <input className="ink-input" placeholder="SKU" {...form.register("sku")} />
        <input className="ink-input" placeholder="Barcode" {...form.register("barcode")} />
        <input className="ink-input" type="date" {...form.register("release_date")} />
        <DynamicAttributeFields
          attributes={variantAttributes}
          values={values}
          onChange={setValues}
        />
        <button className="ink-button" disabled={createVariant.isPending}>
          {createVariant.isPending ? "Создаём..." : "Создать variant"}
        </button>
        {createVariant.data ? (
          <Link className="ink-button" href={`/catalog/variants/${createVariant.data.id}`}>
            Открыть созданную разновидность
          </Link>
        ) : null}
      </form>
      {createVariant.error ? <ErrorMessage error={createVariant.error} /> : null}
    </Panel>
  );
}

function DynamicAttributeFields({
  attributes,
  values,
  onChange,
}: {
  attributes: AttributeDefinition[];
  values: Record<string, string | boolean>;
  onChange: (values: Record<string, string | boolean>) => void;
}) {
  if (attributes.length === 0) return null;

  return (
    <div className="grid gap-3 rounded-lg border-2 border-border p-3">
      <h3 className="font-display text-xl uppercase">Атрибуты</h3>
      {attributes.map((attribute) => {
        const value = values[attribute.id];
        const setValue = (nextValue: string | boolean) => onChange({ ...values, [attribute.id]: nextValue });
        if (attribute.value_type === "boolean") {
          return (
            <label key={attribute.id} className="flex items-center gap-2 font-bold">
              <input
                type="checkbox"
                checked={value === true}
                onChange={(event) => setValue(event.target.checked)}
              />
              {attribute.name}
              {attribute.is_required ? " *" : ""}
            </label>
          );
        }
        if (attribute.value_type === "reference") {
          const options = attribute.reference_options ?? [];
          return (
            <label key={attribute.id} className="grid gap-1 text-sm font-bold">
              {attribute.name}
              {attribute.is_required ? " *" : ""}
              <select
                className="ink-input"
                value={typeof value === "string" ? value : ""}
                onChange={(event) => setValue(event.target.value)}
              >
                <option value="">Не выбрано</option>
                {options.length === 0 ? (
                  <option value="" disabled>Нет значений справочника</option>
                ) : null}
                {options.map((reference) => (
                  <option key={reference.id} value={reference.id}>
                    {reference.canonical_name}
                  </option>
                ))}
              </select>
            </label>
          );
        }
        return (
          <label key={attribute.id} className="grid gap-1 text-sm font-bold">
            {attribute.name}
            {attribute.is_required ? " *" : ""}
            <input
              className="ink-input"
              type={attributeInputType(attribute)}
              value={typeof value === "string" ? value : ""}
              onChange={(event) => setValue(event.target.value)}
            />
          </label>
        );
      })}
    </div>
  );
}

function AttributeList({ attributes }: { attributes: CatalogAttributeValue[] }) {
  const visibleAttributes = attributes.filter((attribute) => attribute.display_value);
  if (visibleAttributes.length === 0) return null;
  return (
    <div className="mt-4 rounded-lg border-2 border-border p-3">
      <h3 className="font-display text-xl uppercase">Характеристики</h3>
      <dl className="mt-3 grid gap-2 sm:grid-cols-2">
        {visibleAttributes.map((attribute) => (
          <div key={attribute.id}>
            <dt className="text-xs font-black uppercase text-muted">{attribute.name}</dt>
            <dd className="font-bold">{attribute.display_value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function MediaManager({
  catalogItemId,
  catalogVariantId,
}: {
  catalogItemId: string;
  catalogVariantId?: string;
}) {
  const config = useCatalogMediaConfig();
  const media = useCatalogMedia({ catalog_item_id: catalogItemId, catalog_variant_id: catalogVariantId });
  const uploadUrl = useApiMutation(mutations.createCatalogMediaUploadUrl, []);
  const confirmUpload = useApiMutation(mutations.confirmCatalogMedia, [["catalog-media"], ["catalog-items"], ["catalog-variants"]]);
  const updateMedia = useApiMutation(
    ({ id, payload }: { id: string; payload: Record<string, unknown> }) => mutations.updateCatalogMedia(id, payload),
    [["catalog-media"], ["catalog-items"], ["catalog-variants"]],
  );
  const deleteMedia = useApiMutation(mutations.deleteCatalogMedia, [["catalog-media"], ["catalog-items"], ["catalog-variants"]]);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currentMedia = media.data ?? [];
  const maxSize = config.data?.max_upload_size_bytes ?? 0;
  const allowedTypes = config.data?.allowed_mime_types ?? [];

  function selectFile(nextFile: File | null) {
    setError(null);
    setFile(null);
    setPreviewUrl(null);
    if (!nextFile) return;
    if (allowedTypes.length > 0 && !allowedTypes.includes(nextFile.type)) {
      setError("Поддерживаются только JPEG, PNG и WebP.");
      return;
    }
    if (maxSize > 0 && nextFile.size > maxSize) {
      setError(`Файл слишком большой. Максимум: ${formatBytes(maxSize)}.`);
      return;
    }
    setFile(nextFile);
    setPreviewUrl(URL.createObjectURL(nextFile));
  }

  async function uploadSelectedFile() {
    if (!file) return;
    setError(null);
    try {
      const upload = await uploadUrl.mutateAsync({
        catalog_item_id: catalogItemId,
        catalog_variant_id: catalogVariantId,
        original_filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
      });
      const response = await fetch(upload.upload_url, {
        method: "PUT",
        headers: upload.headers,
        body: file,
      });
      if (!response.ok) throw new Error("Storage upload failed.");
      await confirmUpload.mutateAsync({
        catalog_item_id: catalogItemId,
        catalog_variant_id: catalogVariantId,
        object_key: upload.object_key,
        original_filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
        is_primary: currentMedia.length === 0,
      });
      setFile(null);
      setPreviewUrl(null);
    } catch {
      setError("Не удалось загрузить изображение. Предмет при этом сохранён.");
    }
  }

  return (
    <Panel>
      <h2 className="font-display text-2xl uppercase">Изображения</h2>
      <div className="mt-4 grid gap-3">
        <input
          className="ink-input"
          type="file"
          accept={allowedTypes.join(",")}
          onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
        />
        {file ? <p className="text-sm text-muted">{file.name} · {formatBytes(file.size)}</p> : null}
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img className="h-40 w-40 rounded-lg border-2 border-border object-cover" src={previewUrl} alt="Preview" />
        ) : null}
        <button
          className="ink-button"
          disabled={!file || uploadUrl.isPending || confirmUpload.isPending}
          onClick={uploadSelectedFile}
        >
          {uploadUrl.isPending || confirmUpload.isPending ? "Загружаем..." : "Загрузить"}
        </button>
        {error ? <p className="font-bold text-danger">{error}</p> : null}
        {media.error ? <ErrorMessage error={media.error} /> : null}
        <div className="grid gap-3 md:grid-cols-2">
          {currentMedia.map((item) => (
            <MediaCard
              key={item.id}
              media={item}
              isSaving={updateMedia.isPending || deleteMedia.isPending}
              onUpdate={(payload) => updateMedia.mutate({ id: item.id, payload })}
              onDelete={() => {
                if (window.confirm("Удалить изображение?")) deleteMedia.mutate(item.id);
              }}
            />
          ))}
        </div>
      </div>
    </Panel>
  );
}

function MediaCard({
  media,
  isSaving,
  onUpdate,
  onDelete,
}: {
  media: CatalogMedia;
  isSaving: boolean;
  onUpdate: (payload: Record<string, unknown>) => void;
  onDelete: () => void;
}) {
  const [altText, setAltText] = useState(media.alt_text ?? "");
  const [sortOrder, setSortOrder] = useState(String(media.sort_order));
  return (
    <div className="rounded-lg border-2 border-border p-3">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="h-36 w-full rounded-lg object-cover" src={media.url} alt={media.alt_text ?? media.original_filename} />
      <div className="mt-3 grid gap-2">
        <span className="text-sm font-black uppercase">{media.is_primary ? "Primary" : "Image"}</span>
        <span className="rounded-full border-2 border-border px-2 py-1 text-xs font-black uppercase">
          {media.processing_status === "ready"
            ? "Готово"
            : media.processing_status === "failed"
              ? "Ошибка обработки"
              : "Обрабатывается"}
        </span>
        {media.processing_error ? (
          <p className="text-xs font-bold text-danger">{media.processing_error}</p>
        ) : null}
        <input className="ink-input" value={altText} placeholder="Alt text" onChange={(event) => setAltText(event.target.value)} />
        <input className="ink-input" value={sortOrder} placeholder="sort_order" onChange={(event) => setSortOrder(event.target.value)} />
        <button className="ink-button" disabled={isSaving} onClick={() => onUpdate({ alt_text: altText, sort_order: Number(sortOrder) || 0 })}>
          Сохранить
        </button>
        {!media.is_primary ? (
          <button className="ink-button" disabled={isSaving} onClick={() => onUpdate({ is_primary: true })}>
            Сделать primary
          </button>
        ) : null}
        <button className="ink-button ink-button-danger" disabled={isSaving} onClick={onDelete}>
          Удалить
        </button>
      </div>
    </div>
  );
}

function buildAttributePayload(
  attributes: AttributeDefinition[],
  values: Record<string, string | boolean>,
) {
  return attributes
    .map((attribute) => {
      const value = values[attribute.id];
      if (value === undefined || value === "") return null;
      const base = { attribute_definition_id: attribute.id };
      if (attribute.value_type === "text") return { ...base, value_text: String(value) };
      if (attribute.value_type === "integer") return { ...base, value_integer: Number(value) };
      if (attribute.value_type === "decimal") return { ...base, value_decimal: String(value) };
      if (attribute.value_type === "boolean") return { ...base, value_boolean: Boolean(value) };
      if (attribute.value_type === "date") return { ...base, value_date: String(value) };
      if (attribute.value_type === "reference") return { ...base, reference_entity_id: String(value) };
      return null;
    })
    .filter((value) => value !== null);
}

function attributeInputType(attribute: AttributeDefinition) {
  if (attribute.value_type === "integer" || attribute.value_type === "decimal") return "number";
  if (attribute.value_type === "date") return "date";
  return "text";
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
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
