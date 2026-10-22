import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";
import {
  Content,
  EmptyState,
  EmptyStateBody,
  PageSection,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  TextInput,
  Title,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";
import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import { CheckCircleIcon } from "@patternfly/react-icons";
import { useWatchlist } from "../api/hooks";
import type { WatchlistKind } from "../api/types";
import { QueryState } from "../components/QueryState";
import { DriverLabels, scoreVariant } from "../components/labels";
import { date } from "../format";

const COPY: Record<WatchlistKind, { title: string; blurb: string; scoreLabel: string; empty: string }> = {
  "at-risk": {
    title: "At-risk watchlist",
    blurb: "Accounts whose latest churn propensity is above the retention threshold, highest first.",
    scoreLabel: "Churn propensity",
    empty: "No accounts are above the churn threshold.",
  },
  expansion: {
    title: "Expansion targets",
    blurb: "Accounts whose latest expansion propensity is above the threshold, highest first.",
    scoreLabel: "Expansion propensity",
    empty: "No accounts are above the expansion threshold.",
  },
};

export function WatchlistPage({ kind }: { kind: WatchlistKind }) {
  const [owner, setOwner] = useState("");
  const deferredOwner = useDeferredValue(owner.trim());
  const { data, isLoading, error } = useWatchlist(kind, deferredOwner);
  const copy = COPY[kind];
  const model = kind === "at-risk" ? "churn" : "expansion";

  return (
    <>
      <PageSection>
        <span className="ci-eyebrow">{kind === "at-risk" ? "Retention" : "Growth"}</span>
        <Title headingLevel="h1" className="ci-page-title">{copy.title}</Title>
        <Content component="p" className="ci-muted">
          {copy.blurb}
        </Content>
      </PageSection>
      <PageSection>
        <div className="ci-panel">
        <Toolbar>
          <ToolbarContent>
            <ToolbarItem>
              <TextInput aria-label="Filter by owner" placeholder="Filter by owner" value={owner} onChange={(_e, v) => setOwner(v)} />
            </ToolbarItem>
          </ToolbarContent>
        </Toolbar>
        <QueryState isLoading={isLoading} error={error}>
          {data && data.length === 0 ? (
            <EmptyState titleText="Nothing to act on" headingLevel="h2" icon={CheckCircleIcon}>
              <EmptyStateBody>{copy.empty}</EmptyStateBody>
            </EmptyState>
          ) : (
            <Table aria-label={copy.title} variant="compact">
              <Thead>
                <Tr>
                  <Th>Account</Th>
                  <Th>Owner</Th>
                  <Th>{copy.scoreLabel}</Th>
                  <Th>Top drivers</Th>
                  <Th>Scored</Th>
                </Tr>
              </Thead>
              <Tbody>
                {data?.map((a) => (
                  <Tr key={a.customer.customer_id}>
                    <Td dataLabel="Account">
                      <Link to={`/accounts/${a.customer.customer_id}`}>{a.customer.name}</Link>
                    </Td>
                    <Td dataLabel="Owner">{a.customer.account_owner ?? "—"}</Td>
                    <Td dataLabel={copy.scoreLabel} className="ci-progress-cell">
                      <Progress
                        aria-label={`${copy.scoreLabel} for ${a.customer.name}`}
                        value={Math.round(a.score * 100)}
                        size={ProgressSize.sm}
                        measureLocation={ProgressMeasureLocation.outside}
                        variant={scoreVariant(a.score, model)}
                      />
                    </Td>
                    <Td dataLabel="Top drivers">
                      <DriverLabels drivers={a.top_drivers ?? []} />
                    </Td>
                    <Td dataLabel="Scored">{date(a.scored_at)}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </QueryState>
        </div>
      </PageSection>
    </>
  );
}
