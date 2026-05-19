import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { formatKRW, formatDate, categoryColor, categoryLabel, monthStart, today } from "../lib/utils";
import { CardSkeleton } from "../components/Skeleton";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
} from "recharts";

const RANGES = [
  { label: "Hoy", start: today(), end: today() },
  { label: "Esta semana", start: (() => { const d = new Date(); d.setDate(d.getDate() - 6); return d.toISOString().slice(0, 10); })(), end: today() },
  { label: "Este mes", start: monthStart(), end: today() },
];

export default function Expenses() {
  const [range, setRange] = useState(2);
  const [data, setData] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    setLoading(true);
    const r = RANGES[range];
    Promise.all([
      api.expenses({ start_date: r.start, end_date: r.end }),
      api.expensesWeekly(),
    ]).then(([exp, wk]) => {
      setData(exp);
      setWeekly(wk.days);
    }).finally(() => setLoading(false));
  }, [range, tick]);

  const categoryData = data
    ? Object.entries(data.by_category).map(([k, v]) => ({
        name: categoryLabel(k), value: v, color: categoryColor(k),
      }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-white">Gastos</h1>
        <div className="flex gap-2">
          <button
            onClick={refresh}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-[#1A1A24] text-[#9CA3AF] hover:text-white border border-[#2A2A3A] transition-colors"
            title="Actualizar"
          >
            ↻
          </button>
          {RANGES.map((r, i) => (
            <button
              key={i}
              onClick={() => setRange(i)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                range === i ? "bg-[#7C3AED] text-white" : "bg-[#1A1A24] text-[#9CA3AF] hover:text-white border border-[#2A2A3A]"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6"><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : (
        <>
          {/* Total card */}
          <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5 flex items-center justify-between">
            <div>
              <p className="text-[#6B7280] text-sm">Total {RANGES[range].label.toLowerCase()}</p>
              <p className="text-3xl font-bold font-mono text-white mt-1">{formatKRW(data?.total || 0)}</p>
            </div>
            <div className="text-4xl">💸</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Donut chart */}
            <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
              <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Por categoría</h2>
              {categoryData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie data={categoryData} innerRadius={55} outerRadius={80} dataKey="value" paddingAngle={3}>
                        {categoryData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Pie>
                      <Tooltip
                        formatter={(v) => formatKRW(v)}
                        contentStyle={{ background: "#1A1A24", border: "1px solid #2A2A3A", borderRadius: "12px" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 mt-2">
                    {categoryData.sort((a, b) => b.value - a.value).map((cat) => (
                      <div key={cat.name} className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: cat.color }} />
                        <div className="flex-1 h-1.5 bg-[#2A2A3A] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${(cat.value / (data?.total || 1)) * 100}%`, background: cat.color }}
                          />
                        </div>
                        <span className="text-xs font-mono text-white w-24 text-right">{formatKRW(cat.value)}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-[#6B7280] text-sm text-center py-8">Sin gastos en este período</p>
              )}
            </div>

            {/* Weekly line chart */}
            <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
              <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Últimos 7 días</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2A2A3A" />
                  <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                  <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} tickFormatter={(v) => `₩${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={(v) => [formatKRW(v), "Gasto"]}
                    contentStyle={{ background: "#1A1A24", border: "1px solid #2A2A3A", borderRadius: "12px" }}
                  />
                  <Line type="monotone" dataKey="total" stroke="#7C3AED" strokeWidth={2} dot={{ fill: "#7C3AED", r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Transactions */}
          <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
            <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">
              Transacciones ({data?.items?.length || 0})
            </h2>
            {data?.items?.length > 0 ? (
              <div className="space-y-2">
                {data.items.map((item) => (
                  <div key={item.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-[#22223A] transition-colors group">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-sm shrink-0"
                      style={{ background: categoryColor(item.category) + "22", color: categoryColor(item.category) }}
                    >
                      {categoryLabel(item.category).charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">{item.description || categoryLabel(item.category)}</p>
                      <p className="text-[#6B7280] text-xs">{formatDate(item.date)} · {categoryLabel(item.category)}</p>
                    </div>
                    <span className="font-mono font-semibold text-white shrink-0">
                      {item.currency === "KRW" ? formatKRW(item.amount) : `${item.currency} ${item.amount.toFixed(2)}`}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[#6B7280] text-sm text-center py-8">Sin transacciones en este período</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
