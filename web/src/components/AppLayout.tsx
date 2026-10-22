import { useRef, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  Masthead,
  MastheadBrand,
  MastheadMain,
  MastheadToggle,
  Nav,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
  PageToggleButton,
} from "@patternfly/react-core";
import { BarsIcon } from "@patternfly/react-icons";

const NAV = [
  { to: "/accounts", label: "Accounts" },
  { to: "/watchlists/at-risk", label: "At-risk watchlist" },
  { to: "/watchlists/expansion", label: "Expansion targets" },
];

export function AppLayout() {
  const [open, setOpen] = useState(true);
  // Page only detects mobile (where the sidebar is an overlay) when onPageResize is set.
  const mobile = useRef(false);
  const onPageResize = (_e: unknown, { mobileView }: { mobileView: boolean }) => {
    if (mobileView === mobile.current) return;
    mobile.current = mobileView;
    setOpen(!mobileView);
  };
  const { pathname } = useLocation();

  const masthead = (
    <Masthead>
      <MastheadMain>
        <MastheadToggle>
          <PageToggleButton isHamburgerButton isSidebarOpen={open} onSidebarToggle={() => setOpen(!open)} aria-label="Toggle navigation">
            <BarsIcon />
          </PageToggleButton>
        </MastheadToggle>
        <MastheadBrand>
          <Link to="/accounts" className="ci-brand">
            <span className="ci-brand-mark" aria-hidden="true">CI</span>
            <span>
              Customer Insights <span className="ci-brand-sub">· Sales 360</span>
            </span>
          </Link>
        </MastheadBrand>
      </MastheadMain>
    </Masthead>
  );

  const sidebar = (
    <PageSidebar isSidebarOpen={open}>
      <PageSidebarBody>
        <div className="ci-nav-section">Workspace</div>
        <Nav aria-label="Main">
          <NavList>
            {NAV.map((n) => (
              <NavItem key={n.to} isActive={pathname.startsWith(n.to)} onClick={() => mobile.current && setOpen(false)}>
                <Link to={n.to}>{n.label}</Link>
              </NavItem>
            ))}
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  );

  return (
    <Page masthead={masthead} sidebar={sidebar} isManagedSidebar={false} onPageResize={onPageResize}>
      <Outlet />
    </Page>
  );
}
