"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  mutations,
  useApiMutation,
  useCategories,
  useCollectionContents,
  useCollections,
  useRequests,
  useWishlist,
  useWishlistDetailed,
} from "@/shared/api/hooks";
import { ItemDisplay } from "@/shared/components/item-display";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";
import { date, money } from "@/shared/lib/format";
import type { CollectionItem, CollectionItemDetailed } from "@/shared/types/domain";

const collectionSchema = z.object({
  name: z.string().min(1, "Название обязательно."),
  description: z.string().optional(),
  visibility: z.enum(["private", "unlisted", "public"]),
});

const requestSchema = z.object({
  category_id: z.string().min(1, "Выберите категорию."),
  raw_title: z.string().min(1, "Название обязательно."),
  description: z.string().optional(),
  source_url: z.string().url("Введите URL.").optional().or(z.literal("")),
  add_to_wishlist: z.boolean(),
  target_price: z.coerce.number().min(0).optional().or(z.literal("")),
  currency: z.string().min(3).max(3).optional().or(z.literal("")),
  priority: z.coerce.number().min(0).max(100),
  comment: z.string().optional(),
});

const collectionItemSchema = z.object({
  condition: z.enum(["sealed", "new", "opened", "used", "damaged"]),
  quantity: z.coerce.number().int().min(1, "Количество должно быть не меньше 1."),
  purchase_price: z.coerce.number().min(0, "Цена не может быть отрицательной.").optional().or(z.literal("")),
  purchase_currency: z
    .string()
    .regex(/^[A-Z]{3}$/, "Валюта должна быть в формате RUB, USD, JPY.")
    .optional()
    .or(z.literal("")),
  purchase_date: z.string().optional(),
  comment: z.string().optional(),
});
type CollectionItemFormInput = z.input<typeof collectionItemSchema>;
type CollectionItemFormOutput = z.output<typeof collectionItemSchema>;

