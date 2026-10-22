import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import type { ProductHealth } from "../../api/types";
import { HealthLabel } from "../../components/labels";
import { pct, signed } from "../../format";

export function HealthTable({ rows }: { rows: ProductHealth[] }) {
  if (rows.length === 0) return <span className="ci-muted">No health data yet.</span>;
  return (
    <Table aria-label="Product health" variant="compact">
      <Thead>
        <Tr>
          <Th>Product</Th>
          <Th>Status</Th>
          <Th>Health score</Th>
          <Th>Utilization</Th>
          <Th>30-day trend</Th>
        </Tr>
      </Thead>
      <Tbody>
        {rows.map((h) => (
          <Tr key={h.sku}>
            <Td dataLabel="Product">{h.product_name}</Td>
            <Td dataLabel="Status">
              <HealthLabel status={h.status} />
            </Td>
            <Td dataLabel="Health score">{h.health_score.toFixed(0)}</Td>
            <Td dataLabel="Utilization">{pct(h.utilization_pct)}</Td>
            <Td dataLabel="30-day trend">{signed(h.trend_30d_pct)}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
}
