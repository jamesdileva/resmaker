import { NavLink, Outlet } from 'react-router-dom';
import { OfflineBanner } from './OfflineBanner';

export function Layout() {
  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column' }}>
      <OfflineBanner />
      <div style={{ display: 'flex', flex: 1 }}>
      <aside
        className="sidebar"
        style={{
          width: 200,
          borderRight: '1px solid var(--border)',
          padding: 16,
        }}
      >
        <h1 style={{ fontSize: 18 }}>Career OS</h1>
        <nav>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            <li>
              <NavLink to="/">Dashboard</NavLink>
            </li>
            <li>
              <NavLink to="/import">Import</NavLink>
            </li>
            <li>
              <NavLink to="/resume">Resume Builder</NavLink>
            </li>
            <li>
              <NavLink to="/soq">SOQ Builder</NavLink>
            </li>
            <li>
              <NavLink to="/duty">Duty Statement</NavLink>
            </li>
            <li>
              <NavLink to="/explore">Explorer</NavLink>
            </li>
            <li>
              <NavLink to="/settings">Settings</NavLink>
            </li>
          </ul>
        </nav>
      </aside>
      <main className="content" style={{ flex: 1, padding: 24 }}>
        <Outlet />
      </main>
      </div>
    </div>
  );
}
