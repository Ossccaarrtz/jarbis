export default function StatCard({ icon: Icon, label, value, sub, color = "#8B5CF6" }) {
  return (
    <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-white/30 text-[11px] font-medium uppercase tracking-widest">{label}</span>
        {Icon && <Icon size={14} strokeWidth={1.75} style={{ color }} className="opacity-60" />}
      </div>
      <div>
        <p className="text-white text-2xl font-semibold tracking-tight leading-none">{value}</p>
        {sub && <p className="text-white/30 text-[11px] mt-1.5">{sub}</p>}
      </div>
    </div>
  );
}
