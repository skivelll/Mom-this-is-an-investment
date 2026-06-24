export function money(value?: string | number | null, currency?: string | null) {
  if (value === null || value === undefined || value === "") return "Цена не указана";
  return `${value} ${currency ?? "RUB"}`;
}

export function date(value?: string | null) {
  if (!value) return "Дата не указана";
  return new Intl.DateTimeFormat("ru-RU").format(new Date(value));
}

export function normalizeTitle(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function compactPayload<T extends Record<string, unknown>>(payload: T) {
  return Object.fromEntries(
    Object.entries(payload)
      .map(([key, value]) => [key, compactValue(value)] as const)
      .filter(([, value]) => value !== "" && value !== null && value !== undefined),
  ) as Partial<T>;
}

function compactValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(compactValue);
  if (value && typeof value === "object") return compactPayload(value as Record<string, unknown>);
  return value;
}
