'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)

    try {
      // aqui SEM FormData pra evitar qualquer bug de name
      const body = new URLSearchParams()
      body.set('username', email)
      body.set('password', password)

      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })

      const text = await res.text()
      if (!res.ok) {
        console.error('Login failed:', res.status, text)
        alert('Falha no login')
        return
      }

      const data = JSON.parse(text)
      localStorage.setItem('token', data.access_token)

      // navegação mais "bruta" pra não ter cache estranho do Next dev
      window.location.assign('/dashboard')
    } catch (err) {
      console.error(err)
      alert('Falha no login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl mb-4 font-bold">Login</h2>

        <input
          name="username"
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
          placeholder="Password"
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
          {loading ? 'Entrando...' : 'Login'}
        </button>

        <p className="mt-4 text-sm">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-blue-500">
            Register
          </Link>
        </p>
      </form>
    </div>
  )
}
