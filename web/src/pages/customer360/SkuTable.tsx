import { Progress, ProgressMeasureLocation, ProgressSize } from "@patternfly/react-core";
import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import type { SkuEntitlement } from "../../api/types";
import { utilizationVariant } from "../../components/labels";
import { date, money } from "../../format";

export function SkuTable({ skus }: { skus: SkuEntitlement[] }) {
  if (skus.length === 0) return <span className="ci-muted">No active entitlements.</span>;
  return (
    <Table aria-label="SKUs by customer" variant="compact">
      <Thead>
        <Tr>
          <Th>Product</Th>
          <Th>SKU</Th>
          <Th>Qty</Th>
          <Th>ARR</Th>
          <Th>Utilization (30d)</Th>
          <Th>Term ends</Th>
        </Tr>
      </Thead>
      <Tbody>
        {skus.map((s) => (
          <Tr key={s.sku}>
            <Td dataLabel="Product">
              {s.product_name}
              {s.product_family && <div className="ci-muted">{s.product_family}</div>}
            </Td>
            <Td dataLabel="SKU">{s.sku}</Td>
            <Td dataLabel="Qty">{s.quantity.toLocaleString()}</Td>
            <Td dataLabel="ARR">{money(s.arr)}</Td>
            <Td dataLabel="Utilization (30d)" className="ci-progress-cell">
              <Progress
                aria-label={`${s.product_name} utilization`}
                value={Math.min(s.utilization_pct, 100)}
                label={`${s.utilization_pct.toFixed(0)}%`}
                size={ProgressSize.sm}
                measureLocation={ProgressMeasureLocation.outside}
                variant={utilizationVariant(s.utilization_pct)}
              />
            </Td>
            <Td dataLabel="Term ends">{date(s.end_date)}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
}
