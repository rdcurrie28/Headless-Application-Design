import { DataList, DataListCell, DataListItem, DataListItemCells, DataListItemRow } from "@patternfly/react-core";
import type { DocumentItem } from "../../api/types";
import { bytes, date } from "../../format";

export function DocumentsList({ docs }: { docs: DocumentItem[] }) {
  if (docs.length === 0) return <span className="ci-muted">No documents on file.</span>;
  return (
    <DataList aria-label="Documents" isCompact>
      {docs.map((d) => (
        <DataListItem key={d.key}>
          <DataListItemRow>
            <DataListItemCells
              dataListCells={[
                <DataListCell key="name">
                  <a href={d.url} target="_blank" rel="noreferrer">
                    {d.name}
                  </a>
                </DataListCell>,
                <DataListCell key="meta" className="ci-muted">
                  {date(d.last_modified)} · {bytes(d.size_bytes)}
                </DataListCell>,
              ]}
            />
          </DataListItemRow>
        </DataListItem>
      ))}
    </DataList>
  );
}
