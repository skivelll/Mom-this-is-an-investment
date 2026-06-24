import Link from "next/link";
import { Panel } from "@/shared/components/ui";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center p-4">
      <Panel>
        <h1 className="font-display text-4xl uppercase">404</h1>
        <p className="mt-2 text-muted">Такой страницы на полке нет.</p>
        <Link href="/dashboard" className="ink-button mt-4">
          На главную
        </Link>
      </Panel>
    </main>
  );
}
