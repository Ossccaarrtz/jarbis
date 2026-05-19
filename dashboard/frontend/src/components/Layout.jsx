import { NavLink } from "react-router-dom";
import { Home, DollarSign, Utensils, Calendar } from "lucide-react";

const navItems = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/expenses", icon: DollarSign, label: "Gastos" },
  { to: "/nutrition", icon: Utensils, label: "Nutrición" },
  { to: "/agenda", icon: Calendar, label: "Agenda" },
];

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#0F0F13]">
      {/* Sidebar (desktop) */}
      <aside className="hidden md:flex flex-col w-56 bg-[#1A1A24] border-r border-[#2A2A3A] py-6 px-4 gap-1 shrink-0">
        <div className="px-2 mb-8">
          <span className="text-xl font-bold text-white tracking-tight">Jarbis</span>
          <span className="text-[#7C3AED] text-xl font-bold">.</span>
        </div>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-[#7C3AED]/20 text-[#8B5CF6]"
                  : "text-[#9CA3AF] hover:bg-[#22223A] hover:text-white"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </aside>

      {/* Main */}
      <main className="flex-1 pb-20 md:pb-0 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-[#0F0F13]/80 backdrop-blur border-b border-[#2A2A3A] px-4 md:px-8 py-3 flex items-center justify-between">
          <span className="text-white font-semibold md:hidden">Jarbis<span className="text-[#7C3AED]">.</span></span>
          <span className="text-[#6B7280] text-sm ml-auto">
            {new Date().toLocaleDateString("es-MX", { weekday: "long", month: "long", day: "numeric" })}
          </span>
        </div>

        <div className="px-4 md:px-8 py-6">
          {children}
        </div>
      </main>

      {/* Bottom nav (mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#1A1A24] border-t border-[#2A2A3A] flex z-20">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-3 gap-1 text-xs transition-colors ${
                isActive ? "text-[#8B5CF6]" : "text-[#6B7280]"
              }`
            }
          >
            <Icon size={20} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
