"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { mutations, useApiMutation, useAttributes, useCategories, useReferences } from "@/shared/api/hooks";
import { RoleGuard } from "@/shared/components/role-guard";
import { EmptyState, ErrorMessage, FieldError, PageHeader, Panel } from "@/shared/components/ui";

const categorySchema = z.object({
  name: z.string().min(1),
  slug: z.string().min(1),
  description: z.string().optional(),
  is_active: z.boolean(),
});

const attributeSchema = z.object({
  category_id: z.string().min(1),
  code: z.string().min(1),
  name: z.string().min(1),
  value_type: z.enum(["text", "integer", "decimal", "boolean", "date", "reference"]),
  is_required: z.boolean(),
  is_filterable: z.boolean(),
  is_searchable: z.boolean(),
  is_variant_attribute: z.boolean(),
  sort_order: z.coerce.number().int(),
});

const referenceSchema = z.object({
  type: z.enum(["manufacturer", "publisher", "franchise", "character", "author", "series"]),
  canonical_name: z.string().min(1),
  normalized_name: z.string().min(1),
});

export function AdminCategoriesPage() {
  const categories = useCategories();
  const create = useApiMutation(mutations.createCategory, [["admin", "categories"]]);
  const form = useForm<z.infer<typeof categorySchema>>({
    resolver: zodResolver(categorySchema),
    defaultValues: { name: "", slug: "", description: "", is_active: true },
  });

  return (
    <RoleGuard mode="admin">
      <AdminHeader title="Категории" />
      <Panel>
        <form className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
          <input className="ink-input" placeholder="Comics" {...form.register("name")} />
          <input className="ink-input" placeholder="comics" {...form.register("slug")} />
          <input className="ink-input" placeholder="Описание" {...form.register("description")} />
          <button className="ink-button">Создать</button>
        </form>
        <FieldError message={form.formState.errors.name?.message} />
        {create.error ? <ErrorMessage error={create.error} /> : null}
      </Panel>
      <List>
        {categories.data?.map((category) => (
          <div key={category.id} className="rounded-lg border-2 border-border p-3">
            <p className="font-black">{category.name}</p>
            <p className="text-muted">{category.slug} · {category.is_active ? "active" : "disabled"}</p>
          </div>
        ))}
      </List>
    </RoleGuard>
  );
}

export function AdminAttributesPage() {
  const { data: categories = [] } = useCategories();
  const [categoryId, setCategoryId] = useState("");
  const attributes = useAttributes(categoryId);
  const create = useApiMutation(mutations.createAttribute, [["admin", "attributes", categoryId]]);
  const form = useForm<z.infer<typeof attributeSchema>>({
    resolver: zodResolver(attributeSchema),
    defaultValues: {
      category_id: "",
      code: "",
      name: "",
      value_type: "text",
      is_required: false,
      is_filterable: true,
      is_searchable: true,
      is_variant_attribute: false,
      sort_order: 0,
    },
  });

  return (
    <RoleGuard mode="admin">
      <AdminHeader title="Атрибуты" />
      <Panel>
        <select
          className="ink-input max-w-sm"
          value={categoryId}
          onChange={(event) => {
            setCategoryId(event.target.value);
            form.setValue("category_id", event.target.value);
          }}
        >
          <option value="">Выберите категорию</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
          <input className="ink-input" placeholder="code" {...form.register("code")} />
          <input className="ink-input" placeholder="Название" {...form.register("name")} />
          <select className="ink-input" {...form.register("value_type")}>
            <option value="text">text</option>
            <option value="integer">integer</option>
            <option value="decimal">decimal</option>
            <option value="boolean">boolean</option>
            <option value="date">date</option>
            <option value="reference">reference</option>
          </select>
          <label className="font-bold"><input type="checkbox" {...form.register("is_required")} /> required</label>
          <label className="font-bold"><input type="checkbox" {...form.register("is_filterable")} /> filterable</label>
          <label className="font-bold"><input type="checkbox" {...form.register("is_variant_attribute")} /> variant</label>
          <button className="ink-button md:col-span-3">Создать атрибут</button>
        </form>
        {create.error ? <ErrorMessage error={create.error} /> : null}
      </Panel>
      <List>
        {attributes.data?.map((attribute) => (
          <div key={attribute.id} className="rounded-lg border-2 border-border p-3">
            <p className="font-black">{attribute.name}</p>
            <p className="text-muted">{attribute.code} · {attribute.value_type}</p>
          </div>
        ))}
      </List>
    </RoleGuard>
  );
}

export function AdminReferencesPage() {
  const references = useReferences();
  const create = useApiMutation(mutations.createReference, [["admin", "references"]]);
  const form = useForm<z.infer<typeof referenceSchema>>({
    resolver: zodResolver(referenceSchema),
    defaultValues: { type: "publisher", canonical_name: "", normalized_name: "" },
  });

  return (
    <RoleGuard mode="admin">
      <AdminHeader title="Справочники" />
      <Panel>
        <form className="grid gap-3 md:grid-cols-[180px_1fr_1fr_auto]" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
          <select className="ink-input" {...form.register("type")}>
            <option value="manufacturer">manufacturer</option>
            <option value="publisher">publisher</option>
            <option value="franchise">franchise</option>
            <option value="character">character</option>
            <option value="author">author</option>
            <option value="series">series</option>
          </select>
          <input className="ink-input" placeholder="Название" {...form.register("canonical_name")} />
          <input className="ink-input" placeholder="normalized_name" {...form.register("normalized_name")} />
          <button className="ink-button">Создать</button>
        </form>
        {create.error ? <ErrorMessage error={create.error} /> : null}
      </Panel>
      <List>
        {references.data?.map((reference) => (
          <div key={reference.id} className="rounded-lg border-2 border-border p-3">
            <p className="font-black">{reference.canonical_name}</p>
            <p className="text-muted">{reference.type} · {reference.normalized_name}</p>
          </div>
        ))}
      </List>
    </RoleGuard>
  );
}

function AdminHeader({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} subtitle="Админские CRUD-экраны для метаданных каталога." />
      <div className="mb-5 flex flex-wrap gap-2">
        <Link className="ink-button" href="/admin/categories">Категории</Link>
        <Link className="ink-button" href="/admin/attributes">Атрибуты</Link>
        <Link className="ink-button" href="/admin/references">Справочники</Link>
      </div>
    </>
  );
}

function List({ children }: { children: React.ReactNode }) {
  return <Panel className="mt-5 grid gap-3">{children || <EmptyState title="Пусто" text="Данных пока нет." />}</Panel>;
}
