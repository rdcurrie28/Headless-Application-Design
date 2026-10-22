import { Link } from "react-router-dom";
import { EmptyState, EmptyStateBody, EmptyStateFooter, PageSection } from "@patternfly/react-core";
import { ExclamationTriangleIcon } from "@patternfly/react-icons";

export function NotFoundPage() {
  return (
    <PageSection>
      <EmptyState titleText="Page not found" headingLevel="h1" icon={ExclamationTriangleIcon}>
        <EmptyStateBody>That page doesn't exist.</EmptyStateBody>
        <EmptyStateFooter>
          <Link to="/accounts">Back to accounts</Link>
        </EmptyStateFooter>
      </EmptyState>
    </PageSection>
  );
}
