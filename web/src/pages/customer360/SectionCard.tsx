import type { ReactNode } from "react";
import { Alert, Card, CardBody, CardHeader, CardTitle } from "@patternfly/react-core";

type Props = {
  title: string;
  available: boolean;
  actions?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ title, available, actions, children }: Props) {
  return (
    <Card isFullHeight>
      <CardHeader actions={actions ? { actions, hasNoOffset: true } : undefined}>
        <CardTitle component="h2">{title}</CardTitle>
      </CardHeader>
      <CardBody>
        {available ? (
          children
        ) : (
          <Alert variant="warning" isInline isPlain title="This section is temporarily unavailable" />
        )}
      </CardBody>
    </Card>
  );
}
