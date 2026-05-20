import { NavLink } from "react-router-dom";
import { LayoutDashboard, CreditCard, Apple, CalendarDays } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Inicio" },
  { to: "/expenses", icon: CreditCard, label: "Gastos" },
  { to: "/nutrition", icon: Apple, label: "Nutrición" },
  { to: "/agenda", icon: CalendarDays, label: "Agenda" },
];

export default function Layout({ children }) {
  const dateStr = new Date().toLocaleDateString("es-MX", {
    weekday: "long", day: "numeric", month: "long",
  });

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#0A0A0F]">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex flex-col w-52 bg-[#0F0F18] border-r border-white/[0.06] py-7 px-3 gap-0.5 shrink-0">
        <div className="px-3 mb-8">
          <span className="text-[15px] font-semibold tracking-tight text-white">jarbis</span>
          <span className="text-violet-500 font-semibold text-[15px]">.</span>
        </div>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all ${
                isActive
                  ? "bg-white/[0.07] text-white"
                  : "text-white/40 hover:bg-white/[0.04] hover:text-white/70"
              }`
            }
          >
            <Icon size={15} strokeWidth={1.75} />
            {label}
          </NavLink>
        ))}
      </aside>

      {/* Main */}
      <main className="flex-1 pb-20 md:pb-0 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-[#0A0A0F]/90 backdrop-blur-md border-b border-white/[0.05] px-4 md:px-8 h-12 flex items-center justify-between">
          <span className="text-white/90 text-[13px] font-semibold md:hidden tracking-tight">
            jarbis<span className="text-violet-500">.</span>
          </span>
          <span className="text-white/30 text-[12px] ml-auto capitalize">{dateStr}</span>
        </div>
        <div className="px-4 md:px-8 py-6 max-w-5xl">
          {children}
        </div>
      </main>

      {/* Bottom nav mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#0F0F18]/95 backdrop-blur-md border-t border-white/[0.06] flex z-20 pb-safe">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-3 gap-1 transition-colors ${
                isActive ? "text-white" : "text-white/30"
              }`
            }
          >
            <Icon size={19} strokeWidth={1.75} />
            <span className="text-[10px] font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
