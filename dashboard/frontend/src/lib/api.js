const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

let _token = localStorage.getItem("jarbis_token") || "";

export function setToken(t) {
  _token = t;
  localStorage.setItem("jarbis_token", t);
}

export function getToken() {
  return _token;
}

async function request(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${_token}`,
      ...(opts.headers || {}),
    },
  });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  summary: () => request("/api/summary"),
  expenses: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/api/expenses${q ? "?" + q : ""}`);
  },
  expensesToday: () => request("/api/expenses/today"),
  expensesWeekly: () => request("/api/expenses/weekly"),
  nutrition: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/api/nutrition${q ? "?" + q : ""}`);
  },
  nutritionToday: () => request("/api/nutrition/today"),
  nutritionWeekly: () => request("/api/nutrition/weekly"),
  calendar: (days = 7) => request(`/api/calendar?days_ahead=${days}`),
  reminders: () => request("/api/reminders"),
};
