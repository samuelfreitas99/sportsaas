'use client'

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'

type BillingMode = 'MEMBERSHIP' | 'PER_SESSION' | 'HYBRID'
type BillingCycle = 'MONTHLY' | 'WEEKLY' | 'CUSTOM_WEEKS'

type BillingSettings = {
  id: string
  org_id: string
  billing_mode: BillingMode
  cycle: BillingCycle
  cycle_weeks: number | null
  anchor_date: string
  due_day: number
  membership_amount: number
  session_amount: number
}

export default function BillingPage() {
  const [orgId, setOrgId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [settings, setSettings] = useState<BillingSettings | null>(null)

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('currentOrgId') : null
    setOrgId(saved)
  }, [])

  const fetchSettings = async (id: string) => {
    setError(null)
    try {
      const res = await api.get(`/orgs/${id}/billing-settings`)
      setSettings(res.data)
    } catch (e) {
      console.error(e)
      setSettings(null)
      setError('Falha ao carregar billing settings (verifique permissões).')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!orgId) {
      setLoading(false)
      return
    }
    fetchSettings(orgId)
  }, [orgId])

  const canSave = useMemo(() => {
    if (!settings) return false
    if (settings.due_day < 1 || settings.due_day > 31) return false
    if (settings.cycle === 'CUSTOM_WEEKS' && (!settings.cycle_weeks || settings.cycle_weeks <= 0))
      return false
    return true
  }, [settings])

  const save = async () => {
    if (!orgId || !settings) return
    if (!canSave) return
    setSaving(true)
    setError(null)
    try {
      await api.put(`/orgs/${orgId}/billing-settings`, settings)
      await fetchSettings(orgId)
    } catch (e) {
      console.error(e)
      setError('Falha ao salvar billing settings.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Billing</h1>
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
        <div className="bg-white p-6 rounded shadow max-w-2xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Configurações</h2>
            <button
              className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
              onClick={() => fetchSettings(orgId)}
              disabled={loading}
            >
              Recarregar
            </button>
          </div>

          {error && <div className="mb-3 text-sm text-red-600">{error}</div>}

          {loading ? (
            <div className="text-gray-500">Carregando...</div>
          ) : settings ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Billing Mode</label>
                  <select
                    className="w-full border p-2 rounded"
                    value={settings.billing_mode}
                    onChange={e =>
                      setSettings({ ...settings, billing_mode: e.target.value as BillingMode })
                    }
                  >
                    <option value="HYBRID">HYBRID</option>
                    <option value="MEMBERSHIP">MEMBERSHIP</option>
                    <option value="PER_SESSION">PER_SESSION</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Cycle</label>
                  <select
                    className="w-full border p-2 rounded"
                    value={settings.cycle}
                    onChange={e => setSettings({ ...settings, cycle: e.target.value as BillingCycle })}
                  >
                    <option value="MONTHLY">MONTHLY</option>
                    <option value="WEEKLY">WEEKLY</option>
                    <option value="CUSTOM_WEEKS">CUSTOM_WEEKS</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Anchor Date</label>
                  <input
                    className="w-full border p-2 rounded"
                    type="date"
                    value={settings.anchor_date}
                    onChange={e => setSettings({ ...settings, anchor_date: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Due Day</label>
                  <input
                    className="w-full border p-2 rounded"
                    type="number"
                    value={settings.due_day}
                    onChange={e => setSettings({ ...settings, due_day: parseInt(e.target.value || '0') })}
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Cycle Weeks</label>
                  <input
                    className="w-full border p-2 rounded"
                    type="number"
                    value={settings.cycle_weeks ?? ''}
                    onChange={e =>
                      setSettings({
                        ...settings,
                        cycle_weeks: e.target.value === '' ? null : parseInt(e.target.value),
                      })
                    }
                    placeholder="Somente para CUSTOM_WEEKS"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Membership Amount</label>
                  <input
                    className="w-full border p-2 rounded"
                    type="number"
                    step="0.01"
                    value={settings.membership_amount}
                    onChange={e =>
                      setSettings({ ...settings, membership_amount: parseFloat(e.target.value || '0') })
                    }
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">Session Amount</label>
                  <input
                    className="w-full border p-2 rounded"
                    type="number"
                    step="0.01"
                    value={settings.session_amount}
                    onChange={e =>
                      setSettings({ ...settings, session_amount: parseFloat(e.target.value || '0') })
                    }
                  />
                </div>
              </div>

              <button
                className="w-full bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60"
                onClick={save}
                disabled={!canSave || saving}
              >
                Salvar
              </button>
            </div>
          ) : (
            <div className="text-gray-500">Sem dados.</div>
          )}
        </div>
      )}
    </div>
  )
}
