"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  mutations,
  useApiMutation,
  useCategories,
  useCollectionItems,
  useCollections,
  useRequests,
  useWishlist,
} from "@/shared/api/hooks";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";
import { date, money } from "@/shared/lib/format";

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
  const form = useForm<z.infer<typeof collectionSchema>>({
    resolver: zodResolver(collectionSchema),
    defaultValues: { name: "", description: "", visibility: "private" },
  });
  const create = useApiMutation(mutations.createCollection, [["collections"]]);

  return (
    <>
      <PageHeader title="Коллекции" subtitle="Личные полки пользователя: private, unlisted или public." />
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
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {collections.data?.map((collection) => (
          <Link key={collection.id} href={`/collections/${collection.id}`} className="ink-panel p-4 transition hover:-translate-y-0.5">
            <p className="font-display text-2xl uppercase">{collection.name}</p>
            <p className="mt-2 text-muted">{collection.description ?? "Без описания"}</p>
            <p className="mt-4 text-sm font-black uppercase text-accent">{collection.visibility}</p>
          </Link>
        ))}
      </div>
    </>
  );
}

export function CollectionDetailPage() {
  const params = useParams<{ id: string }>();
  const items = useCollectionItems(params.id);

  return (
    <>
      <PageHeader title="Коллекция" subtitle="Пока бэкенд отдаёт items отдельным списком, без раскрытия названий вариантов." />
      <Panel>
        <div className="grid gap-3">
          {items.data?.map((item) => (
            <div key={item.id} className="rounded-lg border-2 border-border p-3">
              <Link className="font-black text-accent" href={`/catalog/variants/${item.catalog_variant_id}`}>
                Variant {item.catalog_variant_id}
              </Link>
              <p className="mt-1 text-sm text-muted">
                {item.quantity} шт. · {item.condition ?? "состояние не указано"} · {money(item.purchase_price, item.purchase_currency)}
              </p>
              {item.comment ? <p className="mt-2">{item.comment}</p> : null}
            </div>
          ))}
          {items.data?.length === 0 ? <EmptyState title="Пусто" text="Добавьте variant из каталога." href="/catalog" action="В каталог" /> : null}
        </div>
      </Panel>
    </>
  );
}

export function WishlistPage() {
  const wishlist = useWishlist();
  const update = useApiMutation(({ id, status }: { id: string; status: string }) => mutations.updateWishlistItem(id, { status }), [["wishlist"]]);
  const remove = useApiMutation((id: string) => mutations.deleteWishlistItem(id), [["wishlist"]]);

  return (
    <>
      <PageHeader title="Wishlist" subtitle="Желания могут быть связаны либо с catalog_variant_id, либо с catalog_request_id до модерации." action={<Link className="ink-button ink-button-accent" href="/requests/new">Создать заявку</Link>} />
      <div className="grid gap-4">
        {wishlist.data?.map((item) => (
          <Panel key={item.id}>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <StatusBadge status={item.status} />
                <p className="mt-3 break-all font-black">
                  {item.catalog_variant_id ? "Variant: " : "Request: "}
                  {item.catalog_variant_id ?? item.catalog_request_id}
                </p>
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
      {wishlist.data?.length === 0 ? <EmptyState title="Wishlist пуст" text="Создайте заявку или добавьте variant из каталога." href="/catalog" action="В каталог" /> : null}
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
  const { data: categories = [] } = useCategories();
  const form = useForm<z.infer<typeof requestSchema>>({
    resolver: zodResolver(requestSchema),
    defaultValues: { category_id: "", raw_title: "", description: "", source_url: "", add_to_wishlist: true, target_price: "", currency: "RUB", priority: 10, comment: "" },
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
