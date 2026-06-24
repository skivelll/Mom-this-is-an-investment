"use client";

import { canEditCatalog, canModerate, useMe } from "@/shared/auth/use-auth";
import { Panel } from "@/shared/components/ui";
import type { UserRole } from "@/shared/types/domain";

type GuardMode = "admin" | "catalog_editor" | "moderator";

export function RoleGuard({
  mode,
  children,
}: {
  mode: GuardMode;
  children: React.ReactNode;
}) {
  const { data: me } = useMe();

  const allowed =
    mode === "admin"
      ? me?.role === "admin"
      : mode === "catalog_editor"
        ? canEditCatalog(me?.role)
        : canModerate(me?.role);

  if (!allowed) {
    return (
      <Panel>
        <h2 className="font-display text-2xl uppercase">403. Не эта дверь</h2>
        <p className="mt-2 text-muted">Нужна роль {roleLabel(mode)}. Текущая роль: {me?.role ?? "неизвестно"}.</p>
      </Panel>
    );
  }

  return children;
}

function roleLabel(mode: GuardMode): UserRole | "moderator+" | "senior_moderator+" {
  if (mode === "admin") return "admin";
  if (mode === "catalog_editor") return "senior_moderator+";
  return "moderator+";
}
