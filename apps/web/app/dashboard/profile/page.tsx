'use client'

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'

type Me = {
  id: string
  email: string
  full_name?: string | null
  avatar_url?: string | null
  phone?: string | null
  is_active: boolean
}

export default function ProfilePage() {
  const [me, setMe] = useState<Me | null>(null)
  const [form, setForm] = useState({ full_name: '', avatar_url: '', phone: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedMsg, setSavedMsg] = useState<string | null>(null)

  const load = async () => {
    setError(null)
    setSavedMsg(null)
    try {
      const res = await api.get('/users/me')
      const u: Me = res.data
      setMe(u)
      setForm({
        full_name: u.full_name ?? '',
        avatar_url: u.avatar_url ?? '',
        phone: u.phone ?? '',
      })
    } catch (e) {
      console.error(e)
      setError('Falha ao carregar perfil.')
      setMe(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const canSave = useMemo(() => !saving && !!me, [saving, me])

  const save = async () => {
    if (!canSave) return
    setSaving(true)
    setError(null)
    setSavedMsg(null)
    try {
      const payload = {
        full_name: form.full_name || null,
        avatar_url: form.avatar_url || null,
        phone: form.phone || null,
      }
      const res = await api.put('/users/me', payload)
      const u: Me = res.data
      setMe(u)
      setSavedMsg('Salvo.')
    } catch (e) {
      console.error(e)
      setError('Falha ao salvar perfil.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Perfil</h1>
        <button
          className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
          onClick={load}
          disabled={loading}
        >
          Recarregar
        </button>
      </div>

      <div className="bg-white p-6 rounded shadow max-w-2xl">
        {error && <div className="mb-3 text-sm text-red-600">{error}</div>}
        {savedMsg && <div className="mb-3 text-sm text-green-700">{savedMsg}</div>}

        {loading ? (
          <div className="text-gray-500">Carregando...</div>
        ) : me ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Email</label>
              <input className="w-full border p-2 rounded bg-gray-50" value={me.email} readOnly />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Full Name</label>
              <input
                className="w-full border p-2 rounded"
                value={form.full_name}
                onChange={e => setForm({ ...form, full_name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Avatar URL</label>
              <input
                className="w-full border p-2 rounded"
                value={form.avatar_url}
                onChange={e => setForm({ ...form, avatar_url: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Phone</label>
              <input
                className="w-full border p-2 rounded"
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
              />
            </div>

            <button
              className="w-full bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60"
              onClick={save}
              disabled={!canSave}
            >
              Salvar
            </button>
          </div>
        ) : (
          <div className="text-gray-500">Sem dados.</div>
        )}
      </div>
    </div>
  )
}

