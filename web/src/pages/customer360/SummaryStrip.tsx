import { Gallery } from "@patternfly/react-core";
import type { Summary } from "../../api/types";
import { moneyShort, score } from "../../format";

type Tone = "default" | "alert" | "feature";

function Kpi({ label, value, tone = "default" }: { label: string; value: string; tone?: Tone }) {
  const cls = tone === "default" ? "ci-kpi" : `ci-kpi ci-kpi--${tone}`;
  return (
    <div className={cls}>
      <div className="ci-kpi-value">{value}</div>
      <div className="ci-kpi-label">{label}</div>
    </div>
  );
}

export function SummaryStrip({ summary }: { summary: Summary }) {
  const n = (v: number | null | undefined) => (v == null ? "—" : String(v));
  const atRisk = (summary.at_risk_skus ?? 0) > 0;
  const highChurn = (summary.churn_score ?? 0) >= 0.6;
  return (
    <Gallery hasGutter minWidths={{ default: "140px" }} aria-label="Account summary">
      <Kpi label="Active ARR" value={moneyShort(summary.total_arr)} tone="feature" />
      <Kpi label="Active SKUs" value={n(summary.sku_count)} />
      <Kpi label="Avg product health" value={n(summary.avg_health_score)} />
      <Kpi label="At-risk SKUs" value={n(summary.at_risk_skus)} tone={atRisk ? "alert" : "default"} />
      <Kpi label="Churn propensity" value={score(summary.churn_score)} tone={highChurn ? "alert" : "default"} />
      <Kpi label="Expansion propensity" value={score(summary.expansion_score)} />
    </Gallery>
  );
}
