import { Outlet } from 'react-router-dom';

export function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Career OS</h1>
        <nav>
          <a href="/">Dashboard</a>
        </nav>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
