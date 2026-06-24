"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { apiRequest } from "@/shared/api/client";
import { mutations, useApiMutation, useCatalogVariants, useModerationRequests } from "@/shared/api/hooks";
import { RoleGuard } from "@/shared/components/role-guard";
import { StatusBadge } from "@/shared/components/status-badge";
import { EmptyState, ErrorMessage, PageHeader, Panel } from "@/shared/components/ui";
import { normalizeTitle } from "@/shared/lib/format";
import type { CatalogRequest } from "@/shared/types/domain";

export function ModerationListPage() {
  const [status, setStatus] = useState("pending");
  const queue = useModerationRequests(status);

  return (
    <RoleGuard mode="moderator">
      <PageHeader title="Модерация" subtitle="Очередь пользовательских заявок. Approve создаёт или привязывает catalog item/variant." />
      <Panel>
        <select className="ink-input max-w-xs" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="pending">pending</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="duplicate">duplicate</option>
        </select>
      </Panel>
      <div className="mt-5 grid gap-4">
        {queue.data?.map((request) => (
          <Link key={request.id} href={`/moderation/requests/${request.id}`} className="ink-panel p-4 hover:bg-surface">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-2xl uppercase">{request.raw_title}</h2>
              <StatusBadge status={request.status} />
            </div>
            <p className="mt-2 text-muted">User: {request.created_by_id}</p>
          </Link>
        ))}
        {queue.data?.length === 0 ? <EmptyState title="Очередь пуста" text="Для этого статуса заявок нет." /> : null}
        {queue.error ? <ErrorMessage error={queue.error} /> : null}
      </div>
    </RoleGuard>
  );
}

export function ModerationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const request = useQuery({
    queryKey: ["moderation-request", params.id],
    queryFn: () => apiRequest<CatalogRequest>(`/moderation/catalog-requests/${params.id}`),
  });
  const variants = useCatalogVariants({ query: request.data?.raw_title });
  const approve = useApiMutation((payload: Record<string, unknown>) => mutations.approveRequest(params.id, payload), [["moderation-requests"]]);
  const reject = useApiMutation((payload: Record<string, unknown>) => mutations.rejectRequest(params.id, payload), [["moderation-requests"]]);
  const duplicate = useApiMutation((payload: Record<string, unknown>) => mutations.duplicateRequest(params.id, payload), [["moderation-requests"]]);
  const [existingVariantId, setExistingVariantId] = useState("");
  const [existingItemId, setExistingItemId] = useState("");
  const [reason, setReason] = useState("");

  if (request.isLoading) return <EmptyState title="Загрузка" text="Открываем заявку." />;
  if (request.error) return <ErrorMessage error={request.error} />;
  if (!request.data) return null;

  const title = request.data.raw_title;

  return (
    <RoleGuard mode="moderator">
      <PageHeader title={title} subtitle={request.data.description ?? "Описание не указано."} />
      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={request.data.status} />
            <span className="font-bold text-muted">Category: {request.data.category_id}</span>
          </div>
          <dl className="mt-5 grid gap-3">
            <Meta label="request_id" value={request.data.id} />
            <Meta label="source_url" value={request.data.source_url ?? "нет"} />
            <Meta label="approved_variant_id" value={request.data.approved_variant_id ?? "нет"} />
          </dl>
          <h2 className="mt-6 font-display text-2xl uppercase">Похожие варианты</h2>
          <div className="mt-3 grid gap-2">
            {variants.data?.map((variant) => (
              <button key={variant.id} className="rounded-lg border-2 border-border p-3 text-left font-bold hover:bg-background" onClick={() => setExistingVariantId(variant.id)}>
                {variant.canonical_title}
              </button>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl uppercase">Решение</h2>
          <input className="ink-input mt-4" placeholder="existing_variant_id" value={existingVariantId} onChange={(event) => setExistingVariantId(event.target.value)} />
          <input className="ink-input mt-3" placeholder="existing_catalog_item_id, если нужен новый variant" value={existingItemId} onChange={(event) => setExistingItemId(event.target.value)} />
          <button
            className="ink-button ink-button-accent mt-3 w-full"
            onClick={async () => {
              await approve.mutateAsync(
                existingVariantId
                  ? { existing_variant_id: existingVariantId }
                  : {
                      existing_catalog_item_id: existingItemId || undefined,
                      new_catalog_item: existingItemId
                        ? undefined
                        : {
                            category_id: request.data.category_id,
                            canonical_title: title,
                            normalized_title: normalizeTitle(title),
                            status: "active",
                          },
                      new_variant: {
                        canonical_title: title,
                        normalized_title: normalizeTitle(title),
                        status: "active",
                      },
                    },
              );
              router.push("/moderation/requests");
            }}
          >
            Approve
          </button>
          <button
            className="ink-button mt-3 w-full"
            disabled={!existingVariantId}
            onClick={async () => {
              await duplicate.mutateAsync({ existing_variant_id: existingVariantId });
              router.push("/moderation/requests");
            }}
          >
            Duplicate
          </button>
          <textarea className="ink-input mt-4 min-h-24" placeholder="Причина отклонения" value={reason} onChange={(event) => setReason(event.target.value)} />
          <button
            className="ink-button ink-button-danger mt-3 w-full"
            disabled={!reason}
            onClick={async () => {
              await reject.mutateAsync({ reason });
              router.push("/moderation/requests");
            }}
          >
            Reject
          </button>
          {approve.error ? <ErrorMessage error={approve.error} /> : null}
          {reject.error ? <ErrorMessage error={reject.error} /> : null}
          {duplicate.error ? <ErrorMessage error={duplicate.error} /> : null}
        </Panel>
      </div>
    </RoleGuard>
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
