import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  const linkBase =
    "px-3 py-2 rounded-xl text-sm font-medium transition hover:bg-zinc-100";
  const linkActive = "bg-zinc-900 text-white hover:bg-zinc-900";

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-2xl bg-zinc-900" />
            <div>
              <div className="font-semibold leading-tight">
                Greenwashing Detector
              </div>
              <div className="text-xs text-zinc-500">
                PDF → Claims → Score → Flag
              </div>
            </div>
          </div>

          <nav className="flex items-center gap-2">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : ""}`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/upload"
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : ""}`
              }
            >
              Upload
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
