export type UserRole = "user" | "moderator" | "senior_moderator" | "admin";
export type CatalogStatus = "draft" | "active" | "archived";
export type RequestStatus =
  | "pending"
  | "in_review"
  | "needs_information"
  | "approved"
  | "rejected"
  | "duplicate"
  | "cancelled";
export type WishlistStatus =
  | "active"
  | "pending_moderation"
  | "rejected"
  | "purchased"
  | "archived";

export type User = {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
};

export type Category = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
};

export type CatalogItem = {
  id: string;
  category_id: string;
  canonical_title: string;
  normalized_title: string;
  description: string | null;
  release_year: number | null;
  status: CatalogStatus;
};

export type CatalogVariant = {
  id: string;
  catalog_item_id: string;
  canonical_title: string;
  normalized_title: string;
  sku: string | null;
  barcode: string | null;
  release_date: string | null;
  status: CatalogStatus;
  item_title: string | null;
  variant_label: string | null;
};

export type Collection = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  visibility: "private" | "unlisted" | "public";
  created_at: string;
  updated_at: string;
};

export type CollectionItem = {
  id: string;
  collection_id: string;
  catalog_variant_id: string;
  condition: "sealed" | "new" | "opened" | "used" | "damaged" | null;
  quantity: number;
  purchase_price: string | null;
  purchase_currency: string | null;
  purchase_date: string | null;
  comment: string | null;
};

export type CollectionItemDetailed = CollectionItem & {
  collection_name: string;
  catalog_item_id: string;
  item_title: string;
  variant_title: string;
  variant_label: string | null;
};

export type WishlistItem = {
  id: string;
  user_id: string;
  catalog_variant_id: string | null;
  catalog_request_id: string | null;
  target_price: string | null;
  currency: string | null;
  source_url: string | null;
  priority: number;
  status: WishlistStatus;
  comment: string | null;
};

export type WishlistItemDetailed = WishlistItem & {
  catalog_item_id: string | null;
  item_title: string;
  variant_title: string | null;
  variant_label: string | null;
};

export type CatalogRequest = {
  id: string;
  created_by_id: string;
  category_id: string;
  raw_title: string;
  description: string | null;
  source_url: string | null;
  proposed_data: Record<string, unknown> | null;
  status: RequestStatus;
  rejection_reason: string | null;
  approved_catalog_item_id: string | null;
  approved_variant_id: string | null;
  created_at: string;
  updated_at: string;
};

export type AttributeDefinition = {
  id: string;
  category_id: string;
  code: string;
  name: string;
  value_type: "text" | "integer" | "decimal" | "boolean" | "date" | "reference";
  is_required: boolean;
  is_filterable: boolean;
  is_searchable: boolean;
  is_variant_attribute: boolean;
  sort_order: number;
};

export type ReferenceEntity = {
  id: string;
  type: "manufacturer" | "publisher" | "franchise" | "character" | "author" | "series";
  canonical_name: string;
  normalized_name: string;
};
