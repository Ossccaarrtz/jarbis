import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { CardSkeleton } from "../components/Skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";
import { RotateCw } from "lucide-react";

const MEAL_ORDER = ["desayuno", "almuerzo", "cena", "snack", "merienda", "otro"];
const MEAL_LABEL = { desayuno: "Desayuno", almuerzo: "Almuerzo", cena: "Cena", snack: "Snack", merienda: "Merienda", otro: "Otro" };

function CalorieRing({ consumed, goal }) {
  const pct = Math.min(consumed / goal, 1);
  const r = 64;
  const circ = 2 * Math.PI * r;
  const color = pct < 0.7 ? "#10B981" : pct < 0.9 ? "#F59E0B" : "#EF4444";
  return (
    <div className="relative flex items-center justify-center" style={{ width: 160, height: 160 }}>
      <svg width="160" height="160" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="80" cy="80" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <circle cx="80" cy="80" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)}
          strokeLinecap="round" style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-white text-2xl font-semibold tracking-tight">{consumed.toLocaleString()}</span>
        <span className="text-white/30 text-[11px]">/ {goal.toLocaleString()} kcal</span>
      </div>
    </div>
  );
}

export default function Nutrition() {
  const [todayData, setTodayData] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [goal, setGoal] = useState(2200);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([api.nutritionToday(), api.nutritionWeekly(), api.summary()])
      .then(([t, wk, s]) => { setTodayData(t); setWeekly(wk.days); setGoal(s.preferences?.calorie_goal_daily || 2200); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const totalCalories = todayData?.total_calories || 0;
  const byType = todayData?.by_meal_type || {};
  const mealGroups = [...MEAL_ORDER.filter(t => byType[t]), ...Object.keys(byType).filter(t => !MEAL_ORDER.includes(t))];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[15px] font-semibold text-white/90 tracking-tight">Nutrición</h1>
        <button onClick={load} disabled={loading} className="flex items-center gap-1.5 text-white/30 hover:text-white/60 transition-colors text-[12px]">
          <RotateCw size={13} className={loading ? "animate-spin" : ""} />
          Actualizar
        </button>
      </div>

      {loading && !todayData ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><CardSkeleton /><CardSkeleton /></div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4 flex flex-col items-center gap-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest self-start">Calorías de hoy</span>
              <CalorieRing consumed={totalCalories} goal={goal} />
              <div className="grid grid-cols-2 gap-2 w-full">
                <div className="bg-white/[0.03] rounded-lg p-3 text-center">
                  <p className="text-white/30 text-[10px] uppercase tracking-wider">Consumido</p>
                  <p className="text-white font-mono font-semibold text-[15px] mt-0.5">{totalCalories.toLocaleString()}</p>
                </div>
                <div className="bg-white/[0.03] rounded-lg p-3 text-center">
                  <p className="text-white/30 text-[10px] uppercase tracking-wider">Restante</p>
                  <p className="text-white font-mono font-semibold text-[15px] mt-0.5">{Math.max(goal - totalCalories, 0).toLocaleString()}</p>
                </div>
              </div>
            </div>

            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Semana</span>
              <ResponsiveContainer width="100%" height={200} className="mt-2">
                <BarChart data={weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} tickFormatter={d => d.slice(5)} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={v => [`${v} kcal`, "Calorías"]} contentStyle={{ background: "#0F0F18", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", fontSize: "12px" }} itemStyle={{ color: "#fff" }} />
                  <ReferenceLine y={goal} stroke="rgba(139,92,246,0.4)" strokeDasharray="4 4" />
                  <Bar dataKey="calories" fill="#10B981" radius={[3, 3, 0, 0]} opacity={0.8} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
            <span className="text-white/40 text-[11px] uppercase tracking-widest">Comidas de hoy</span>
            {mealGroups.length > 0 ? (
              <div className="mt-3 space-y-4">
                {mealGroups.map(type => {
                  const meals = byType[type] || [];
                  const typeCalories = meals.reduce((s, m) => s + m.calories, 0);
                  return (
                    <div key={type}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-white/50 text-[12px] font-medium">{MEAL_LABEL[type] || type}</span>
                        <span className="text-white/25 text-[11px] font-mono">{typeCalories} kcal</span>
                      </div>
                      {meals.map(meal => (
                        <div key={meal.id} className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
                          <p className="text-white/60 text-[13px]">{meal.description}</p>
                          <span className="text-white/30 text-[12px] font-mono shrink-0 ml-3">{meal.calories} kcal</span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-white/20 text-[12px] text-center py-8">Sin comidas registradas hoy</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
