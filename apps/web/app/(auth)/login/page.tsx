'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import Link from 'next/link'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const router = useRouter()

    const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
        const body = new URLSearchParams()
        body.append('username', email)
        body.append('password', password)

        const res = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })

        localStorage.setItem('token', res.data.access_token)
        router.push('/dashboard')
    } catch (err) {
        alert('Login failed')
    }
    }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl mb-4 font-bold">Login</h2>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 p-2 border rounded"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 p-2 border rounded"
        />
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          Login
        </button>
        <p className="mt-4 text-sm">
          Don't have an account? <Link href="/register" className="text-blue-500">Register</Link>
        </p>
      </form>
    </div>
  )
}
