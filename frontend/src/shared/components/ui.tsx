import Link from "next/link";
import { cn } from "@/shared/lib/cn";

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="mb-2 text-sm font-black uppercase tracking-wide text-accent">скетчбук</p>
        <h1 className="font-display text-3xl uppercase leading-none md:text-5xl">{title}</h1>
        {subtitle ? <p className="mt-3 max-w-2xl text-muted">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Panel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <section className={cn("ink-panel p-4 md:p-5", className)}>{children}</section>;
}

export function EmptyState({
  title,
  text,
  href,
  action,
}: {
  title: string;
  text: string;
  href?: string;
  action?: string;
}) {
  return (
    <Panel className="flex min-h-44 flex-col items-center justify-center text-center">
      <h2 className="font-display text-2xl uppercase">{title}</h2>
      <p className="mt-2 max-w-lg text-muted">{text}</p>
      {href && action ? (
        <Link className="ink-button mt-4" href={href}>
          {action}
        </Link>
      ) : null}
    </Panel>
  );
}

export function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-sm font-semibold text-danger">{message}</p>;
}

export function ErrorMessage({ error }: { error: unknown }) {
  const message =
    error && typeof error === "object" && "message" in error
      ? String((error as { message?: unknown }).message)
      : "Что-то пошло не так.";
  return <div className="ink-panel border-danger p-4 font-semibold text-danger">{message}</div>;
}
