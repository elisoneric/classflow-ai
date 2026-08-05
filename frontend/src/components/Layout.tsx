import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/auth-context";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/pending-review", label: "Pending Review" },
  { to: "/courses", label: "Courses" },
  { to: "/lecturers", label: "Lecturers" },
  { to: "/sessions", label: "Session History" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  const { logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      <aside className="flex w-56 shrink-0 flex-col border-r border-gray-200 bg-white">
        <div className="px-4 py-5 text-lg font-semibold">ClassFlow AI</div>
        <nav className="flex flex-col gap-1 px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-purple-100 text-purple-700"
                    : "text-gray-600 hover:bg-gray-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          onClick={() => void logout()}
          className="mx-2 mt-auto mb-4 rounded-md px-3 py-2 text-left text-sm font-medium text-gray-500 hover:bg-gray-100"
        >
          Log out
        </button>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
