export default function StatCard({ icon, label, value, sub, color = "#8B5CF6" }) {
  return (
    <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5 flex items-center gap-4 hover:-translate-y-0.5 transition-transform">
      <div
        className="w-11 h-11 rounded-xl flex items-center justify-center text-xl shrink-0"
        style={{ backgroundColor: color + "22", color }}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[#6B7280] text-xs font-medium uppercase tracking-wide">{label}</p>
        <p className="text-white text-xl font-bold font-mono leading-tight">{value}</p>
        {sub && <p className="text-[#6B7280] text-xs mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}
