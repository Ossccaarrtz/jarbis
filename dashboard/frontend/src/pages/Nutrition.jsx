import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { CardSkeleton } from "../components/Skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";

const MEAL_ICONS = { desayuno: "🌅", almuerzo: "☀️", cena: "🌙", snack: "🍎", merienda: "🍎", otro: "🍽️" };
const MEAL_ORDER = ["desayuno", "almuerzo", "cena", "snack", "merienda", "otro"];

function CalorieRing({ consumed, goal }) {
  const pct = Math.min(consumed / goal, 1);
  const r = 70;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const color = pct < 0.7 ? "#10B981" : pct < 0.9 ? "#F59E0B" : "#EF4444";

  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="180" className="-rotate-90">
        <circle cx="90" cy="90" r={r} fill="none" stroke="#2A2A3A" strokeWidth="12" />
        <circle
          cx="90" cy="90" r={r} fill="none"
          stroke={color} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center pointer-events-none" style={{ marginTop: "-120px" }}>
        <span className="text-3xl font-bold font-mono text-white">{consumed.toLocaleString()}</span>
        <span className="text-[#6B7280] text-sm">/ {goal.toLocaleString()} kcal</span>
      </div>
    </div>
  );
}

export default function Nutrition() {
  const [todayData, setTodayData] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [goal, setGoal] = useState(2200);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.nutritionToday(), api.nutritionWeekly(), api.summary()])
      .then(([t, wk, s]) => {
        setTodayData(t);
        setWeekly(wk.days);
        setGoal(s.preferences?.calorie_goal_daily || 2200);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="grid grid-cols-1 md:grid-cols-2 gap-6"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>;
  }

  const totalCalories = todayData?.total_calories || 0;
  const byType = todayData?.by_meal_type || {};
  const orderedMeals = MEAL_ORDER.filter((t) => byType[t]);
  const otherMeals = Object.keys(byType).filter((t) => !MEAL_ORDER.includes(t));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Nutrición</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Calorie ring */}
        <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5 flex flex-col items-center">
          <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide self-start">Calorías de hoy</h2>
          <div className="relative flex justify-center">
            <CalorieRing consumed={totalCalories} goal={goal} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 w-full">
            <div className="bg-[#0F0F13] rounded-xl p-3 text-center">
              <p className="text-[#6B7280] text-xs">Consumido</p>
              <p className="text-white font-mono font-bold">{totalCalories.toLocaleString()} kcal</p>
            </div>
            <div className="bg-[#0F0F13] rounded-xl p-3 text-center">
              <p className="text-[#6B7280] text-xs">Restante</p>
              <p className="text-white font-mono font-bold">{Math.max(goal - totalCalories, 0).toLocaleString()} kcal</p>
            </div>
          </div>
        </div>

        {/* Weekly chart */}
        <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
          <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Semana</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A3A" />
              <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} />
              <Tooltip
                formatter={(v) => [`${v} kcal`, "Calorías"]}
                contentStyle={{ background: "#1A1A24", border: "1px solid #2A2A3A", borderRadius: "12px" }}
              />
              <ReferenceLine y={goal} stroke="#7C3AED" strokeDasharray="4 4" label={{ value: "Meta", fill: "#7C3AED", fontSize: 11 }} />
              <Bar dataKey="calories" fill="#10B981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Meal log */}
      <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
        <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Comidas de hoy</h2>
        {[...orderedMeals, ...otherMeals].length > 0 ? (
          <div className="space-y-4">
            {[...orderedMeals, ...otherMeals].map((type) => {
              const meals = byType[type] || [];
              const typeCalories = meals.reduce((s, m) => s + m.calories, 0);
              return (
                <div key={type}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white capitalize">
                      {MEAL_ICONS[type] || "🍽️"} {type}
                    </span>
                    <span className="text-xs font-mono text-[#6B7280]">{typeCalories} kcal</span>
                  </div>
                  <div className="space-y-1.5">
                    {meals.map((meal) => (
                      <div key={meal.id} className="flex items-center justify-between p-3 bg-[#0F0F13] rounded-xl">
                        <p className="text-sm text-[#D1D5DB]">{meal.description}</p>
                        <span className="text-xs font-mono text-[#9CA3AF] shrink-0 ml-3">{meal.calories} kcal</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-[#6B7280]">
            <span className="text-4xl mb-2">🥗</span>
            <span className="text-sm">Sin comidas registradas hoy</span>
          </div>
        )}
      </div>
    </div>
  );
}
