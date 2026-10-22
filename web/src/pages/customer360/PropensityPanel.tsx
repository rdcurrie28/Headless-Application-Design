import { Content, Progress, ProgressMeasureLocation, Stack, StackItem } from "@patternfly/react-core";
import type { PropensityScore } from "../../api/types";
import { DriverLabels, scoreVariant } from "../../components/labels";
import { date } from "../../format";

const TITLES = { churn: "Churn", expansion: "Expansion" } as const;

export function PropensityPanel({ scores }: { scores: PropensityScore[] }) {
  if (scores.length === 0) return <span className="ci-muted">This account hasn't been scored yet.</span>;
  const ordered = [...scores].sort((a, b) => a.model_name.localeCompare(b.model_name));
  return (
    <Stack hasGutter>
      {ordered.map((s) => (
        <StackItem key={s.model_name}>
          <Progress
            title={`${TITLES[s.model_name]} propensity`}
            value={Math.round(s.score * 100)}
            measureLocation={ProgressMeasureLocation.top}
            variant={scoreVariant(s.score, s.model_name)}
          />
          <Content component="small" className="ci-muted">
            Model {s.model_version ?? "—"} · scored {date(s.scored_at)}
          </Content>
          <div style={{ marginTop: "var(--pf-t--global--spacer--xs)" }}>
            <DriverLabels drivers={s.top_drivers ?? []} />
          </div>
        </StackItem>
      ))}
    </Stack>
  );
}
