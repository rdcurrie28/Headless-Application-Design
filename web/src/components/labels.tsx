import { Label, LabelGroup } from "@patternfly/react-core";
import type { HealthStatus, Motion } from "../api/types";
import { humanize } from "../format";

const HEALTH: Record<HealthStatus, { text: string; status: "success" | "warning" | "danger" }> = {
  healthy: { text: "Healthy", status: "success" },
  watch: { text: "Watch", status: "warning" },
  at_risk: { text: "At risk", status: "danger" },
};

export function HealthLabel({ status }: { status: HealthStatus }) {
  const h = HEALTH[status];
  return <Label status={h.status}>{h.text}</Label>;
}

const MOTION: Record<Motion, { text: string; color: "red" | "green" | "purple" | "blue" | "grey" }> = {
  retain: { text: "Retain", color: "red" },
  expand: { text: "Expand", color: "green" },
  retain_and_expand: { text: "Retain & expand", color: "purple" },
  nurture: { text: "Nurture", color: "blue" },
  unknown: { text: "Unknown", color: "grey" },
};

export function MotionLabel({ motion }: { motion: Motion }) {
  const m = MOTION[motion];
  return <Label color={m.color}>{m.text}</Label>;
}

export function DriverLabels({ drivers }: { drivers: string[] }) {
  if (drivers.length === 0) return <span className="ci-muted">—</span>;
  return (
    <LabelGroup numLabels={3}>
      {drivers.map((d) => (
        <Label key={d} isCompact variant="outline">
          {humanize(d)}
        </Label>
      ))}
    </LabelGroup>
  );
}

export function scoreVariant(value: number, kind: "churn" | "expansion"): "danger" | "warning" | "success" | undefined {
  if (kind === "churn") return value >= 0.6 ? "danger" : value >= 0.35 ? "warning" : "success";
  return value >= 0.6 ? "success" : undefined;
}

export function utilizationVariant(value: number): "danger" | "warning" | undefined {
  if (value < 40) return "danger";
  if (value < 60) return "warning";
  return undefined;
}
