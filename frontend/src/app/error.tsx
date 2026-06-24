"use client";

import { ErrorMessage, Panel } from "@/shared/components/ui";

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center p-4">
      <Panel>
        <h1 className="font-display text-4xl uppercase">Сломалось</h1>
        <div className="mt-4">
          <ErrorMessage error={error} />
        </div>
        <button className="ink-button mt-4" onClick={reset}>
          Попробовать ещё раз
        </button>
      </Panel>
    </main>
  );
}
