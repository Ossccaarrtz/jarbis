import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { formatKRW, categoryColor, categoryLabel, today } from "../lib/utils";
import { CardSkeleton } from "../components/Skeleton";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingDown, Flame, RotateCw, Utensils } from "lucide-react";

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

const MEAL_TYPE_LABELS = {
  breakfast: "Desayuno",
  desayuno: "Desayuno",
  lunch: "Almuerzo",
  almuerzo: "Almuerzo",
  dinner: "Cena",
  cena: "Cena",
  snack: "Snack",
};

function mealTypeLabel(t) {
  return MEAL_TYPE_LABELS[t?.toLowerCase()] || (t ? t.charAt(0).toUpperCase() + t.slice(1) : "Otro");
}

export default function Daily() {
  const [date, setDate] = useState(today());
  const [expenses, setExpenses] = useState(null);
  const [nutrition, setNutrition] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.expenses({ start_date: date, end_date: date }),
      api.nutrition({ start_date: date, end_date: date }),
    ])
      .then(([e, n]) => { setExpenses(e); setNutrition(n); })
      .finally(() => setLoading(false));
  }, [date]);

  useEffect(() => { load(); }, [load]);

  const categoryData = Object.entries(expenses?.by_category || {}).map(([k, v]) => ({
    name: categoryLabel(k), value: v, color: categoryColor(k),
  }));

  const meals = nutrition?.items || [];
  const mealsByType = meals.reduce((acc, m) => {
    (acc[m.meal_type] = acc[m.meal_type] || []).push(m);
    return acc;
  }, {});

  return (
    <div>
      <PageHeader title="Resumen del día" onRefresh={load} loading={loading} />

      {/* Date picker */}
      <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4 mb-4 flex items-center gap-3">
        <span className="text-white/40 text-[11px] uppercase tracking-widest">Fecha</span>
        <input
          type="date"
          value={date}
          max={today()}
          onChange={(e) => setDate(e.target.value)}
          className="bg-white/[0.04] border border-white/[0.06] rounded-lg px-3 py-1.5 text-[13px] text-white/80 focus:outline-none focus:border-violet-500/40"
        />
        <button
          onClick={() => setDate(today())}
          className="ml-auto text-white/30 hover:text-white/60 transition-colors text-[12px]"
        >
          Hoy
        </button>
      </div>

      {loading && !expenses ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3"><CardSkeleton /><CardSkeleton /></div>
      ) : (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown size={13} className="text-amber-500" />
                <span className="text-white/40 text-[11px] uppercase tracking-widest">Gastado</span>
              </div>
              <p className="text-white text-[18px] font-semibold">{formatKRW(expenses?.total || 0)}</p>
              <p className="text-white/30 text-[11px] mt-0.5">{expenses?.items?.length || 0} transacciones</p>
            </div>
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Flame size={13} className="text-emerald-500" />
                <span className="text-white/40 text-[11px] uppercase tracking-widest">Calorías</span>
              </div>
              <p className="text-white text-[18px] font-semibold">{(nutrition?.total_calories || 0).toLocaleString()} kcal</p>
              <p className="text-white/30 text-[11px] mt-0.5">{meals.length} comidas</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Expenses donut + list */}
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Gastos por categoría</span>
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
                  <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-1.5">
                    {expenses.items.map((it) => (
                      <div key={it.id} className="flex items-center gap-2">
                        <div className="w-1 h-1 rounded-full shrink-0" style={{ background: categoryColor(it.category) }} />
                        <span className="text-white/60 text-[12px] flex-1 truncate">{it.description || categoryLabel(it.category)}</span>
                        <span className="text-white/80 text-[12px] font-mono">{formatKRW(it.amount)}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-white/20 text-[12px] text-center py-8">Sin gastos este día</p>
              )}
            </div>

            {/* Meals list */}
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Comidas</span>
              {meals.length > 0 ? (
                <div className="space-y-3 mt-3">
                  {Object.entries(mealsByType).map(([type, list]) => (
                    <div key={type}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <Utensils size={11} className="text-white/30" />
                        <span className="text-white/40 text-[11px] uppercase tracking-wider">{mealTypeLabel(type)}</span>
                        <span className="text-white/30 text-[11px] ml-auto font-mono">
                          {list.reduce((s, m) => s + m.calories, 0)} kcal
                        </span>
                      </div>
                      <div className="space-y-1.5 pl-4">
                        {list.map((m) => (
                          <div key={m.id} className="flex items-center gap-2">
                            <span className="text-white/30 text-[11px] font-mono">{m.time}</span>
                            <span className="text-white/60 text-[12px] flex-1 truncate">{m.description}</span>
                            <span className="text-white/80 text-[12px] font-mono">{m.calories}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-white/20 text-[12px] text-center py-8">Sin comidas registradas</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
