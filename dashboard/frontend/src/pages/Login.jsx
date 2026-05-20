import { useState } from "react";
import { setToken } from "../lib/api";

export default function Login({ onLogin }) {
  const [token, setTokenInput] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setToken(token);
    try {
      const res = await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/summary", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) { onLogin(); }
      else { setError(true); setToken(""); }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center px-4">
      <div className="w-full max-w-xs">
        <div className="mb-8">
          <h1 className="text-[22px] font-semibold tracking-tight text-white">
            jarbis<span className="text-violet-500">.</span>
          </h1>
          <p className="text-white/30 text-[13px] mt-1">Introduce tu token de acceso</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="password"
            value={token}
            onChange={(e) => { setTokenInput(e.target.value); setError(false); }}
            placeholder="••••••••••••"
            autoFocus
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white text-[14px] placeholder-white/20 focus:outline-none focus:border-violet-500/50 transition-colors"
          />
          {error && <p className="text-red-400/80 text-[12px]">Token incorrecto</p>}
          <button
            type="submit"
            disabled={loading || !token}
            className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white text-[14px] font-medium py-3 rounded-xl transition-colors"
          >
            {loading ? "Verificando..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
