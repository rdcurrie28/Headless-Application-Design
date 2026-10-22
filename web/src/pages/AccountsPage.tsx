import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";
import {
  Content,
  EmptyState,
  EmptyStateBody,
  PageSection,
  Pagination,
  SearchInput,
  Title,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";
import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import { SearchIcon } from "@patternfly/react-icons";
import { useCustomers } from "../api/hooks";
import { QueryState } from "../components/QueryState";

export function AccountsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const deferred = useDeferredValue(search);

  const { data, isLoading, error } = useCustomers({ search: deferred, limit: perPage, offset: (page - 1) * perPage });

  return (
    <>
      <PageSection>
        <span className="ci-eyebrow">Directory</span>
        <Title headingLevel="h1" className="ci-page-title">Accounts</Title>
        <Content component="p" className="ci-muted">
          Pick an account to open its 360 view.
        </Content>
      </PageSection>
      <PageSection>
        <div className="ci-panel">
        <Toolbar>
          <ToolbarContent>
            <ToolbarItem>
              <SearchInput
                aria-label="Search accounts"
                placeholder="Search by name or ID"
                value={search}
                onChange={(_e, v) => {
                  setSearch(v);
                  setPage(1);
                }}
                onClear={() => {
                  setSearch("");
                  setPage(1);
                }}
              />
            </ToolbarItem>
            <ToolbarItem variant="pagination">
              <Pagination
                itemCount={data?.total ?? 0}
                page={page}
                perPage={perPage}
                onSetPage={(_e, p) => setPage(p)}
                onPerPageSelect={(_e, pp) => {
                  setPerPage(pp);
                  setPage(1);
                }}
                isCompact
              />
            </ToolbarItem>
          </ToolbarContent>
        </Toolbar>
        <QueryState isLoading={isLoading} error={error}>
          {data && data.items.length === 0 ? (
            <EmptyState titleText="No accounts match" headingLevel="h2" icon={SearchIcon}>
              <EmptyStateBody>Try a different name or customer ID.</EmptyStateBody>
            </EmptyState>
          ) : (
            <Table aria-label="Accounts" variant="compact">
              <Thead>
                <Tr>
                  <Th>Account</Th>
                  <Th>Customer ID</Th>
                  <Th>Segment</Th>
                  <Th>Region</Th>
                  <Th>Owner</Th>
                  <Th>Primary contact</Th>
                </Tr>
              </Thead>
              <Tbody>
                {data?.items.map((c) => (
                  <Tr key={c.customer_id}>
                    <Td dataLabel="Account">
                      <Link to={`/accounts/${c.customer_id}`}>{c.name}</Link>
                    </Td>
                    <Td dataLabel="Customer ID">{c.customer_id}</Td>
                    <Td dataLabel="Segment">{c.segment ?? "—"}</Td>
                    <Td dataLabel="Region">{c.region ?? "—"}</Td>
                    <Td dataLabel="Owner">{c.account_owner ?? "—"}</Td>
                    <Td dataLabel="Primary contact">
                      {c.contact_name ?? "—"}
                      {c.contact_phone && <div className="ci-muted">{c.contact_phone}</div>}
                    </Td>
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
