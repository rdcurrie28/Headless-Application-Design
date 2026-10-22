import type { ReactNode } from "react";
import { Alert, Bullseye, Spinner } from "@patternfly/react-core";

type Props = {
  isLoading: boolean;
  error: Error | null;
  title?: string;
  children: ReactNode;
};

export function QueryState({ isLoading, error, title = "Could not load data", children }: Props) {
  if (isLoading) {
    return (
      <Bullseye style={{ minHeight: "8rem" }}>
        <Spinner aria-label="Loading" />
      </Bullseye>
    );
  }
  if (error) {
    return (
      <Alert variant="danger" isInline title={title}>
        {error.message}
      </Alert>
    );
  }
  return <>{children}</>;
}
