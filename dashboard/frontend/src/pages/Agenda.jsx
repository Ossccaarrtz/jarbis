import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { formatDate, formatTime, formatDateTime } from "../lib/utils";
import { CardSkeleton } from "../components/Skeleton";
import { Clock, MapPin, RotateCw } from "lucide-react";

function groupByDate(events) {
  const groups = {};
  for (const ev of events) {
    const d = ev.start?.slice(0, 10) || "unknown";
    if (!groups[d]) groups[d] = [];
    groups[d].push(ev);
  }
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}

export default function Agenda() {
  const [events, setEvents] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([api.calendar(14), api.reminders()])
      .then(([cal, rem]) => { setEvents(cal.events); setReminders(rem.reminders); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const grouped = groupByDate(events);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[15px] font-semibold text-white/90 tracking-tight">Agenda</h1>
        <button onClick={load} disabled={loading} className="flex items-center gap-1.5 text-white/30 hover:text-white/60 transition-colors text-[12px]">
          <RotateCw size={13} className={loading ? "animate-spin" : ""} />
          Actualizar
        </button>
      </div>

      {loading && !events.length ? (
        <div className="space-y-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : (
        <div className="space-y-4">
          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
            <span className="text-white/40 text-[11px] uppercase tracking-widest">Próximos 14 días</span>
            {grouped.length > 0 ? (
              <div className="mt-4 space-y-5">
                {grouped.map(([date, evs]) => (
                  <div key={date}>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-[11px] font-medium text-violet-400/70 capitalize">{formatDate(date)}</span>
                      <div className="flex-1 h-px bg-white/[0.05]" />
                    </div>
                    <div className="space-y-1.5">
                      {evs.map(ev => (
                        <div key={ev.id} className="flex gap-2.5 p-3 bg-white/[0.02] rounded-lg border border-white/[0.04] hover:bg-white/[0.04] transition-colors">
                          <div className="w-0.5 rounded-full bg-violet-500/50 shrink-0 my-0.5" />
                          <div className="flex-1 min-w-0">
                            <p className="text-white/75 text-[13px] font-medium">{ev.title}</p>
                            {!ev.all_day && (
                              <div className="flex items-center gap-1 text-white/25 text-[11px] mt-0.5">
                                <Clock size={10} />
                                {formatTime(ev.start)}{ev.end && ` — ${formatTime(ev.end)}`}
                              </div>
                            )}
                            {ev.all_day && <span className="text-white/20 text-[11px]">Todo el día</span>}
                            {ev.location && (
                              <div className="flex items-center gap-1 text-white/20 text-[11px] mt-0.5">
                                <MapPin size={10} />
                                {ev.location}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/20 text-[12px] text-center py-10">Sin eventos los próximos 14 días</p>
            )}
          </div>

          <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-white/40 text-[11px] uppercase tracking-widest">Recordatorios pendientes</span>
              {reminders.length > 0 && <span className="text-white/25 text-[11px]">{reminders.length}</span>}
            </div>
            {reminders.length > 0 ? (
              <div className="mt-3 space-y-1.5">
                {reminders.map(r => (
                  <div key={r.sk} className="flex items-center gap-3 py-2.5 border-b border-white/[0.04] last:border-0">
                    <Clock size={13} className="text-violet-400/50 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-white/60 text-[13px]">{r.message}</p>
                      <p className="text-white/25 text-[11px] mt-0.5">{formatDateTime(r.remind_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/20 text-[12px] text-center py-8">Sin recordatorios pendientes</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