export function DashboardPage() {
  const wishlist = useWishlist();
  const requests = useRequests();
  const collections = useCollections();

  return (
    <>
      <PageHeader title="Дашборд" subtitle="Один экран для понимания: что ищем, что уже в коллекции и что висит на модерации." />
      <div className="grid gap-5 md:grid-cols-3">
        <Stat title="Wishlist" value={wishlist.data?.length ?? 0} href="/wishlist" />
        <Stat title="Заявки" value={requests.data?.length ?? 0} href="/requests" />
        <Stat title="Коллекции" value={collections.data?.length ?? 0} href="/collections" />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-2xl uppercase">Последние заявки</h2>
          <div className="mt-4 grid gap-3">
            {requests.data?.slice(0, 5).map((request) => (
              <Link key={request.id} href={`/requests/${request.id}`} className="flex items-center justify-between gap-3 rounded-lg border-2 border-border p-3 hover:bg-background">
                <span className="font-bold">{request.raw_title}</span>
                <StatusBadge status={request.status} />
              </Link>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl uppercase">Wishlist</h2>
          <div className="mt-4 grid gap-3">
            {wishlist.data?.slice(0, 5).map((item) => (
              <Link key={item.id} href="/wishlist" className="rounded-lg border-2 border-border p-3 hover:bg-background">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-bold">{item.catalog_variant_id ? "Catalog variant" : "Заявка"}: {item.catalog_variant_id ?? item.catalog_request_id}</span>
                  <StatusBadge status={item.status} />
                </div>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </>
  );
}

export function CollectionsPage() {
  const collections = useCollections();
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedCollectionId = searchParams.get("collection_id") ?? "";
  const [query, setQuery] = useState("");
  const contents = useCollectionContents({
    collection_id: selectedCollectionId || undefined,
    query: query || undefined,
  });
  const form = useForm<z.infer<typeof collectionSchema>>({
    resolver: zodResolver(collectionSchema),
    defaultValues: { name: "", description: "", visibility: "private" },
  });
  const create = useApiMutation(mutations.createCollection, [["collections"], ["collection-contents"]]);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [savedItemId, setSavedItemId] = useState<string | null>(null);
  const updateItem = useApiMutation(
    ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      mutations.updateCollectionItem(id, payload),
    [["collection-contents"], ["collection-items"]],
  );
  const deleteItem = useApiMutation((id: string) => mutations.deleteCollectionItem(id), [["collection-contents"], ["collection-items"]]);

  return (
    <>
      <PageHeader title="Коллекция" subtitle="Все предметы из ваших коллекций на одном экране. Конкретная коллекция здесь работает как фильтр." />
      <Panel>
        <form className="grid gap-3 md:grid-cols-[1fr_1fr_180px_auto]" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
          <input className="ink-input" placeholder="Название коллекции" {...form.register("name")} />
          <input className="ink-input" placeholder="Описание" {...form.register("description")} />
          <select className="ink-input" {...form.register("visibility")}>
            <option value="private">private</option>
            <option value="unlisted">unlisted</option>
            <option value="public">public</option>
          </select>
          <button className="ink-button">Создать</button>
        </form>
        <FieldError message={form.formState.errors.name?.message} />
        {create.error ? <ErrorMessage error={create.error} /> : null}
      </Panel>
      <Panel className="mt-5">
        <div className="grid gap-3 md:grid-cols-[220px_1fr_auto]">
          <select
            className="ink-input"
            value={selectedCollectionId}
            onChange={(event) => {
              const value = event.target.value;
              router.push(value ? `/collections?collection_id=${value}` : "/collections");
            }}
          >
            <option value="">Все коллекции</option>
            {collections.data?.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
          <input
            className="ink-input"
            placeholder="Поиск по названию предмета"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Link className="ink-button" href="/catalog">
            Найти предмет
          </Link>
        </div>
      </Panel>
      <div className="mt-5 grid gap-4">
        {contents.isLoading ? <EmptyState title="Загрузка" text="Собираем предметы из ваших коллекций." /> : null}
        {contents.error ? <ErrorMessage error={contents.error} /> : null}
        {contents.data?.map((item) => (
          <CollectionItemCard
            key={item.id}
            item={item}
            isEditing={editingItemId === item.id}
            isSaving={updateItem.isPending}
            error={updateItem.error}
            saved={savedItemId === item.id}
            onEdit={() => setEditingItemId(editingItemId === item.id ? null : item.id)}
            onCancel={() => setEditingItemId(null)}
            onDelete={() => deleteItem.mutate(item.id)}
            onSubmit={async (payload) => {
              const updated = await updateItem.mutateAsync({ id: item.id, payload });
              setSavedItemId(updated.id);
              setEditingItemId(null);
            }}
          />
        ))}
        {contents.data?.length === 0 ? (
          <EmptyState title="Коллекция пуста" text="Найдите первый предмет в каталоге или создайте коллекцию выше." href="/catalog" action="В каталог" />
        ) : null}
        {deleteItem.error ? <ErrorMessage error={deleteItem.error} /> : null}
      </div>
    </>
  );
}

export function CollectionDetailPage() {
  const params = useParams<{ id: string }>();
  const items = useCollectionContents({ collection_id: params.id });
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [savedItemId, setSavedItemId] = useState<string | null>(null);
  const updateItem = useApiMutation(
    ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      mutations.updateCollectionItem(id, payload),
    [["collection-items", params.id]],
  );
  const deleteItem = useApiMutation((id: string) => mutations.deleteCollectionItem(id), [["collection-items", params.id]]);

  return (
    <>
      <PageHeader title="Коллекция" subtitle="Предметы коллекции можно обновлять точечно: состояние, количество, цену, дату покупки и заметку." />
      <Panel>
        <div className="grid gap-3">
          {items.data?.map((item) => (
            <CollectionItemCard
              key={item.id}
              item={item}
              isEditing={editingItemId === item.id}
              isSaving={updateItem.isPending}
              error={updateItem.error}
              saved={savedItemId === item.id}
              onEdit={() => setEditingItemId(editingItemId === item.id ? null : item.id)}
              onCancel={() => setEditingItemId(null)}
              onDelete={() => deleteItem.mutate(item.id)}
              onSubmit={async (payload) => {
                const updated = await updateItem.mutateAsync({ id: item.id, payload });
                setSavedItemId(updated.id);
                setEditingItemId(null);
              }}
            />
          ))}
          {items.data?.length === 0 ? <EmptyState title="Пусто" text="Добавьте variant из каталога." href="/catalog" action="В каталог" /> : null}
        </div>
        {deleteItem.error ? <ErrorMessage error={deleteItem.error} /> : null}
      </Panel>
    </>
  );
}

function CollectionItemCard({
  item,
  isEditing,
  isSaving,
  error,
  saved,
  onEdit,
  onCancel,
  onDelete,
  onSubmit,
}: {
  item: CollectionItemDetailed;
  isEditing: boolean;
  isSaving: boolean;
  error: unknown;
  saved: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onSubmit: (payload: CollectionItemFormOutput) => Promise<void>;
}) {
  return (
    <Panel>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <ItemDisplay item={item} titleClassName="text-xl" />
          <p className="mt-2 text-sm text-muted">
            {item.collection_name} · {item.quantity} шт. · {item.condition ?? "состояние не указано"} ·{" "}
            {money(item.purchase_price, item.purchase_currency)}
          </p>
          <p className="text-sm text-muted">Покупка: {date(item.purchase_date)}</p>
          {item.comment ? <p className="mt-2">{item.comment}</p> : null}
          {saved ? <p className="mt-2 text-sm font-black uppercase text-accent">Сохранено</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="ink-button" onClick={onEdit}>
            {isEditing ? "Закрыть" : "Редактировать"}
          </button>
          <button className="ink-button ink-button-danger" onClick={onDelete}>
            Удалить
          </button>
        </div>
      </div>
      {isEditing ? (
        <CollectionItemEditForm
          item={item}
          isSaving={isSaving}
          error={error}
          onCancel={onCancel}
          onSubmit={onSubmit}
        />
      ) : null}
    </Panel>
  );
}

function CollectionItemEditForm({
  item,
  isSaving,
  error,
  onCancel,
  onSubmit,
}: {
  item: CollectionItem;
  isSaving: boolean;
  error: unknown;
  onCancel: () => void;
  onSubmit: (payload: CollectionItemFormOutput) => Promise<void>;
}) {
  const form = useForm<CollectionItemFormInput, undefined, CollectionItemFormOutput>({
    resolver: zodResolver(collectionItemSchema),
    defaultValues: {
      condition: item.condition ?? "new",
      quantity: item.quantity,
      purchase_price: item.purchase_price ? Number(item.purchase_price) : "",
      purchase_currency: item.purchase_currency ?? "",
      purchase_date: item.purchase_date ?? "",
      comment: item.comment ?? "",
    },
  });

  return (
    <form className="mt-4 grid gap-3 border-t-2 border-border pt-4" onSubmit={form.handleSubmit(onSubmit)}>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="grid gap-1 text-sm font-bold">
          Состояние
          <select className="ink-input" {...form.register("condition")}>
            <option value="sealed">sealed</option>
            <option value="new">new</option>
            <option value="opened">opened</option>
            <option value="used">used</option>
            <option value="damaged">damaged</option>
          </select>
        </label>
        <label className="grid gap-1 text-sm font-bold">
          Количество
          <input className="ink-input" type="number" min="1" {...form.register("quantity")} />
        </label>
        <label className="grid gap-1 text-sm font-bold">
          Дата покупки
          <input className="ink-input" type="date" {...form.register("purchase_date")} />
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="grid gap-1 text-sm font-bold">
          Цена
          <input className="ink-input" inputMode="decimal" placeholder="1200" {...form.register("purchase_price")} />
        </label>
        <label className="grid gap-1 text-sm font-bold">
          Валюта
          <input className="ink-input" placeholder="RUB" maxLength={3} {...form.register("purchase_currency")} />
        </label>
      </div>
      <label className="grid gap-1 text-sm font-bold">
        Комментарий
        <textarea className="ink-input min-h-20" placeholder="Заметка о предмете" {...form.register("comment")} />
      </label>
      <div>
        <FieldError
          message={
            form.formState.errors.quantity?.message ??
            form.formState.errors.purchase_price?.message ??
            form.formState.errors.purchase_currency?.message
          }
        />
        {error ? <ErrorMessage error={error} /> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        <button className="ink-button ink-button-accent" disabled={isSaving}>
          {isSaving ? "Сохраняем..." : "Сохранить"}
        </button>
        <button className="ink-button" type="button" onClick={onCancel}>
          Отмена
        </button>
      </div>
    </form>
  );
}

export function WishlistPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const wishlist = useWishlistDetailed({ status: status || undefined, query: query || undefined });
  const update = useApiMutation(({ id, status }: { id: string; status: string }) => mutations.updateWishlistItem(id, { status }), [["wishlist"], ["wishlist-detailed"]]);
  const remove = useApiMutation((id: string) => mutations.deleteWishlistItem(id), [["wishlist"], ["wishlist-detailed"]]);

  return (
    <>
      <PageHeader title="Wishlist" subtitle="Желаемые предметы: активные, ожидающие добавления в каталог, купленные и архивные." action={<Link className="ink-button ink-button-accent" href="/requests/new">Создать заявку</Link>} />
      <Panel className="mb-5">
        <div className="grid gap-3 md:grid-cols-[220px_1fr_auto]">
          <select className="ink-input" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">Все статусы</option>
            <option value="active">active</option>
            <option value="pending_moderation">Ждёт добавления</option>
            <option value="rejected">rejected</option>
            <option value="purchased">purchased</option>
            <option value="archived">archived</option>
          </select>
          <input
            className="ink-input"
            placeholder="Поиск по названию"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Link className="ink-button" href="/catalog">
            В каталог
          </Link>
        </div>
      </Panel>
      <div className="grid gap-4">
        {wishlist.data?.map((item) => (
          <Panel key={item.id}>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <StatusBadge status={item.status} />
                <ItemDisplay item={item} className="mt-3" titleClassName="text-xl" />
                {item.catalog_request_id ? <p className="mt-1 text-sm font-bold text-warning">Ждёт добавления в каталог</p> : null}
                <p className="text-muted">{money(item.target_price, item.currency)} · priority {item.priority}</p>
                {item.comment ? <p className="mt-2">{item.comment}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="ink-button" onClick={() => update.mutate({ id: item.id, status: "purchased" })}>Куплено</button>
                <button className="ink-button" onClick={() => update.mutate({ id: item.id, status: "archived" })}>Архив</button>
                <button className="ink-button ink-button-danger" onClick={() => remove.mutate(item.id)}>Удалить</button>
              </div>
            </div>
          </Panel>
        ))}
      </div>
      {wishlist.isLoading ? <EmptyState title="Загрузка" text="Собираем wishlist." /> : null}
      {wishlist.error ? <ErrorMessage error={wishlist.error} /> : null}
      {wishlist.data?.length === 0 ? <EmptyState title="Wishlist пуст" text="Найдите предмет в каталоге или создайте заявку." href="/catalog" action="В каталог" /> : null}
    </>
  );
}

export function RequestsPage() {
  const requests = useRequests();
  return (
    <>
      <PageHeader title="Мои заявки" subtitle="Путь новой позиции: pending -> moderation -> approved/rejected/duplicate." action={<Link className="ink-button ink-button-accent" href="/requests/new">Новая заявка</Link>} />
      <div className="grid gap-4">
        {requests.data?.map((request) => (
          <Link key={request.id} href={`/requests/${request.id}`} className="ink-panel p-4 hover:bg-surface">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-2xl uppercase">{request.raw_title}</h2>
              <StatusBadge status={request.status} />
            </div>
            <p className="mt-2 text-muted">Создано: {date(request.created_at)}</p>
          </Link>
        ))}
      </div>
    </>
  );
}

export function NewRequestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const titleFromSearch = searchParams.get("title") ?? "";
  const { data: categories = [] } = useCategories();
  const form = useForm<z.infer<typeof requestSchema>>({
    resolver: zodResolver(requestSchema),
    defaultValues: {
      category_id: "",
      raw_title: titleFromSearch,
      description: "",
      source_url: "",
      add_to_wishlist: true,
      target_price: "",
      currency: "RUB",
      priority: 10,
      comment: "",
    },
  });
  const create = useApiMutation(mutations.createRequest, [["catalog-requests"], ["wishlist"]]);

  return (
    <>
      <PageHeader title="Новая заявка" subtitle="Если включить wishlist, после approve бэкенд перепривяжет item с catalog_request_id на catalog_variant_id." />
      <Panel>
        <form
          className="grid gap-4"
          onSubmit={form.handleSubmit(async (values) => {
            const payload = {
              category_id: values.category_id,
              raw_title: values.raw_title,
              description: values.description,
              source_url: values.source_url,
              proposed_data: {},
              wishlist: values.add_to_wishlist
                ? {
                    target_price: values.target_price,
                    currency: values.currency,
                    priority: values.priority,
                    comment: values.comment,
                  }
                : undefined,
            };
            const result = await create.mutateAsync(payload);
            router.push(`/requests/${result.request.id}`);
          })}
        >
          <select className="ink-input" {...form.register("category_id")}>
            <option value="">Категория</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
          <FieldError message={form.formState.errors.category_id?.message} />
          <input className="ink-input" placeholder="Название: том, выпуск, фигурка..." {...form.register("raw_title")} />
          <FieldError message={form.formState.errors.raw_title?.message} />
          <textarea className="ink-input min-h-28" placeholder="Описание, признаки, edition notes" {...form.register("description")} />
          <input className="ink-input" placeholder="Источник URL" {...form.register("source_url")} />
          <label className="flex items-center gap-2 font-bold">
            <input type="checkbox" {...form.register("add_to_wishlist")} />
            Сразу добавить в wishlist
          </label>
          <div className="grid gap-3 md:grid-cols-3">
            <input className="ink-input" placeholder="Целевая цена" {...form.register("target_price")} />
            <input className="ink-input" placeholder="RUB" {...form.register("currency")} />
            <input className="ink-input" type="number" placeholder="Priority" {...form.register("priority")} />
          </div>
          <textarea className="ink-input min-h-20" placeholder="Комментарий для wishlist" {...form.register("comment")} />
          {create.error ? <ErrorMessage error={create.error} /> : null}
          <button className="ink-button ink-button-accent">Отправить на модерацию</button>
        </form>
      </Panel>
    </>
  );
}

export function RequestDetailPage() {
  const params = useParams<{ id: string }>();
  const requests = useRequests();
  const request = requests.data?.find((item) => item.id === params.id);

  if (requests.isLoading) return <EmptyState title="Загрузка" text="Ищем заявку." />;
  if (!request) return <EmptyState title="Не найдено" text="Заявка не найдена среди ваших заявок." href="/requests" action="К заявкам" />;

  return (
    <>
      <PageHeader title={request.raw_title} subtitle={request.description ?? "Заявка без описания."} />
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={request.status} />
          <span className="font-bold text-muted">Обновлено: {date(request.updated_at)}</span>
        </div>
        <dl className="mt-5 grid gap-3">
          <Meta label="category_id" value={request.category_id} />
          <Meta label="approved_variant_id" value={request.approved_variant_id ?? "ещё нет"} />
          <Meta label="rejection_reason" value={request.rejection_reason ?? "нет"} />
          <Meta label="source_url" value={request.source_url ?? "нет"} />
        </dl>
      </Panel>
    </>
  );
}

function Stat({ title, value, href }: { title: string; value: number; href: string }) {
  return (
    <Link href={href} className="ink-panel p-5">
      <p className="text-sm font-black uppercase text-accent">{title}</p>
      <p className="font-display text-5xl">{value}</p>
    </Link>
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
