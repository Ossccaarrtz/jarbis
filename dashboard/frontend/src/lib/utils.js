export function formatKRW(amount) {
  return `₩${Math.round(amount).toLocaleString("ko-KR")}`;
}

export function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("es-MX", { weekday: "short", month: "short", day: "numeric" });
}

export function formatTime(dateStr) {
  if (!dateStr || !dateStr.includes("T")) return "";
  const d = new Date(dateStr);
  return d.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

export function formatDateTime(dateStr) {
  if (!dateStr) return "";
  return `${formatDate(dateStr)} ${formatTime(dateStr)}`.trim();
}

function localDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function today() {
  return localDateStr(new Date());
}

export function monthStart() {
  const d = new Date();
  d.setDate(1);
  return localDateStr(d);
}

export const CATEGORY_COLORS = {
  comida: "#F59E0B",
  food: "#F59E0B",
  transporte: "#3B82F6",
  transport: "#3B82F6",
  entretenimiento: "#EC4899",
  entertainment: "#EC4899",
  salud: "#10B981",
  health: "#10B981",
  otro: "#6B7280",
  other: "#6B7280",
  compras: "#8B5CF6",
  shopping: "#8B5CF6",
  cafe: "#F97316",
  coffee: "#F97316",
};

export function categoryColor(cat) {
  return CATEGORY_COLORS[cat?.toLowerCase()] || "#6B7280";
}

export function categoryLabel(cat) {
  const labels = {
    comida: "Comida", food: "Comida",
    transporte: "Transporte", transport: "Transporte",
    entretenimiento: "Entretenimiento",
    salud: "Salud", health: "Salud",
    otro: "Otro", other: "Otro",
    compras: "Compras", shopping: "Compras",
    cafe: "Café", coffee: "Café",
  };
  return labels[cat?.toLowerCase()] || (cat ? cat.charAt(0).toUpperCase() + cat.slice(1) : "Otro");
}
