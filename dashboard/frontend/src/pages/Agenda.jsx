import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate, formatTime, formatDateTime } from "../lib/utils";
import { CardSkeleton } from "../components/Skeleton";
import { Clock, MapPin, X } from "lucide-react";

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

  useEffect(() => {
    Promise.all([api.calendar(14), api.reminders()])
      .then(([cal, rem]) => {
        setEvents(cal.events);
        setReminders(rem.reminders);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="space-y-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>;
  }

  const grouped = groupByDate(events);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Agenda</h1>

      {/* Events */}
      <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
        <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">Próximos 14 días</h2>
        {grouped.length > 0 ? (
          <div className="space-y-6">
            {grouped.map(([date, evs]) => (
              <div key={date}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="text-xs font-semibold text-[#7C3AED] uppercase tracking-wider">{formatDate(date)}</div>
                  <div className="flex-1 h-px bg-[#2A2A3A]" />
                </div>
                <div className="space-y-2">
                  {evs.map((ev) => (
                    <div key={ev.id} className="flex gap-3 p-4 bg-[#0F0F13] rounded-xl hover:bg-[#22223A] transition-colors">
                      <div className="w-1 rounded-full bg-[#7C3AED] shrink-0 my-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium">{ev.title}</p>
                        {!ev.all_day && (
                          <div className="flex items-center gap-1 text-[#6B7280] text-xs mt-1">
                            <Clock size={11} />
                            {formatTime(ev.start)}
                            {ev.end && ` — ${formatTime(ev.end)}`}
                          </div>
                        )}
                        {ev.all_day && <span className="text-xs text-[#6B7280]">Todo el día</span>}
                        {ev.location && (
                          <div className="flex items-center gap-1 text-[#6B7280] text-xs mt-0.5">
                            <MapPin size={11} />
                            {ev.location}
                          </div>
                        )}
                        {ev.description && (
                          <p className="text-[#9CA3AF] text-xs mt-1 line-clamp-2">{ev.description}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-[#6B7280]">
            <span className="text-4xl mb-2">📭</span>
            <span className="text-sm">Sin eventos los próximos 14 días</span>
          </div>
        )}
      </div>

      {/* Reminders */}
      <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5">
        <h2 className="text-sm font-medium text-[#9CA3AF] mb-4 uppercase tracking-wide">
          Recordatorios pendientes {reminders.length > 0 && `(${reminders.length})`}
        </h2>
        {reminders.length > 0 ? (
          <div className="space-y-2">
            {reminders.map((r) => (
              <div key={r.sk} className="flex items-center gap-3 p-3 bg-[#0F0F13] rounded-xl">
                <Clock size={16} className="text-[#7C3AED] shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium">{r.message}</p>
                  <p className="text-[#6B7280] text-xs mt-0.5">{formatDateTime(r.remind_at)}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-[#6B7280]">
            <span className="text-3xl mb-2">✅</span>
            <span className="text-sm">Sin recordatorios pendientes</span>
          </div>
        )}
      </div>
    </div>
  );
}
