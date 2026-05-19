import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { getToken } from "./lib/api";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Expenses from "./pages/Expenses";
import Nutrition from "./pages/Nutrition";
import Agenda from "./pages/Agenda";

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());

  if (!authed) {
    return <Login onLogin={() => setAuthed(true)} />;
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/nutrition" element={<Nutrition />} />
          <Route path="/agenda" element={<Agenda />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
