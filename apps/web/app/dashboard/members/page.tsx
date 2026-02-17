'use client'

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'

type OrgRole = 'OWNER' | 'ADMIN' | 'MEMBER'
type MemberType = 'MONTHLY' | 'GUEST'

type Member = {
  id: string
  user_id: string
  org_id: string
  role: OrgRole
  member_type: MemberType
  nickname?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  user: {
    id: string
    email: string
    full_name?: string | null
  }
}

export default function MembersPage() {
  const [orgId, setOrgId] = useState<string | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [newEmail, setNewEmail] = useState('')
  const [newRole, setNewRole] = useState<OrgRole>('MEMBER')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('currentOrgId') : null
    setOrgId(saved)
  }, [])

  const refresh = async (id: string) => {
    setError(null)
    try {
      const res = await api.get(`/orgs/${id}/members`)
      setMembers(res.data)
    } catch (e) {
      console.error(e)
      setMembers([])
      setError('Falha ao carregar membros')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!orgId) {
      setLoading(false)
      return
    }
    refresh(orgId)
  }, [orgId])

  const canSubmit = useMemo(() => newEmail.trim().length > 3, [newEmail])

  const addMember = async () => {
    if (!orgId) return
    if (!canSubmit) return
    setSaving(true)
    setError(null)
    try {
      await api.post(`/orgs/${orgId}/members`, { email: newEmail.trim(), role: newRole })
      setNewEmail('')
      setNewRole('MEMBER')
      await refresh(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao adicionar membro')
    } finally {
      setSaving(false)
    }
  }

  const changeRole = async (memberId: string, role: OrgRole) => {
    if (!orgId) return
    setError(null)
    try {
      await api.patch(`/orgs/${orgId}/members/${memberId}/role`, { role })
      await refresh(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao alterar role')
    }
  }

  const changeMemberType = async (memberId: string, member_type: MemberType) => {
    if (!orgId) return
    setError(null)
    try {
      await api.patch(`/orgs/${orgId}/members/${memberId}`, { member_type })
      await refresh(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao alterar member_type')
    }
  }

  const removeMember = async (memberId: string) => {
    if (!orgId) return
    setError(null)
    try {
      await api.delete(`/orgs/${orgId}/members/${memberId}`)
      await refresh(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao remover membro')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Membros</h1>
        <div className="text-sm text-gray-500">
          Org: <span className="font-mono">{orgId ?? '-'}</span>
        </div>
      </div>

      {!orgId && (
        <div className="bg-white p-6 rounded shadow">
          <p className="text-gray-700">Selecione uma organização no Dashboard primeiro.</p>
        </div>
      )}

      {orgId && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white p-6 rounded shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Lista</h2>
              <button
                onClick={() => refresh(orgId)}
                className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
                disabled={loading}
              >
                Recarregar
              </button>
            </div>

            {error && <div className="mb-3 text-sm text-red-600">{error}</div>}

            {loading ? (
              <div className="text-gray-500">Carregando...</div>
            ) : (
              <div className="space-y-2">
                {members.map(m => (
                  <div key={m.id} className="border rounded p-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-semibold truncate">
                        {m.nickname || m.user.full_name || m.user.email}
                      </div>
                      <div className="text-sm text-gray-500 truncate">{m.user.email}</div>
                      <div className="mt-1 flex gap-2">
                        <span
                          className={`text-xs px-2 py-0.5 rounded border ${
                            m.member_type === 'MONTHLY'
                              ? 'bg-blue-50 text-blue-700 border-blue-200'
                              : 'bg-yellow-50 text-yellow-800 border-yellow-200'
                          }`}
                        >
                          {m.member_type}
                        </span>
                        {!m.is_active && (
                          <span className="text-xs px-2 py-0.5 rounded border bg-gray-100 text-gray-700 border-gray-200">
                            INACTIVE
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <select
                        className="border p-2 rounded text-sm"
                        value={m.member_type}
                        onChange={e => changeMemberType(m.id, e.target.value as MemberType)}
                      >
                        <option value="MONTHLY">MONTHLY</option>
                        <option value="GUEST">GUEST</option>
                      </select>
                      <select
                        className="border p-2 rounded text-sm"
                        value={m.role}
                        onChange={e => changeRole(m.id, e.target.value as OrgRole)}
                      >
                        <option value="OWNER">OWNER</option>
                        <option value="ADMIN">ADMIN</option>
                        <option value="MEMBER">MEMBER</option>
                      </select>
                      <button
                        onClick={() => removeMember(m.id)}
                        className="text-sm px-3 py-2 rounded bg-red-600 text-white hover:bg-red-700"
                      >
                        Remover
                      </button>
                    </div>
                  </div>
                ))}
                {members.length === 0 && (
                  <div className="text-gray-500">Nenhum membro encontrado.</div>
                )}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-bold mb-4">Adicionar</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Email</label>
                <input
                  className="w-full border p-2 rounded"
                  value={newEmail}
                  onChange={e => setNewEmail(e.target.value)}
                  placeholder="email@exemplo.com"
                  type="email"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-1">Role</label>
                <select
                  className="w-full border p-2 rounded"
                  value={newRole}
                  onChange={e => setNewRole(e.target.value as OrgRole)}
                >
                  <option value="MEMBER">MEMBER</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="OWNER">OWNER</option>
                </select>
              </div>

              <button
                onClick={addMember}
                disabled={!canSubmit || saving}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60"
              >
                Adicionar membro
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
