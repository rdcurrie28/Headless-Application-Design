import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Alert,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Flex,
  FlexItem,
  Grid,
  GridItem,
  PageSection,
  Title,
} from "@patternfly/react-core";
import { PlusIcon } from "@patternfly/react-icons";
import { useCustomer360 } from "../api/hooks";
import type { Customer, SectionError } from "../api/types";
import { QueryState } from "../components/QueryState";
import { MotionLabel } from "../components/labels";
import { humanize } from "../format";
import { SectionCard } from "./customer360/SectionCard";
import { SummaryStrip } from "./customer360/SummaryStrip";
import { SkuTable } from "./customer360/SkuTable";
import { HealthTable } from "./customer360/HealthTable";
import { PropensityPanel } from "./customer360/PropensityPanel";
import { DocumentsList } from "./customer360/DocumentsList";
import { ActionsList } from "./customer360/ActionsList";
import { AddActionModal } from "./customer360/AddActionModal";

type Fact = [string, ReactNode];

function FactList({ facts, label }: { facts: Fact[]; label?: string }) {
  return (
    <dl className="ci-facts" aria-label={label}>
      {facts.map(([term, value]) => (
        <div key={term}>
          <dt className="ci-fact-term">{term}</dt>
          <dd className="ci-fact-value">{value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

function AccountFacts({ customer }: { customer: Customer }) {
  const facts: Fact[] = [
    ["Customer ID", customer.customer_id],
    ["Segment", customer.segment],
    ["Region", customer.region],
    ["Owner", customer.account_owner],
    ["Salesforce ID", customer.salesforce_id],
  ];
  return <FactList facts={facts} />;
}

function ContactFacts({ customer }: { customer: Customer }) {
  const { contact_name, contact_phone, address } = customer;
  const facts: Fact[] = [
    ["Primary contact", contact_name],
    ["Phone", contact_phone && <a href={`tel:${contact_phone.replace(/[^\d+]/g, "")}`}>{contact_phone}</a>],
    ["Address", address],
  ];
  return <FactList facts={facts} label="Primary contact" />;
}

function PartialDataAlert({ errors }: { errors: SectionError[] }) {
  if (errors.length === 0) return null;
  const list = errors.map((e) => `${humanize(e.section)} (${e.source})`).join(", ");
  return (
    <Alert variant="warning" isInline title="Some sections couldn't load">
      Showing everything else. Unavailable: {list}.
    </Alert>
  );
}

export function Customer360Page() {
  const { customerId = "" } = useParams();
  const { data, isLoading, error, refetch, isFetching } = useCustomer360(customerId);
  const [adding, setAdding] = useState(false);

  return (
    <>
      <PageSection>
        <Breadcrumb className="ci-crumbs">
          <BreadcrumbItem render={() => <Link to="/accounts">Accounts</Link>} />
          <BreadcrumbItem isActive>{data?.customer.name ?? customerId}</BreadcrumbItem>
        </Breadcrumb>
      </PageSection>
      <QueryState isLoading={isLoading} error={error} title="Could not load this account">
        {data && (
          <>
            <PageSection>
              <div className="ci-hero">
              <span className="ci-eyebrow">Customer 360</span>
              <Flex alignItems={{ default: "alignItemsCenter" }} spaceItems={{ default: "spaceItemsMd" }}>
                <FlexItem>
                  <Title headingLevel="h1" className="ci-page-title">{data.customer.name}</Title>
                </FlexItem>
                <FlexItem>
                  <MotionLabel motion={data.summary.recommended_motion ?? "unknown"} />
                </FlexItem>
                <FlexItem align={{ default: "alignRight" }}>
                  <Button variant="secondary" onClick={() => refetch()} isLoading={isFetching}>
                    Refresh
                  </Button>
                </FlexItem>
              </Flex>
              <AccountFacts customer={data.customer} />
              <ContactFacts customer={data.customer} />
              </div>
            </PageSection>
            <PageSection>
              <Flex direction={{ default: "column" }} spaceItems={{ default: "spaceItemsLg" }}>
                <PartialDataAlert errors={data.errors ?? []} />
                <SummaryStrip summary={data.summary} />
                <Grid hasGutter>
                  <GridItem lg={8}>
                    <Flex direction={{ default: "column" }} spaceItems={{ default: "spaceItemsLg" }}>
                      <SectionCard title="SKUs" available={data.skus != null}>
                        <SkuTable skus={data.skus ?? []} />
                      </SectionCard>
                      <SectionCard title="Product health" available={data.product_health != null}>
                        <HealthTable rows={data.product_health ?? []} />
                      </SectionCard>
                    </Flex>
                  </GridItem>
                  <GridItem lg={4}>
                    <Flex direction={{ default: "column" }} spaceItems={{ default: "spaceItemsLg" }}>
                      <SectionCard title="Propensity" available={data.propensity != null}>
                        <PropensityPanel scores={data.propensity ?? []} />
                      </SectionCard>
                      <SectionCard
                        title="Next steps"
                        available={data.recent_actions != null}
                        actions={
                          <Button variant="link" icon={<PlusIcon />} onClick={() => setAdding(true)}>
                            Add
                          </Button>
                        }
                      >
                        <ActionsList actions={data.recent_actions ?? []} />
                      </SectionCard>
                      <SectionCard title="Documents" available={data.documents != null}>
                        <DocumentsList docs={data.documents ?? []} />
                      </SectionCard>
                    </Flex>
                  </GridItem>
                </Grid>
              </Flex>
            </PageSection>
            <AddActionModal
              customerId={data.customer.customer_id}
              customerName={data.customer.name}
              isOpen={adding}
              onClose={() => setAdding(false)}
            />
          </>
        )}
      </QueryState>
    </>
  );
}
