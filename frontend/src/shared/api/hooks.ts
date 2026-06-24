"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest, queryKeys } from "@/shared/api/client";
import { compactPayload } from "@/shared/lib/format";
import type {
  AttributeDefinition,
  CatalogItem,
  CatalogRequest,
  CatalogVariant,
  Category,
  Collection,
  CollectionItem,
  ReferenceEntity,
  WishlistItem,
} from "@/shared/types/domain";

type RequestCreateResponse = {
  request: CatalogRequest;
  wishlist_item: WishlistItem | null;
};

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => apiRequest<Category[]>("/admin/categories", { auth: false }),
  });
}

export function useCatalogVariants(params: { query?: string; category_id?: string }) {
  return useQuery({
    queryKey: queryKeys.catalogVariants(params),
    queryFn: () => apiRequest<CatalogVariant[]>(`/catalog/variants${toSearch(params)}`, { auth: false }),
  });
}

export function useCatalogItems(params: { query?: string; category_id?: string }) {
  return useQuery({
    queryKey: queryKeys.catalogItems(params),
    queryFn: () => apiRequest<CatalogItem[]>(`/catalog/items${toSearch(params)}`, { auth: false }),
  });
}

export function useCatalogItem(id: string) {
  return useQuery({
    queryKey: queryKeys.catalogItem(id),
    queryFn: () => apiRequest<CatalogItem>(`/catalog/items/${id}`, { auth: false }),
  });
}

export function useCatalogVariant(id: string) {
  return useQuery({
    queryKey: queryKeys.catalogVariant(id),
    queryFn: () => apiRequest<CatalogVariant>(`/catalog/variants/${id}`, { auth: false }),
  });
}

export function useCollections() {
  return useQuery({
    queryKey: queryKeys.collections,
    queryFn: () => apiRequest<Collection[]>("/collections"),
  });
}

export function useCollectionItems(collectionId: string) {
  return useQuery({
    queryKey: queryKeys.collectionItems(collectionId),
    queryFn: () => apiRequest<CollectionItem[]>(`/collections/${collectionId}/items`),
  });
}

export function useWishlist() {
  return useQuery({
    queryKey: queryKeys.wishlist,
    queryFn: () => apiRequest<WishlistItem[]>("/wishlist"),
  });
}

export function useRequests() {
  return useQuery({
    queryKey: queryKeys.requests,
    queryFn: () => apiRequest<CatalogRequest[]>("/catalog-requests"),
  });
}

export function useModerationRequests(status = "pending") {
  return useQuery({
    queryKey: [...queryKeys.moderationRequests, status],
    queryFn: () => apiRequest<CatalogRequest[]>(`/moderation/catalog-requests${toSearch({ status })}`),
  });
}

export function useReferences() {
  return useQuery({
    queryKey: queryKeys.references,
    queryFn: () => apiRequest<ReferenceEntity[]>("/admin/references", { auth: false }),
  });
}

export function useAttributes(categoryId?: string) {
  return useQuery({
    queryKey: ["admin", "attributes", categoryId],
    queryFn: () => apiRequest<AttributeDefinition[]>(`/admin/attributes?category_id=${categoryId}`),
    enabled: Boolean(categoryId),
  });
}

export function useApiMutation<TResponse, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TResponse>,
  invalidate: readonly unknown[][],
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await Promise.all(invalidate.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
    },
  });
}

export const mutations = {
  createRequest: (payload: Record<string, unknown>) =>
    apiRequest<RequestCreateResponse>("/catalog-requests", {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
  createCollection: (payload: Record<string, unknown>) =>
    apiRequest<Collection>("/collections", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  addCollectionItem: (collectionId: string, payload: Record<string, unknown>) =>
    apiRequest<CollectionItem>(`/collections/${collectionId}/items`, {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
  updateCollectionItem: (id: string, payload: Record<string, unknown>) =>
    apiRequest<CollectionItem>(`/collections/items/${id}`, {
      method: "PATCH",
      body: JSON.stringify(compactPayload(payload)),
    }),
  deleteCollectionItem: (id: string) => apiRequest<void>(`/collections/items/${id}`, { method: "DELETE" }),
  addWishlistItem: (payload: Record<string, unknown>) =>
    apiRequest<WishlistItem>("/wishlist", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  updateWishlistItem: (id: string, payload: Record<string, unknown>) =>
    apiRequest<WishlistItem>(`/wishlist/${id}`, { method: "PATCH", body: JSON.stringify(compactPayload(payload)) }),
  deleteWishlistItem: (id: string) => apiRequest<void>(`/wishlist/${id}`, { method: "DELETE" }),
  createCategory: (payload: Record<string, unknown>) =>
    apiRequest<Category>("/admin/categories", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  createAttribute: (payload: Record<string, unknown>) =>
    apiRequest<AttributeDefinition>("/admin/attributes", {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
  createReference: (payload: Record<string, unknown>) =>
    apiRequest<ReferenceEntity>("/admin/references", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  createCatalogItem: (payload: Record<string, unknown>) =>
    apiRequest<CatalogItem>("/catalog/items", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  createCatalogVariant: (payload: Record<string, unknown>) =>
    apiRequest<CatalogVariant>("/catalog/variants", { method: "POST", body: JSON.stringify(compactPayload(payload)) }),
  approveRequest: (id: string, payload: Record<string, unknown>) =>
    apiRequest<CatalogRequest>(`/moderation/catalog-requests/${id}/approve`, {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
  rejectRequest: (id: string, payload: Record<string, unknown>) =>
    apiRequest<CatalogRequest>(`/moderation/catalog-requests/${id}/reject`, {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
  duplicateRequest: (id: string, payload: Record<string, unknown>) =>
    apiRequest<CatalogRequest>(`/moderation/catalog-requests/${id}/duplicate`, {
      method: "POST",
      body: JSON.stringify(compactPayload(payload)),
    }),
};

function toSearch(params: Record<string, string | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}
