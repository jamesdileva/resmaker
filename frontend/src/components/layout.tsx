import { NavLink, Outlet } from 'react-router-dom';

export function Layout() {
  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        className="sidebar"
        style={{
          width: 200,
          borderRight: '1px solid #e5e7eb',
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
          </ul>
        </nav>
      </aside>
      <main className="content" style={{ flex: 1, padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
