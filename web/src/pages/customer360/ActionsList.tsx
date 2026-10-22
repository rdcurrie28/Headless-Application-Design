import { Content, Label, Stack, StackItem } from "@patternfly/react-core";
import type { RepAction } from "../../api/types";
import { date, humanize } from "../../format";

export function ActionsList({ actions }: { actions: RepAction[] }) {
  if (actions.length === 0) return <span className="ci-muted">No next steps logged yet.</span>;
  return (
    <Stack hasGutter>
      {actions.map((a) => (
        <StackItem key={a.action_id}>
          <Label isCompact color="blue">
            {humanize(a.action_type)}
          </Label>{" "}
          <span>{a.note}</span>
          <Content component="small" className="ci-muted">
            {a.created_by} · {date(a.created_at)}
            {a.due_date ? ` · due ${date(a.due_date)}` : ""}
          </Content>
        </StackItem>
      ))}
    </Stack>
  );
}
