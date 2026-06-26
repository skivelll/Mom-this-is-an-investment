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
  attributes: CatalogAttributeValue[];
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
  primary_image_url: string | null;
  attributes: CatalogAttributeValue[];
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
  primary_image_url: string | null;
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
  primary_image_url: string | null;
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
  reference_type: ReferenceType | null;
  is_required: boolean;
  is_filterable: boolean;
  is_searchable: boolean;
  is_variant_attribute: boolean;
  sort_order: number;
  validation_rules: Record<string, unknown> | null;
  reference_options: ReferenceEntity[];
};

export type CatalogAttributeValue = {
  id: string;
  attribute_definition_id: string;
  code: string;
  name: string;
  value_type: AttributeDefinition["value_type"];
  reference_type: ReferenceType | null;
  is_variant_attribute: boolean;
  value_text: string | null;
  value_integer: number | null;
  value_decimal: string | null;
  value_boolean: boolean | null;
  value_date: string | null;
  reference_entity_id: string | null;
  reference_label: string | null;
  display_value: string | null;
};

export type CatalogMedia = {
  id: string;
  catalog_item_id: string;
  catalog_variant_id: string | null;
  object_key: string;
  thumbnail_object_key: string | null;
  card_object_key: string | null;
  full_object_key: string | null;
  url: string;
  thumbnail_url: string | null;
  card_url: string | null;
  full_url: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  width: number | null;
  height: number | null;
  media_type: "image";
  is_primary: boolean;
  sort_order: number;
  alt_text: string | null;
  processing_status: "pending" | "processing" | "ready" | "failed";
  processing_error: string | null;
  created_at: string;
  updated_at: string;
};

export type CatalogMediaConfig = {
  max_upload_size_bytes: number;
  allowed_mime_types: string[];
};

export type CatalogMediaUpload = {
  object_key: string;
  upload_url: string;
  public_url: string;
  headers: Record<string, string>;
  expires_in: number;
};

export type ReferenceEntity = {
  id: string;
  type: ReferenceType;
  canonical_name: string;
  normalized_name: string;
};

export type ReferenceType =
  | "manufacturer"
  | "publisher"
  | "franchise"
  | "character"
  | "author"
  | "series";
