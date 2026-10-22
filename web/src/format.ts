const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const compactUsd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 });
const day = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });

export const money = (v: number | null | undefined) => (v == null ? "—" : usd.format(v));
export const moneyShort = (v: number | null | undefined) => (v == null ? "—" : compactUsd.format(v));
export const pct = (v: number | null | undefined, digits = 0) => (v == null ? "—" : `${v.toFixed(digits)}%`);
export const score = (v: number | null | undefined) => (v == null ? "—" : `${Math.round(v * 100)}`);
export const date = (v: string | null | undefined) => (v ? day.format(new Date(v)) : "—");
export const bytes = (v: number) => (v < 1024 * 1024 ? `${Math.round(v / 1024)} KB` : `${(v / 1024 / 1024).toFixed(1)} MB`);

export const humanize = (key: string) => {
  const s = key.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
};

export const signed = (v: number | null | undefined) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(0)}%`);
