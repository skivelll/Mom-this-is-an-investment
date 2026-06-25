"use client";

import { ImageOff } from "lucide-react";
import { useState } from "react";
import { cn } from "@/shared/lib/cn";

export type ItemDisplayData = {
  item_title: string;
  variant_label?: string | null;
  primary_image_url?: string | null;
};

export function ItemDisplay({
  item,
  className,
  titleClassName,
  imageClassName,
}: {
  item: ItemDisplayData;
  className?: string;
  titleClassName?: string;
  imageClassName?: string;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = item.primary_image_url && !imageFailed;

  return (
    <div className={cn("flex gap-3", className)}>
      <div
        className={cn(
          "grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-lg border-2 border-border bg-background",
          imageClassName,
        )}
      >
        {showImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={item.primary_image_url ?? ""}
            alt={item.item_title}
            className="h-full w-full object-cover"
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <ImageOff className="text-muted" size={24} />
        )}
      </div>
      <div className="min-w-0">
        <p className={cn("font-black leading-tight", titleClassName)}>{item.item_title}</p>
        {item.variant_label ? <p className="mt-1 text-sm text-muted">{item.variant_label}</p> : null}
      </div>
    </div>
  );
}
