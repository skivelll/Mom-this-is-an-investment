"use client";

import {
  ClipboardList,
  FolderKanban,
  Heart,
  Home,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { canModerate, useLogout, useMe } from "@/shared/auth/use-auth";
import { cn } from "@/shared/lib/cn";

const baseNav = [
  { href: "/dashboard", label: "Главная", icon: Home },
  { href: "/catalog", label: "Каталог", icon: Search },
  { href: "/collections", label: "Коллекции", icon: FolderKanban },
  { href: "/wishlist", label: "Вишлист", icon: Heart },
  { href: "/requests", label: "Мои заявки", icon: ClipboardList },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useLogout();
  const { data: me, isLoading, error } = useMe();

  useEffect(() => {
    if (error) router.push(`/login?next=${encodeURIComponent(pathname)}`);
  }, [error, pathname, router]);

  if (isLoading) return <div className="p-8 font-black">Загружаем полку...</div>;
  if (!me) return null;

  const nav = [
    ...baseNav,
    ...(canModerate(me.role) ? [{ href: "/moderation/requests", label: "Модерка", icon: ShieldCheck }] : []),
    ...(me.role === "admin" ? [{ href: "/admin/categories", label: "Админка", icon: Settings }] : []),
  ];

  return (
    <div className="min-h-screen md:grid md:grid-cols-[260px_1fr]">
      <aside className="border-b-2 border-border bg-surface p-4 md:min-h-screen md:border-b-0 md:border-r-2">
        <Link href="/dashboard" className="flex items-center gap-3">
          <Image
            src="/logo.png"
            alt="Мам, это инвестиция"
            width={74}
            height={74}
            className="rounded-lg border-2 border-border object-cover"
          />
          <div>
            <p className="font-display text-xl uppercase leading-none">Мам, это</p>
            <p className="font-display text-xl uppercase leading-none text-accent">инвестиция</p>
          </div>
        </Link>
        <nav className="mt-6 grid gap-2">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg border-2 border-transparent px-3 py-2 font-bold",
                  active && "border-border bg-background shadow-ink-sm",
                )}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-6 rounded-lg border-2 border-border bg-background p-3 text-sm">
          <p className="font-black">{me.username}</p>
          <p className="text-muted">{me.role}</p>
        </div>
        <button className="ink-button mt-4 w-full" onClick={logout}>
          <LogOut size={17} />
          Выйти
        </button>
      </aside>
      <main className="p-4 md:p-8">{children}</main>
      <nav className="fixed bottom-0 left-0 right-0 grid grid-cols-5 border-t-2 border-border bg-surface md:hidden">
        {baseNav.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="flex flex-col items-center p-2 text-[11px] font-bold">
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
