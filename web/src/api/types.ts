import type { components } from "./schema";

type S = components["schemas"];

export type Customer = S["Customer"];
export type CustomerPage = S["CustomerPage"];
export type Customer360 = S["Customer360"];
export type Summary = S["Customer360Summary"];
export type SkuEntitlement = S["SkuEntitlement"];
export type ProductHealth = S["ProductHealth"];
export type PropensityScore = S["PropensityScore"];
export type DocumentItem = S["Document"];
export type RepAction = S["RepAction"];
export type RepActionCreate = S["RepActionCreate"];
export type ScoredAccount = S["ScoredAccount"];
export type SectionError = S["SectionError"];
export type ActionType = RepActionCreate["action_type"];
export type Motion = Summary["recommended_motion"];
export type HealthStatus = ProductHealth["status"];
export type WatchlistKind = "at-risk" | "expansion";
