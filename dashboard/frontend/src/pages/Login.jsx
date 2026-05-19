import { useState } from "react";
import { setToken } from "../lib/api";

export default function Login({ onLogin }) {
  const [token, setTokenInput] = useState("");
  const [error, setError] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setToken(token);
    try {
      const res = await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/summary", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        onLogin();
      } else {
        setError(true);
        setToken("");
      }
    } catch {
      setError(true);
    }
  }

  return (
    <div className="min-h-screen bg-[#0F0F13] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">Jarbis<span className="text-[#7C3AED]">.</span></h1>
          <p className="text-[#6B7280] mt-2 text-sm">Tu asistente personal</p>
        </div>
        <form onSubmit={handleSubmit} className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-6 space-y-4">
          <div>
            <label className="block text-sm text-[#9CA3AF] mb-1.5">Token de acceso</label>
            <input
              type="password"
              value={token}
              onChange={(e) => { setTokenInput(e.target.value); setError(false); }}
              placeholder="••••••••"
              className="w-full bg-[#0F0F13] border border-[#2A2A3A] rounded-xl px-4 py-2.5 text-white placeholder-[#4B5563] focus:outline-none focus:border-[#7C3AED] transition-colors"
            />
            {error && <p className="text-red-400 text-xs mt-1">Token incorrecto</p>}
          </div>
          <button
            type="submit"
            className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-medium py-2.5 rounded-xl transition-colors"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
