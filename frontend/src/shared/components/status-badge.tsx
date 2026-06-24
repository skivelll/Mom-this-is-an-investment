import { cn } from "@/shared/lib/cn";

const statusMap: Record<string, { label: string; hint: string; className: string }> = {
  active: {
    label: "Активно",
    hint: "Позиция доступна и используется.",
    className: "bg-success/15 text-success",
  },
  pending: {
    label: "Ждёт",
    hint: "Заявка создана и ждёт модерации.",
    className: "bg-warning/15 text-warning",
  },
  pending_moderation: {
    label: "На модерации",
    hint: "Позиция ждёт решения модераторов.",
    className: "bg-warning/15 text-warning",
  },
  in_review: {
    label: "В работе",
    hint: "Модератор уже смотрит заявку.",
    className: "bg-warning/15 text-warning",
  },
  needs_information: {
    label: "Нужны данные",
    hint: "Модератор запросил уточнение.",
    className: "bg-warning/15 text-warning",
  },
  approved: {
    label: "Одобрено",
    hint: "Заявка принята и связана с каталогом.",
    className: "bg-success/15 text-success",
  },
  rejected: {
    label: "Отклонено",
    hint: "Заявка или wishlist item отклонены.",
    className: "bg-danger/15 text-danger",
  },
  duplicate: {
    label: "Дубликат",
    hint: "Такой вариант уже есть в каталоге.",
    className: "bg-muted/15 text-muted",
  },
  cancelled: {
    label: "Отменено",
    hint: "Заявка отменена.",
    className: "bg-muted/15 text-muted",
  },
  purchased: {
    label: "Куплено",
    hint: "Позиция уже куплена.",
    className: "bg-success/15 text-success",
  },
  archived: {
    label: "Архив",
    hint: "Позиция скрыта из активного списка.",
    className: "bg-muted/15 text-muted",
  },
  draft: {
    label: "Черновик",
    hint: "Позиция ещё не опубликована.",
    className: "bg-muted/15 text-muted",
  },
};

export function StatusBadge({ status }: { status: string }) {
  const meta = statusMap[status] ?? {
    label: status,
    hint: "Неизвестный статус.",
    className: "bg-muted/15 text-muted",
  };

  return (
    <span
      title={meta.hint}
      className={cn(
        "inline-flex items-center rounded-full border-2 border-border px-2.5 py-1 text-xs font-black",
        meta.className,
      )}
    >
      {meta.label}
    </span>
  );
}
