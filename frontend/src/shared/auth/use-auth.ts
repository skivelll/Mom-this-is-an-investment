"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiRequest, clearToken, queryKeys, setToken } from "@/shared/api/client";
import type { User } from "@/shared/types/domain";

type LoginPayload = { email: string; password: string };
type RegisterPayload = LoginPayload & { username: string };
type TokenResponse = { access_token: string; token_type: "bearer" };

export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiRequest<User>("/auth/me"),
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LoginPayload) =>
      apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify(payload),
      }),
    onSuccess: async (data) => {
      setToken(data.access_token);
      await queryClient.invalidateQueries({ queryKey: queryKeys.me });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (payload: RegisterPayload) =>
      apiRequest<User>("/auth/register", {
        method: "POST",
        auth: false,
        body: JSON.stringify(payload),
      }),
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return () => {
    clearToken();
    queryClient.clear();
    router.push("/login");
  };
}

export function canModerate(role?: string) {
  return role === "moderator" || role === "senior_moderator" || role === "admin";
}

export function canEditCatalog(role?: string) {
  return role === "senior_moderator" || role === "admin";
}
