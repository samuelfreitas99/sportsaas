'use client'

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'

type ChargeStatus = 'PENDING' | 'PAID' | 'VOID'
type ChargeType = 'MEMBERSHIP' | 'PER_SESSION'

type Charge = {
  id: string
  org_id: string
  org_member_id: string
  cycle_key: string
  type: ChargeType
  status: ChargeStatus
  amount: number
  paid_at?: string | null
  voided_at?: string | null
  ledger_entry_id?: string | null
  org_member: {
    id: string
    user_id: string
    role: 'OWNER' | 'ADMIN' | 'MEMBER'
    user: {
      email: string
      full_name?: string | null
    }
  }
}

export default function ChargesPage() {
  const [orgId, setOrgId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Charge[]>([])

  const [cycleKey, setCycleKey] = useState('')
  const [status, setStatus] = useState<ChargeStatus | ''>('')
  const [memberId, setMemberId] = useState('')

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('currentOrgId') : null
    setOrgId(saved)
  }, [])

  const queryString = useMemo(() => {
    const qs = new URLSearchParams()
    if (cycleKey.trim()) qs.set('cycle_key', cycleKey.trim())
    if (memberId.trim()) qs.set('member_id', memberId.trim())
    if (status) qs.set('status', status)
    const s = qs.toString()
    return s ? `?${s}` : ''
  }, [cycleKey, memberId, status])

  const fetchCharges = async (id: string) => {
    setError(null)
    try {
      const res = await api.get(`/orgs/${id}/charges${queryString}`)
      setItems(res.data)
    } catch (e) {
      console.error(e)
      setItems([])
      setError('Falha ao carregar charges (verifique permissões).')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!orgId) {
      setLoading(false)
      return
    }
    fetchCharges(orgId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId])

  const applyFilters = async () => {
    if (!orgId) return
    setLoading(true)
    await fetchCharges(orgId)
  }

  const updateStatus = async (chargeId: string, next: ChargeStatus) => {
    if (!orgId) return
    setError(null)
    try {
      await api.patch(`/orgs/${orgId}/charges/${chargeId}`, { status: next })
      await fetchCharges(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao atualizar charge.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Charges</h1>
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
        <div className="space-y-6">
          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-bold mb-4">Filtros</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <input
                className="border p-2 rounded"
                placeholder="cycle_key"
                value={cycleKey}
                onChange={e => setCycleKey(e.target.value)}
              />
              <input
                className="border p-2 rounded"
                placeholder="member_id"
                value={memberId}
                onChange={e => setMemberId(e.target.value)}
              />
              <select
                className="border p-2 rounded"
                value={status}
                onChange={e => setStatus(e.target.value as ChargeStatus | '')}
              >
                <option value="">ALL</option>
                <option value="PENDING">PENDING</option>
                <option value="PAID">PAID</option>
                <option value="VOID">VOID</option>
              </select>
              <button
                className="bg-blue-600 text-white px-4 py-2 rounded"
                onClick={applyFilters}
              >
                Aplicar
              </button>
            </div>
          </div>

          <div className="bg-white p-6 rounded shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Lista</h2>
              <button
                className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
                onClick={() => fetchCharges(orgId)}
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
                {items.map(c => (
                  <div key={c.id} className="border rounded p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-semibold truncate">
                        {c.org_member.user.full_name || c.org_member.user.email}
                      </div>
                      <div className="text-sm text-gray-500 truncate">
                        {c.cycle_key} • {c.type} • {c.status}
                      </div>
                      <div className="text-xs text-gray-400 truncate font-mono">
                        member: {c.org_member_id}
                      </div>
                    </div>

                    <div className="flex items-center justify-between md:justify-end gap-3">
                      <div className="font-bold">${c.amount}</div>
                      <div className="flex gap-2">
                        <button
                          className="px-3 py-2 rounded bg-green-600 text-white disabled:opacity-60"
                          disabled={c.status !== 'PENDING'}
                          onClick={() => updateStatus(c.id, 'PAID')}
                        >
                          Marcar PAID
                        </button>
                        <button
                          className="px-3 py-2 rounded bg-gray-700 text-white disabled:opacity-60"
                          disabled={c.status !== 'PENDING'}
                          onClick={() => updateStatus(c.id, 'VOID')}
                        >
                          VOID
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                {items.length === 0 && <div className="text-gray-500">Nenhuma charge encontrada.</div>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
