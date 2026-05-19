import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatKRW, formatDateTime, categoryColor, categoryLabel } from "../lib/utils";
import StatCard from "../components/StatCard";
import { CardSkeleton } from "../components/Skeleton";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

export default function Home() {
  const [data, setData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.summary(), api.calendar(3)])
      .then(([s, c]) => {
        setData(s);
        setEvents(c.events.slice(0, 3));
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      </div>
    );
  }

  const calorieGoal = data?.preferences?.calorie_goal_daily || 2200;
  const todayCalories = data?.today?.calories || 0;
  const caloriePercent = Math.min((todayCalories / calorieGoal) * 100, 100);
  const calorieColor = caloriePercent < 70 ? "#10B981" : caloriePercent < 90 ? "#F59E0B" : "#EF4444";

  const monthSpend = data?.month?.spend || 0;
  const weeklyBudget = data?.preferences?.budget_weekly_KRW || 0;
  const monthlyBudget = weeklyBudget * 4;

  const categoryData = Object.entries(data?.month?.by_category || {}).map(([k, v]) => ({
    name: categoryLabel(k),
    value: v,
    color: categoryColor(k),
  }));

  const nextEvent = events[0];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Resumen del día</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon="💸"
          label="Gastado hoy"
          value={formatKRW(data?.today?.spend || 0)}
          sub="en todas las categorías"
          color="#F59E0B"
        />
        <StatCard
          icon="🔥"
          label="Calorías hoy"
          value={`${todayCalories.toLocaleString()} kcal`}
          sub={`Meta: ${calorieGoal.toLocaleString()} kcal`}
          color={calorieColor}
        />
        <StatCard
          icon="📅"
          label="Próximo evento"
          value={nextEvent ? nextEvent.title : "Sin eventos"}
          sub={nextEvent ? formatDateTime(nextEvent.start) : ""}
          color="#8B5CF6"
        />
      </div>

      {/* Calorie progress */}
      <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-[#9CA3AF]">Calorías del día</span>
          <span className="text-sm font-mono text-white">{todayCalories} / {calorieGoal} kcal</span>
        </div>
        <div className="h-2 bg-[#2A2A3A] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${caloriePercent}%`, backgroundColor: calorieColor }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Monthly budget */}
        <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
          <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Budget del mes</h2>
          {categoryData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={categoryData} innerRadius={55} outerRadius={80} dataKey="value" paddingAngle={3}>
                    {categoryData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v) => formatKRW(v)}
                    contentStyle={{ background: "#1A1A24", border: "1px solid #2A2A3A", borderRadius: "12px" }}
                    labelStyle={{ color: "#9CA3AF" }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {categoryData.map((cat) => (
                  <div key={cat.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: cat.color }} />
                      <span className="text-sm text-[#9CA3AF]">{cat.name}</span>
                    </div>
                    <span className="text-sm font-mono text-white">{formatKRW(cat.value)}</span>
                  </div>
                ))}
              </div>
                      <div className="mt-4 pt-4 border-t border-[#2A2A3A]">
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-[#6B7280]">Total este mes</span>
                  <span className="font-mono font-bold text-white">{formatKRW(monthSpend)}</span>
                </div>
                {monthlyBudget > 0 && (
                  <>
                    <div className="h-2 bg-[#2A2A3A] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${Math.min((monthSpend / monthlyBudget) * 100, 100)}%`,
                          backgroundColor: monthSpend / monthlyBudget < 0.75 ? "#10B981" : monthSpend / monthlyBudget < 1 ? "#F59E0B" : "#EF4444",
                        }}
                      />
                    </div>
                    <div className="flex justify-between mt-1.5">
                      <span className="text-xs text-[#6B7280]">Budget mensual</span>
                      <span className="text-xs font-mono text-[#6B7280]">{formatKRW(monthlyBudget)}</span>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <p className="text-[#6B7280] text-sm text-center py-8">Sin gastos este mes</p>
          )}
        </div>

        {/* Upcoming events */}
        <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
          <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Próximos eventos</h2>
          {events.length > 0 ? (
            <div className="space-y-3">
              {events.map((ev) => (
                <div key={ev.id} className="flex gap-3 p-3 bg-[#0F0F13] rounded-xl">
                  <div className="w-1 rounded-full bg-[#7C3AED] shrink-0" />
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{ev.title}</p>
                    <p className="text-[#6B7280] text-xs mt-0.5">{formatDateTime(ev.start)}</p>
                    {ev.location && <p className="text-[#6B7280] text-xs truncate">📍 {ev.location}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-32 text-[#6B7280]">
              <span className="text-3xl mb-2">📭</span>
              <span className="text-sm">Sin eventos próximos</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
