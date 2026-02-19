"use client";

import { login } from "@/lib/auth";
import { useState } from "react";
import Link from "next/link";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      // ✅ UM ÚNICO CAMINHO: axios (/api/v1) + rewrite => api:8000
      await login(email, password);
      window.location.assign("/dashboard");
    } catch (err) {
      console.error(err);
      alert("Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl mb-4 font-bold">Login</h2>

        <input
          name="email"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 p-2 border rounded"
          autoComplete="email"
        />

        <input
          name="password"
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 p-2 border rounded"
          autoComplete="current-password"
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-500 text-white p-2 rounded disabled:opacity-60"
        >
          {loading ? "Entrando..." : "Login"}
        </button>

        <p className="mt-4 text-sm">
          Não tem conta?{" "}
          <Link href="/register" className="text-blue-500">
            Registrar
          </Link>
        </p>
      </form>
    </div>
  );
}