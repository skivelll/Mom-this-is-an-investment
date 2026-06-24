"use client";

export type ApiError = {
  status: number;
  message: string;
  details?: unknown;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "mti_access_token";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (options.auth !== false) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const error: ApiError = {
      status: response.status,
      message: normalizeError(payload) || response.statusText,
      details: payload,
    };
    if (response.status === 401) clearToken();
    throw error;
  }

  return payload as T;
}

function normalizeError(payload: unknown) {
  if (!payload || typeof payload !== "object") return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Проверьте поля формы.";
  return null;
}

export const queryKeys = {
  me: ["auth", "me"] as const,
  categories: ["admin", "categories"] as const,
  references: ["admin", "references"] as const,
  catalogItems: (params: unknown) => ["catalog-items", params] as const,
  catalogItem: (id: string) => ["catalog-item", id] as const,
  catalogVariants: (params: unknown) => ["catalog-variants", params] as const,
  catalogVariant: (id: string) => ["catalog-variant", id] as const,
  collections: ["collections"] as const,
  collectionItems: (id: string) => ["collection-items", id] as const,
  wishlist: ["wishlist"] as const,
  requests: ["catalog-requests"] as const,
  moderationRequests: ["moderation-requests"] as const,
};
