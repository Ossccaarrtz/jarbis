import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { formatKRW, formatDateTime, categoryColor, categoryLabel } from "../lib/utils";
import StatCard from "../components/StatCard";
import { CardSkeleton } from "../components/Skeleton";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingDown, Flame, CalendarDays, RotateCw } from "lucide-react";

function PageHeader({ title, onRefresh, loading }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <h1 className="text-[15px] font-semibold text-white/90 tracking-tight">{title}</h1>
      <button
        onClick={onRefresh}
        disabled={loading}
        className="flex items-center gap-1.5 text-white/30 hover:text-white/60 transition-colors text-[12px]"
      >
        <RotateCw size={13} className={loading ? "animate-spin" : ""} />
        Actualizar
      </button>
    </div>
  );
}

export default function Home() {
  const [data, setData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([api.summary(), api.calendar(3)])
      .then(([s, c]) => { setData(s); setEvents(c.events.slice(0, 3)); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const calorieGoal = data?.preferences?.calorie_goal_daily || 2200;
  const todayCalories = data?.today?.calories || 0;
  const caloriePercent = Math.min((todayCalories / calorieGoal) * 100, 100);
  const calorieColor = caloriePercent < 70 ? "#10B981" : caloriePercent < 90 ? "#F59E0B" : "#EF4444";
  const monthSpend = data?.month?.spend || 0;
  const weeklyBudget = data?.preferences?.budget_weekly_KRW || 0;
  const monthlyBudget = weeklyBudget * 4;
  const nextEvent = events[0];

  const categoryData = Object.entries(data?.month?.by_category || {}).map(([k, v]) => ({
    name: categoryLabel(k), value: v, color: categoryColor(k),
  }));

  return (
    <div>
      <PageHeader title="Inicio" onRefresh={load} loading={loading} />

      {loading && !data ? (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <StatCard icon={TrendingDown} label="Gastado hoy" value={formatKRW(data?.today?.spend || 0)} sub={`Este mes: ${formatKRW(monthSpend)}`} color="#F59E0B" />
            <StatCard icon={Flame} label="Calorías" value={`${todayCalories.toLocaleString()} kcal`} sub={`Meta: ${calorieGoal.toLocaleString()} kcal`} color={calorieColor} />
            <StatCard icon={CalendarDays} label="Próximo evento" value={nextEvent ? nextEvent.title : "Sin eventos"} sub={nextEvent ? formatDateTime(nextEvent.start) : "—"} color="#8B5CF6" />
          </div>

          {/* Calorie bar */}
          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Calorías del día</span>
              <span className="text-white/60 text-[12px] font-mono">{todayCalories} / {calorieGoal}</span>
            </div>
            <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${caloriePercent}%`, backgroundColor: calorieColor }} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Budget card */}
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Gastos del mes</span>
              {categoryData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={160} className="mt-3">
                    <PieChart>
                      <Pie data={categoryData} innerRadius={48} outerRadius={68} dataKey="value" paddingAngle={2} strokeWidth={0}>
                        {categoryData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Pie>
                      <Tooltip
                        formatter={(v) => formatKRW(v)}
                        contentStyle={{ background: "#0F0F18", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", fontSize: "12px" }}
                        itemStyle={{ color: "#fff" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 mt-1">
                    {categoryData.sort((a, b) => b.value - a.value).map((cat) => (
                      <div key={cat.name} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: cat.color }} />
                        <span className="text-white/50 text-[12px] flex-1">{cat.name}</span>
                        <span className="text-white/80 text-[12px] font-mono">{formatKRW(cat.value)}</span>
                      </div>
                    ))}
                  </div>
                  {monthlyBudget > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/[0.06]">
                      <div className="flex justify-between mb-1.5">
                        <span className="text-white/30 text-[11px]">Budget mensual</span>
                        <span className="text-white/50 text-[11px] font-mono">{formatKRW(monthlyBudget)}</span>
                      </div>
                      <div className="h-1 bg-white/[0.06] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${Math.min((monthSpend / monthlyBudget) * 100, 100)}%`,
                            backgroundColor: monthSpend / monthlyBudget < 0.75 ? "#10B981" : monthSpend / monthlyBudget < 1 ? "#F59E0B" : "#EF4444",
                          }}
                        />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-white/20 text-[12px] text-center py-8">Sin gastos este mes</p>
              )}
            </div>

            {/* Events */}
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Próximos eventos</span>
              {events.length > 0 ? (
                <div className="space-y-2 mt-3">
                  {events.map((ev) => (
                    <div key={ev.id} className="flex gap-3 p-3 bg-white/[0.03] rounded-lg border border-white/[0.04]">
                      <div className="w-0.5 rounded-full bg-violet-500/60 shrink-0 my-0.5" />
                      <div className="min-w-0">
                        <p className="text-white/80 text-[13px] font-medium truncate">{ev.title}</p>
                        <p className="text-white/30 text-[11px] mt-0.5">{formatDateTime(ev.start)}</p>
                        {ev.location && <p className="text-white/25 text-[11px] truncate mt-0.5">{ev.location}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-white/20 text-[12px] text-center py-8">Sin eventos próximos</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
