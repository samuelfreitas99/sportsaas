'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { useRouter } from 'next/navigation'

interface Org {
  id: string
  name: string
  slug: string
  owner_id: string
}

interface Game {
  id: string
  title: string
  sport: string
  start_at: string
  location: string
}

interface LedgerSummary {
  total_income: number
  total_expense: number
  balance: number
}

export default function Dashboard() {
  const [orgs, setOrgs] = useState<Org[]>([])
  const [selectedOrg, setSelectedOrg] = useState<Org | null>(null)
  const [games, setGames] = useState<Game[]>([])
  const [summary, setSummary] = useState<LedgerSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [newOrgName, setNewOrgName] = useState('')
  const [newGame, setNewGame] = useState({ title: '', sport: '', location: '', start_at: '' })
  const router = useRouter()

  useEffect(() => {
    fetchOrgs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedOrg) {
      fetchGames(selectedOrg.id)
      fetchSummary(selectedOrg.id)
    } else {
      setGames([])
      setSummary(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOrg])

  const fetchOrgs = async () => {
    try {
      const res = await api.get('/orgs/')
      const list: Org[] = res.data
      setOrgs(list)

      const savedId =
        typeof window !== 'undefined' ? localStorage.getItem('currentOrgId') : null
      const found = savedId ? list.find(o => o.id === savedId) : null

      const initial = found || list[0] || null
      setSelectedOrg(initial)

      if (initial) localStorage.setItem('currentOrgId', initial.id)
      setLoading(false)
    } catch (err) {
      console.error(err)
      router.push('/login')
    }
  }

  const createOrg = async () => {
    try {
      const res = await api.post('/orgs/', { name: newOrgName })
      const created: Org = res.data
      const next = [...orgs, created]
      setOrgs(next)
      setSelectedOrg(created)
      localStorage.setItem('currentOrgId', created.id)
      setNewOrgName('')
    } catch (err) {
      console.error(err)
      alert('Failed to create org')
    }
  }

  const fetchGames = async (orgId: string) => {
    try {
      const res = await api.get(`/orgs/${orgId}/games`)
      setGames(res.data)
    } catch (err) {
      console.error(err)
      setGames([])
    }
  }

  const fetchSummary = async (orgId: string) => {
    try {
      const res = await api.get(`/orgs/${orgId}/ledger/summary`)
      setSummary(res.data)
    } catch (err) {
      console.error(err)
      setSummary(null)
    }
  }

    const toISO = (v: string) => (v ? new Date(v).toISOString() : v)

    const createGame = async () => {
    if (!selectedOrg) return
    try {
        await api.post(`/orgs/${selectedOrg.id}/games`, {
        ...newGame,
        start_at: toISO(newGame.start_at),
        })
        fetchGames(selectedOrg.id)
        setNewGame({ title: '', sport: '', location: '', start_at: '' })
    } catch (err) {
        console.error(err)
        alert('Failed to create game')
    }
    }

    const markAttendance = async (gameId: string, status: string) => {
    try {
        await api.post(`/games/${gameId}/attendance`, { status })
        // opcional: refetch games (se depois você incluir status no retorno)
        alert('Attendance marked!')
    } catch (err) {
        console.error(err)
        alert('Failed to mark attendance')
    }
    }


  if (loading) return <div className="p-8">Loading...</div>

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <button
          onClick={() => {
            localStorage.removeItem('token')
            localStorage.removeItem('currentOrgId')
            router.push('/login')
          }}
          className="text-red-500"
        >
          Logout
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sidebar / Org Selector */}
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Organizations</h2>
          <ul>
            {orgs.map(org => (
              <li
                key={org.id}
                className={`p-2 cursor-pointer rounded ${
                  selectedOrg?.id === org.id
                    ? 'bg-blue-100 text-blue-600'
                    : 'hover:bg-gray-100'
                }`}
                onClick={() => {
                  setSelectedOrg(org)
                  localStorage.setItem('currentOrgId', org.id)
                }}
              >
                {org.name}
              </li>
            ))}
          </ul>

          <div className="mt-4 border-t pt-4">
            <input
              className="w-full border p-2 rounded mb-2"
              placeholder="New Org Name"
              value={newOrgName}
              onChange={e => setNewOrgName(e.target.value)}
            />
            <button
              onClick={createOrg}
              className="w-full bg-blue-500 text-white p-2 rounded"
              disabled={!newOrgName.trim()}
            >
              Create Org
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="col-span-3 space-y-8">
          {selectedOrg ? (
            <>
              {/* Stats */}
              <div className="bg-white p-6 rounded shadow grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-gray-500">Income</p>
                  <p className="text-2xl font-bold text-green-500">
                    ${summary?.total_income ?? 0}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-gray-500">Expense</p>
                  <p className="text-2xl font-bold text-red-500">
                    ${summary?.total_expense ?? 0}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-gray-500">Balance</p>
                  <p className="text-2xl font-bold text-blue-500">
                    ${summary?.balance ?? 0}
                  </p>
                </div>
              </div>

              {/* Games */}
              <div className="bg-white p-6 rounded shadow">
                <h2 className="text-2xl font-bold mb-4">Games</h2>

                <div className="grid grid-cols-1 gap-4 mb-4">
                  {games.map(game => (
                    <div
                      key={game.id}
                      className="border p-4 rounded flex justify-between items-center"
                    >
                      <div>
                        <h3 className="font-bold">{game.title}</h3>
                        <p className="text-sm text-gray-600">
                          {game.sport} @ {game.location}
                        </p>
                        <p className="text-xs text-gray-400">
                          {new Date(game.start_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => markAttendance(game.id, 'GOING')}
                          className="bg-green-100 text-green-700 px-3 py-1 rounded hover:bg-green-200"
                        >
                          Going
                        </button>
                        <button
                          onClick={() => markAttendance(game.id, 'MAYBE')}
                          className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded hover:bg-yellow-200"
                        >
                          Maybe
                        </button>
                        <button
                          onClick={() => markAttendance(game.id, 'NOT_GOING')}
                          className="bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
                        >
                          Not Going
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-bold mb-2">Create Game</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      className="border p-2 rounded"
                      placeholder="Title"
                      value={newGame.title}
                      onChange={e => setNewGame({ ...newGame, title: e.target.value })}
                    />
                    <input
                      className="border p-2 rounded"
                      placeholder="Sport"
                      value={newGame.sport}
                      onChange={e => setNewGame({ ...newGame, sport: e.target.value })}
                    />
                    <input
                      className="border p-2 rounded"
                      placeholder="Location"
                      value={newGame.location}
                      onChange={e => setNewGame({ ...newGame, location: e.target.value })}
                    />
                    <input
                      className="border p-2 rounded"
                      type="datetime-local"
                      value={newGame.start_at}
                      onChange={e => setNewGame({ ...newGame, start_at: e.target.value })}
                    />
                  </div>
                  <button
                    onClick={createGame}
                    className="mt-2 bg-blue-600 text-white px-4 py-2 rounded"
                  >
                    Add Game
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white p-8 rounded shadow text-center">
              <h2 className="text-xl">Select or create an organization to get started</h2>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
