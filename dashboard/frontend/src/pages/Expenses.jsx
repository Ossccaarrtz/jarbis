import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { formatKRW, formatDate, categoryColor, categoryLabel, monthStart, today } from "../lib/utils";
import { CardSkeleton } from "../components/Skeleton";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from "recharts";
import { RotateCw } from "lucide-react";

function getRanges() {
  return [
    { label: "Hoy", start: today(), end: today() },
    { label: "Semana", start: (() => { const d = new Date(); d.setDate(d.getDate() - 6); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; })(), end: today() },
    { label: "Mes", start: monthStart(), end: today() },
  ];
}

export default function Expenses() {
  const [range, setRange] = useState(2);
  const [data, setData] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const load = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    setLoading(true);
    const r = getRanges()[range];
    Promise.all([
      api.expenses({ start_date: r.start, end_date: r.end }),
      api.expensesWeekly(),
    ]).then(([exp, wk]) => { setData(exp); setWeekly(wk.days); })
      .finally(() => setLoading(false));
  }, [range, tick]);

  const categoryData = data
    ? Object.entries(data.by_category).map(([k, v]) => ({ name: categoryLabel(k), value: v, color: categoryColor(k) }))
    : [];

  const RANGES = getRanges();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[15px] font-semibold text-white/90 tracking-tight">Gastos</h1>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-white/[0.04] rounded-lg p-1">
            {RANGES.map((r, i) => (
              <button key={i} onClick={() => setRange(i)}
                className={`px-3 py-1 rounded-md text-[12px] font-medium transition-all ${
                  range === i ? "bg-white/[0.08] text-white" : "text-white/30 hover:text-white/50"
                }`}
              >{r.label}</button>
            ))}
          </div>
          <button onClick={load} disabled={loading} className="text-white/30 hover:text-white/60 transition-colors p-1">
            <RotateCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {loading && !data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : (
        <div className="space-y-4">
          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4 flex items-end justify-between">
            <div>
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Total {RANGES[range].label.toLowerCase()}</span>
              <p className="text-white text-3xl font-semibold tracking-tight mt-1">{formatKRW(data?.total || 0)}</p>
            </div>
            <span className="text-white/20 text-[12px] mb-1">{data?.items?.length || 0} transacciones</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Por categoría</span>
              {categoryData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={160} className="mt-2">
                    <PieChart>
                      <Pie data={categoryData} innerRadius={48} outerRadius={68} dataKey="value" paddingAngle={2} strokeWidth={0}>
                        {categoryData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Pie>
                      <Tooltip formatter={(v) => formatKRW(v)} contentStyle={{ background: "#0F0F18", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", fontSize: "12px" }} itemStyle={{ color: "#fff" }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 mt-1">
                    {categoryData.sort((a, b) => b.value - a.value).map((cat) => (
                      <div key={cat.name} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: cat.color }} />
                        <div className="flex-1 h-px bg-white/[0.06]" style={{ background: `linear-gradient(to right, ${cat.color}40 ${(cat.value/(data?.total||1))*100}%, transparent 0%)` }} />
                        <span className="text-white/60 text-[12px] font-mono w-20 text-right">{formatKRW(cat.value)}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-white/20 text-[12px] text-center py-8">Sin gastos en este período</p>
              )}
            </div>

            <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Últimos 7 días</span>
              <ResponsiveContainer width="100%" height={200} className="mt-2">
                <LineChart data={weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} tickFormatter={(d) => d.slice(5)} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => [formatKRW(v), "Gasto"]} contentStyle={{ background: "#0F0F18", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", fontSize: "12px" }} itemStyle={{ color: "#fff" }} />
                  <Line type="monotone" dataKey="total" stroke="#8B5CF6" strokeWidth={1.5} dot={{ fill: "#8B5CF6", r: 3, strokeWidth: 0 }} activeDot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
            <span className="text-white/40 text-[11px] uppercase tracking-widest">Transacciones</span>
            {data?.items?.length > 0 ? (
              <div className="mt-3 space-y-px">
                {data.items.map((item) => (
                  <div key={item.id} className="flex items-center gap-3 py-2.5 border-b border-white/[0.04] last:border-0">
                    <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: categoryColor(item.category) }} />
                    <div className="flex-1 min-w-0">
                      <p className="text-white/70 text-[13px] truncate">{item.description || categoryLabel(item.category)}</p>
                      <p className="text-white/25 text-[11px]">{formatDate(item.date)} · {categoryLabel(item.category)}</p>
                    </div>
                    <span className="font-mono text-[13px] text-white/80 shrink-0">
                      {item.currency === "KRW" ? formatKRW(item.amount) : `${item.currency} ${item.amount.toFixed(2)}`}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/20 text-[12px] text-center py-8">Sin transacciones en este período</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
