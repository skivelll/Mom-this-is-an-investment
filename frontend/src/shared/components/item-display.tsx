import { cn } from "@/shared/lib/cn";

export type ItemDisplayData = {
  item_title: string;
  variant_label?: string | null;
};

export function ItemDisplay({
  item,
  className,
  titleClassName,
}: {
  item: ItemDisplayData;
  className?: string;
  titleClassName?: string;
}) {
  return (
    <div className={className}>
      <p className={cn("font-black leading-tight", titleClassName)}>{item.item_title}</p>
      {item.variant_label ? <p className="mt-1 text-sm text-muted">{item.variant_label}</p> : null}
    </div>
  );
}
