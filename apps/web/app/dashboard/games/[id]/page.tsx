'use client'

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'
import { useRouter } from 'next/navigation'

type AttendanceStatus = 'GOING' | 'MAYBE' | 'NOT_GOING'
type MemberType = 'MONTHLY' | 'GUEST'
type OrgRole = 'OWNER' | 'ADMIN' | 'MEMBER'
type TeamSide = 'A' | 'B'
type DraftStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'FINISHED'

type CaptainResolved =
  | {
      type: 'MEMBER'
      org_member_id: string
      nickname?: string | null
      member_type: MemberType
      included: boolean
      billable: boolean
      user: { id: string; email: string; full_name?: string | null; avatar_url?: string | null }
    }
  | {
      type: 'GUEST'
      game_guest_id: string
      name: string
      phone?: string | null
      billable: true
      source: 'GAME_GUEST'
    }

type Teams = {
  team_a: {
    members: Array<{
      org_member_id: string
      nickname?: string | null
      member_type: MemberType
      included: boolean
      billable: boolean
      user: { id: string; email: string; full_name?: string | null; avatar_url?: string | null }
    }>
    guests: Array<{ game_guest_id: string; name: string; phone?: string | null; billable: true; source: 'GAME_GUEST' }>
  }
  team_b: {
    members: Array<{
      org_member_id: string
      nickname?: string | null
      member_type: MemberType
      included: boolean
      billable: boolean
      user: { id: string; email: string; full_name?: string | null; avatar_url?: string | null }
    }>
    guests: Array<{ game_guest_id: string; name: string; phone?: string | null; billable: true; source: 'GAME_GUEST' }>
  }
}

type GameDetail = {
  id: string
  org_id: string
  title: string
  sport?: string | null
  location?: string | null
  start_at: string
  created_by?: {
    org_member_id: string
    user_id: string
    email: string
    full_name?: string | null
    nickname?: string | null
  } | null
  attendance_summary: { going_count: number; maybe_count: number; not_going_count: number }
  attendance_list: Array<{
    org_member_id: string
    status: AttendanceStatus
    member_type: MemberType
    included: boolean
    billable: boolean
    nickname?: string | null
    user: { id: string; email: string; full_name?: string | null; avatar_url?: string | null }
  }>
  game_guests: Array<{ id: string; name: string; phone?: string | null; billable: boolean; source: string }>
  captains: { captain_a?: CaptainResolved | null; captain_b?: CaptainResolved | null }
  teams: Teams
  draft: {
    status: DraftStatus
    current_turn_team_side?: TeamSide | null
    picks_count: number
    remaining_count: number
  }
}

type OrgGuest = { id: string; name: string; phone?: string | null }

type DraftPickItem =
  | {
      type: 'MEMBER'
      org_member_id: string
      nickname?: string | null
      member_type: MemberType
      included: boolean
      billable: boolean
      user: { id: string; email: string; full_name?: string | null; avatar_url?: string | null }
    }
  | { type: 'GUEST'; game_guest_id: string; name: string; phone?: string | null; billable: true; source: 'GAME_GUEST' }

type DraftPick = {
  id: string
  round_number: number
  pick_number: number
  team_side: TeamSide
  created_at: string
  item: DraftPickItem
}

type DraftState = {
  status: DraftStatus
  order_mode: string
  current_pick_index: number
  current_turn_team_side?: TeamSide | null
  picks: DraftPick[]
  remaining_pool: DraftPickItem[]
  teams: Teams
}

export default function GameDetailsPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [orgId, setOrgId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [game, setGame] = useState<GameDetail | null>(null)
  const [orgGuests, setOrgGuests] = useState<OrgGuest[]>([])
  const [isAdmin, setIsAdmin] = useState(false)
  const [meUserId, setMeUserId] = useState<string | null>(null)
  const [draft, setDraft] = useState<DraftState | null>(null)

  const [attendanceSet, setAttendanceSet] = useState<AttendanceStatus>('GOING')
  const [guestMode, setGuestMode] = useState<'CATALOG' | 'SNAPSHOT'>('SNAPSHOT')
  const [guestName, setGuestName] = useState('')
  const [guestPhone, setGuestPhone] = useState('')
  const [guestOrgGuestId, setGuestOrgGuestId] = useState('')

  const [captainASelect, setCaptainASelect] = useState('')
  const [captainBSelect, setCaptainBSelect] = useState('')

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('currentOrgId') : null
    setOrgId(saved)
  }, [])

  const fetchGame = async (org_id: string, game_id: string) => {
    setError(null)
    try {
      const res = await api.get(`/orgs/${org_id}/games/${game_id}`)
      setGame(res.data)
    } catch (e) {
      console.error(e)
      setGame(null)
      setError('Falha ao carregar jogo')
    } finally {
      setLoading(false)
    }
  }

  const fetchOrgGuests = async (org_id: string) => {
    try {
      const res = await api.get(`/orgs/${org_id}/guests`)
      setOrgGuests(res.data)
    } catch (e) {
      console.error(e)
      setOrgGuests([])
    }
  }

  const fetchDraft = async (org_id: string, game_id: string) => {
    try {
      const res = await api.get(`/orgs/${org_id}/games/${game_id}/draft`)
      setDraft(res.data)
    } catch (e) {
      console.error(e)
      setDraft(null)
    }
  }

  const fetchMyRole = async (org_id: string) => {
    try {
      const meRes = await api.get('/users/me')
      const myId = meRes.data?.id ?? null
      setMeUserId(myId)
      if (!myId) {
        setIsAdmin(false)
        return
      }
      const membersRes = await api.get(`/orgs/${org_id}/members`)
      const list = (membersRes.data ?? []) as Array<{ user_id: string; role: OrgRole }>
      const mine = list.find(m => m.user_id === myId) ?? null
      setIsAdmin(mine?.role === 'OWNER' || mine?.role === 'ADMIN')
    } catch (e) {
      console.error(e)
      setIsAdmin(false)
    }
  }

  useEffect(() => {
    if (!orgId) {
      setLoading(false)
      return
    }
    fetchGame(orgId, params.id)
    fetchOrgGuests(orgId)
    fetchMyRole(orgId)
    fetchDraft(orgId, params.id)
  }, [orgId, params.id])

  const title = useMemo(() => {
    if (!game) return 'Jogo'
    return game.title || 'Jogo'
  }, [game])

  const startAt = useMemo(() => {
    if (!game) return null
    const dt = new Date(game.start_at)
    return {
      date: dt.toLocaleDateString(),
      time: dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  }, [game])

  const groups = useMemo(() => {
    const list = game?.attendance_list ?? []
    return {
      GOING: list.filter(i => i.status === 'GOING'),
      MAYBE: list.filter(i => i.status === 'MAYBE'),
      NOT_GOING: list.filter(i => i.status === 'NOT_GOING'),
    }
  }, [game])

  const assignedMemberIds = useMemo(() => {
    const t = game?.teams
    if (!t) return new Set<string>()
    return new Set<string>([...t.team_a.members, ...t.team_b.members].map(m => m.org_member_id))
  }, [game])

  const assignedGuestIds = useMemo(() => {
    const t = game?.teams
    if (!t) return new Set<string>()
    return new Set<string>([...t.team_a.guests, ...t.team_b.guests].map(g => g.game_guest_id))
  }, [game])

  const availableGoingMembers = useMemo(() => {
    return groups.GOING.filter(m => !assignedMemberIds.has(m.org_member_id))
  }, [groups, assignedMemberIds])

  const availableGuests = useMemo(() => {
    const list = game?.game_guests ?? []
    return list.filter(g => !assignedGuestIds.has(g.id))
  }, [game, assignedGuestIds])

  const parseCaptainSelect = (v: string): null | { type: 'MEMBER' | 'GUEST'; id: string } => {
    if (!v) return null
    const [type, id] = v.split(':')
    if ((type !== 'MEMBER' && type !== 'GUEST') || !id) return null
    return { type: type as 'MEMBER' | 'GUEST', id }
  }

  const setMyAttendance = async () => {
    if (!orgId) return
    setError(null)
    try {
      await api.put(`/orgs/${orgId}/games/${params.id}/attendance`, { status: attendanceSet })
      await fetchGame(orgId, params.id)
      await fetchDraft(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao marcar presença')
    }
  }

  const addGuest = async () => {
    if (!orgId) return
    setError(null)
    try {
      const payload =
        guestMode === 'CATALOG'
          ? { org_guest_id: guestOrgGuestId }
          : { name: guestName, phone: guestPhone || null }
      await api.post(`/orgs/${orgId}/games/${params.id}/guests`, payload)
      setGuestName('')
      setGuestPhone('')
      await fetchGame(orgId, params.id)
      await fetchDraft(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao adicionar convidado')
    }
  }

  const saveCaptainsManual = async () => {
    if (!orgId) return
    if (!isAdmin) return
    setError(null)
    try {
      const capA = parseCaptainSelect(captainASelect)
      const capB = parseCaptainSelect(captainBSelect)
      const body = {
        mode: 'MANUAL',
        captain_a: capA ? { type: capA.type, id: capA.id } : null,
        captain_b: capB ? { type: capB.type, id: capB.id } : null,
      }
      await api.put(`/orgs/${orgId}/games/${params.id}/captains`, body)
      await fetchGame(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao definir capitães')
    }
  }

  const sortCaptains = async () => {
    if (!orgId) return
    if (!isAdmin) return
    setError(null)
    try {
      await api.put(`/orgs/${orgId}/games/${params.id}/captains`, { mode: 'RANDOM', captain_a: null, captain_b: null })
      await fetchGame(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao sortear capitães')
    }
  }

  const setTeam = async (target: { type: 'MEMBER' | 'GUEST'; id: string }, team: 'A' | 'B' | null) => {
    if (!orgId) return
    if (!isAdmin) return
    setError(null)
    try {
      await api.put(`/orgs/${orgId}/games/${params.id}/teams`, { target, team })
      await fetchGame(orgId, params.id)
      await fetchDraft(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao atualizar time')
    }
  }

  const startDraft = async () => {
    if (!orgId) return
    if (!isAdmin) return
    setError(null)
    try {
      await api.post(`/orgs/${orgId}/games/${params.id}/draft/start`)
      await fetchDraft(orgId, params.id)
      await fetchGame(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao iniciar draft')
    }
  }

  const pickDraft = async (item: DraftPickItem) => {
    if (!orgId) return
    if (!isAdmin) return
    const turn = draft?.current_turn_team_side
    if (!turn) return
    setError(null)
    try {
      const body =
        item.type === 'MEMBER'
          ? { team_side: turn, org_member_id: item.org_member_id, game_guest_id: null }
          : { team_side: turn, game_guest_id: item.game_guest_id, org_member_id: null }
      await api.post(`/orgs/${orgId}/games/${params.id}/draft/pick`, body)
      await fetchDraft(orgId, params.id)
      await fetchGame(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao fazer pick')
    }
  }

  const finishDraft = async () => {
    if (!orgId) return
    if (!isAdmin) return
    setError(null)
    try {
      await api.post(`/orgs/${orgId}/games/${params.id}/draft/finish`)
      await fetchDraft(orgId, params.id)
      await fetchGame(orgId, params.id)
    } catch (e) {
      console.error(e)
      setError('Falha ao finalizar draft')
    }
  }

  if (!orgId) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="bg-white p-6 rounded shadow">
          <div className="font-bold text-lg mb-2">Jogo</div>
          <div className="text-gray-700">Selecione uma organização no Dashboard primeiro.</div>
          <button onClick={() => router.push('/dashboard')} className="mt-4 border px-4 py-2 rounded">
            Voltar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">{title}</h1>
          {startAt && (
            <div className="text-sm text-gray-600 mt-1">
              {startAt.date} • {startAt.time}
              {game?.location ? ` • ${game.location}` : ''}
            </div>
          )}
          {game?.created_by && (
            <div className="text-xs text-gray-500 mt-1">
              Criado por: {game.created_by.nickname || game.created_by.full_name || game.created_by.email}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={() => fetchGame(orgId, params.id)} className="border px-4 py-2 rounded hover:bg-gray-50">
            Recarregar
          </button>
          <button onClick={() => router.push('/dashboard')} className="border px-4 py-2 rounded hover:bg-gray-50">
            Voltar
          </button>
        </div>
      </div>

      {error && <div className="mb-4 text-sm text-red-600">{error}</div>}

      {loading ? (
        <div className="text-gray-500">Carregando...</div>
      ) : !game ? (
        <div className="bg-white p-6 rounded shadow">Jogo não encontrado.</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white p-6 rounded shadow">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Resumo</h2>
                <div className="text-sm text-gray-600">
                  GOING: <span className="font-semibold">{game.attendance_summary.going_count}</span>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-sm">
                <span className="px-2 py-1 rounded border bg-green-50 text-green-700 border-green-200">
                  GOING: {game.attendance_summary.going_count}
                </span>
                <span className="px-2 py-1 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                  MAYBE: {game.attendance_summary.maybe_count}
                </span>
                <span className="px-2 py-1 rounded border bg-red-50 text-red-700 border-red-200">
                  NOT_GOING: {game.attendance_summary.not_going_count}
                </span>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Presença</h2>

              <div className="flex flex-wrap items-end gap-2 mb-4">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Minha presença</div>
                  <select
                    className="border p-2 rounded"
                    value={attendanceSet}
                    onChange={e => setAttendanceSet(e.target.value as AttendanceStatus)}
                  >
                    <option value="GOING">GOING</option>
                    <option value="MAYBE">MAYBE</option>
                    <option value="NOT_GOING">NOT_GOING</option>
                  </select>
                </div>
                <button onClick={setMyAttendance} className="bg-blue-600 text-white px-4 py-2 rounded">
                  Marcar presença
                </button>
              </div>

              {(['GOING', 'MAYBE', 'NOT_GOING'] as const).map(status => (
                <div key={status} className="mb-6 last:mb-0">
                  <div className="font-bold mb-2">{status}</div>
                  <div className="space-y-2">
                    {groups[status].map(item => (
                      <div key={item.org_member_id} className="border rounded p-2 flex items-center justify-between">
                        <div className="min-w-0">
                          <div className="font-semibold truncate">
                            {item.nickname || item.user.full_name || item.user.email}
                          </div>
                          <div className="text-xs text-gray-500 truncate">{item.user.email}</div>
                        </div>
                        <div className="flex flex-wrap gap-2 justify-end">
                          <span
                            className={`text-xs px-2 py-0.5 rounded border ${
                              item.member_type === 'MONTHLY'
                                ? 'bg-green-50 text-green-700 border-green-200'
                                : 'bg-yellow-50 text-yellow-800 border-yellow-200'
                            }`}
                          >
                            {item.member_type}
                          </span>
                          {item.included && (
                            <span className="text-xs px-2 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200">
                              Included
                            </span>
                          )}
                          {item.billable && (
                            <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                              Billable
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                    {groups[status].length === 0 && <div className="text-sm text-gray-500">Nenhum.</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Convidados</h2>

              <div className="space-y-2 mb-4">
                {game.game_guests.map(g => (
                  <div key={g.id} className="border rounded p-2 flex items-center justify-between">
                    <div className="min-w-0">
                      <div className="font-semibold truncate">{g.name}</div>
                      <div className="text-xs text-gray-500 truncate">{g.phone ?? '-'}</div>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-end">
                      <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                        Billable
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded border bg-gray-50 text-gray-700 border-gray-200">
                        {g.source}
                      </span>
                    </div>
                  </div>
                ))}
                {game.game_guests.length === 0 && <div className="text-sm text-gray-500">Nenhum convidado.</div>}
              </div>

              <div className="border-t pt-4">
                <div className="font-bold mb-2">Adicionar convidado</div>

                <div className="flex gap-2 mb-2">
                  <button
                    onClick={() => setGuestMode('SNAPSHOT')}
                    className={`text-sm px-3 py-1 rounded border ${
                      guestMode === 'SNAPSHOT' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'hover:bg-gray-50'
                    }`}
                  >
                    Snapshot
                  </button>
                  <button
                    onClick={() => setGuestMode('CATALOG')}
                    className={`text-sm px-3 py-1 rounded border ${
                      guestMode === 'CATALOG' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'hover:bg-gray-50'
                    }`}
                  >
                    Catálogo
                  </button>
                </div>

                {guestMode === 'CATALOG' ? (
                  <select
                    className="w-full border p-2 rounded mb-2"
                    value={guestOrgGuestId}
                    onChange={e => setGuestOrgGuestId(e.target.value)}
                  >
                    <option value="">Selecionar do catálogo</option>
                    {orgGuests.map(og => (
                      <option key={og.id} value={og.id}>
                        {og.name}{og.phone ? ` (${og.phone})` : ''}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="grid grid-cols-1 gap-2 mb-2">
                    <input
                      className="border p-2 rounded"
                      placeholder="Nome"
                      value={guestName}
                      onChange={e => setGuestName(e.target.value)}
                    />
                    <input
                      className="border p-2 rounded"
                      placeholder="Telefone (opcional)"
                      value={guestPhone}
                      onChange={e => setGuestPhone(e.target.value)}
                    />
                  </div>
                )}

                <button onClick={addGuest} className="w-full bg-blue-600 text-white px-4 py-2 rounded">
                  Adicionar
                </button>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Capitães & Times</h2>

              <div className="mb-4">
                <div className="font-bold mb-2">Capitães</div>
                <div className="text-sm text-gray-700">
                  <div>
                    <span className="text-gray-500">Capitão A:</span>{' '}
                    {game.captains?.captain_a
                      ? game.captains.captain_a.type === 'MEMBER'
                        ? game.captains.captain_a.nickname ||
                          game.captains.captain_a.user.full_name ||
                          game.captains.captain_a.user.email
                        : `${game.captains.captain_a.name}${game.captains.captain_a.phone ? ` (${game.captains.captain_a.phone})` : ''}`
                      : '-'}
                  </div>
                  <div>
                    <span className="text-gray-500">Capitão B:</span>{' '}
                    {game.captains?.captain_b
                      ? game.captains.captain_b.type === 'MEMBER'
                        ? game.captains.captain_b.nickname ||
                          game.captains.captain_b.user.full_name ||
                          game.captains.captain_b.user.email
                        : `${game.captains.captain_b.name}${game.captains.captain_b.phone ? ` (${game.captains.captain_b.phone})` : ''}`
                      : '-'}
                  </div>
                </div>

                {!isAdmin && <div className="text-xs text-gray-500 mt-2">Apenas OWNER/ADMIN pode editar.</div>}

                {isAdmin && (
                  <div className="mt-3 space-y-2">
                    <div className="flex gap-2">
                      <button onClick={sortCaptains} className="text-sm px-3 py-2 rounded bg-blue-600 text-white">
                        Sortear capitães
                      </button>
                      <button onClick={saveCaptainsManual} className="text-sm px-3 py-2 rounded border hover:bg-gray-50">
                        Salvar (manual)
                      </button>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      <select
                        className="border p-2 rounded text-sm"
                        value={captainASelect}
                        onChange={e => setCaptainASelect(e.target.value)}
                      >
                        <option value="">Capitão A (vazio)</option>
                        <option value="" disabled>
                          Members GOING
                        </option>
                        {groups.GOING.map(m => (
                          <option key={m.org_member_id} value={`MEMBER:${m.org_member_id}`}>
                            {(m.nickname || m.user.full_name || m.user.email) + ` [${m.member_type}]`}
                          </option>
                        ))}
                        <option value="" disabled>
                          Guests
                        </option>
                        {game.game_guests.map(g => (
                          <option key={g.id} value={`GUEST:${g.id}`}>
                            {g.name}{g.phone ? ` (${g.phone})` : ''}
                          </option>
                        ))}
                      </select>

                      <select
                        className="border p-2 rounded text-sm"
                        value={captainBSelect}
                        onChange={e => setCaptainBSelect(e.target.value)}
                      >
                        <option value="">Capitão B (vazio)</option>
                        <option value="" disabled>
                          Members GOING
                        </option>
                        {groups.GOING.map(m => (
                          <option key={m.org_member_id} value={`MEMBER:${m.org_member_id}`}>
                            {(m.nickname || m.user.full_name || m.user.email) + ` [${m.member_type}]`}
                          </option>
                        ))}
                        <option value="" disabled>
                          Guests
                        </option>
                        {game.game_guests.map(g => (
                          <option key={g.id} value={`GUEST:${g.id}`}>
                            {g.name}{g.phone ? ` (${g.phone})` : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
              </div>

              <div className="border-t pt-4">
                <div className="font-bold mb-3">Times A/B</div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="font-semibold mb-2">Time A</div>
                    <div className="space-y-2">
                      {game.teams.team_a.members.map(m => (
                        <div key={m.org_member_id} className="border rounded p-2 flex items-center justify-between">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">{m.nickname || m.user.full_name || m.user.email}</div>
                            <div className="text-xs text-gray-500 truncate">{m.user.email}</div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <span
                                className={`text-xs px-2 py-0.5 rounded border ${
                                  m.member_type === 'MONTHLY'
                                    ? 'bg-green-50 text-green-700 border-green-200'
                                    : 'bg-yellow-50 text-yellow-800 border-yellow-200'
                                }`}
                              >
                                {m.member_type}
                              </span>
                              {m.included && (
                                <span className="text-xs px-2 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200">
                                  Included
                                </span>
                              )}
                              {m.billable && (
                                <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                  Billable
                                </span>
                              )}
                            </div>
                          </div>
                          {isAdmin && (
                            <button
                              onClick={() => setTeam({ type: 'MEMBER', id: m.org_member_id }, null)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              Remover
                            </button>
                          )}
                        </div>
                      ))}
                      {game.teams.team_a.guests.map(g => (
                        <div key={g.game_guest_id} className="border rounded p-2 flex items-center justify-between">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">{g.name}</div>
                            <div className="text-xs text-gray-500 truncate">{g.phone ?? '-'}</div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                Billable
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded border bg-gray-50 text-gray-700 border-gray-200">
                                {g.source}
                              </span>
                            </div>
                          </div>
                          {isAdmin && (
                            <button
                              onClick={() => setTeam({ type: 'GUEST', id: g.game_guest_id }, null)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              Remover
                            </button>
                          )}
                        </div>
                      ))}
                      {game.teams.team_a.members.length === 0 && game.teams.team_a.guests.length === 0 && (
                        <div className="text-sm text-gray-500">Vazio.</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="font-semibold mb-2">Time B</div>
                    <div className="space-y-2">
                      {game.teams.team_b.members.map(m => (
                        <div key={m.org_member_id} className="border rounded p-2 flex items-center justify-between">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">{m.nickname || m.user.full_name || m.user.email}</div>
                            <div className="text-xs text-gray-500 truncate">{m.user.email}</div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <span
                                className={`text-xs px-2 py-0.5 rounded border ${
                                  m.member_type === 'MONTHLY'
                                    ? 'bg-green-50 text-green-700 border-green-200'
                                    : 'bg-yellow-50 text-yellow-800 border-yellow-200'
                                }`}
                              >
                                {m.member_type}
                              </span>
                              {m.included && (
                                <span className="text-xs px-2 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200">
                                  Included
                                </span>
                              )}
                              {m.billable && (
                                <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                  Billable
                                </span>
                              )}
                            </div>
                          </div>
                          {isAdmin && (
                            <button
                              onClick={() => setTeam({ type: 'MEMBER', id: m.org_member_id }, null)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              Remover
                            </button>
                          )}
                        </div>
                      ))}
                      {game.teams.team_b.guests.map(g => (
                        <div key={g.game_guest_id} className="border rounded p-2 flex items-center justify-between">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">{g.name}</div>
                            <div className="text-xs text-gray-500 truncate">{g.phone ?? '-'}</div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                Billable
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded border bg-gray-50 text-gray-700 border-gray-200">
                                {g.source}
                              </span>
                            </div>
                          </div>
                          {isAdmin && (
                            <button
                              onClick={() => setTeam({ type: 'GUEST', id: g.game_guest_id }, null)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              Remover
                            </button>
                          )}
                        </div>
                      ))}
                      {game.teams.team_b.members.length === 0 && game.teams.team_b.guests.length === 0 && (
                        <div className="text-sm text-gray-500">Vazio.</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 border-t pt-4">
                  <div className="font-semibold mb-2">Disponíveis</div>
                  {!isAdmin && <div className="text-xs text-gray-500">Apenas OWNER/ADMIN pode montar times.</div>}

                  <div className="space-y-2">
                    {availableGoingMembers.map(m => (
                      <div key={m.org_member_id} className="border rounded p-2 flex items-center justify-between">
                        <div className="min-w-0">
                          <div className="font-semibold truncate">{m.nickname || m.user.full_name || m.user.email}</div>
                          <div className="text-xs text-gray-500 truncate">{m.user.email}</div>
                        </div>
                        {isAdmin && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => setTeam({ type: 'MEMBER', id: m.org_member_id }, 'A')}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              → A
                            </button>
                            <button
                              onClick={() => setTeam({ type: 'MEMBER', id: m.org_member_id }, 'B')}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              → B
                            </button>
                          </div>
                        )}
                      </div>
                    ))}

                    {availableGuests.map(g => (
                      <div key={g.id} className="border rounded p-2 flex items-center justify-between">
                        <div className="min-w-0">
                          <div className="font-semibold truncate">{g.name}</div>
                          <div className="text-xs text-gray-500 truncate">{g.phone ?? '-'}</div>
                        </div>
                        {isAdmin && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => setTeam({ type: 'GUEST', id: g.id }, 'A')}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              → A
                            </button>
                            <button
                              onClick={() => setTeam({ type: 'GUEST', id: g.id }, 'B')}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                            >
                              → B
                            </button>
                          </div>
                        )}
                      </div>
                    ))}

                    {availableGoingMembers.length === 0 && availableGuests.length === 0 && (
                      <div className="text-sm text-gray-500">Ninguém disponível.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Draft v1</h2>

              <div className="text-sm text-gray-700">
                <div>
                  <span className="text-gray-500">Status:</span> <span className="font-semibold">{draft?.status ?? game.draft.status}</span>
                </div>
                <div>
                  <span className="text-gray-500">Turno:</span>{' '}
                  <span className="font-semibold">{draft?.current_turn_team_side ?? game.draft.current_turn_team_side ?? '-'}</span>
                </div>
              </div>

              {isAdmin && (draft?.status ?? game.draft.status) === 'NOT_STARTED' && (
                <button onClick={startDraft} className="mt-3 w-full bg-blue-600 text-white px-4 py-2 rounded">
                  Iniciar draft
                </button>
              )}

              {!isAdmin && <div className="text-xs text-gray-500 mt-2">Apenas OWNER/ADMIN controla o draft.</div>}

              {draft && (
                <>
                  <div className="mt-4 border-t pt-4">
                    <div className="font-bold mb-2">Disponíveis</div>
                    <div className="space-y-2">
                      {draft.remaining_pool.map(item => (
                        <div key={item.type === 'MEMBER' ? item.org_member_id : item.game_guest_id} className="border rounded p-2 flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">
                              {item.type === 'MEMBER'
                                ? item.nickname || item.user.full_name || item.user.email
                                : item.name}
                            </div>
                            <div className="text-xs text-gray-500 truncate">
                              {item.type === 'MEMBER' ? item.user.email : item.phone ?? '-'}
                            </div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              {item.type === 'MEMBER' ? (
                                <>
                                  <span
                                    className={`text-xs px-2 py-0.5 rounded border ${
                                      item.member_type === 'MONTHLY'
                                        ? 'bg-green-50 text-green-700 border-green-200'
                                        : 'bg-yellow-50 text-yellow-800 border-yellow-200'
                                    }`}
                                  >
                                    {item.member_type}
                                  </span>
                                  {item.included && (
                                    <span className="text-xs px-2 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200">
                                      Included
                                    </span>
                                  )}
                                  {item.billable && (
                                    <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                      Billable
                                    </span>
                                  )}
                                </>
                              ) : (
                                <>
                                  <span className="text-xs px-2 py-0.5 rounded border bg-yellow-50 text-yellow-800 border-yellow-200">
                                    Billable
                                  </span>
                                  <span className="text-xs px-2 py-0.5 rounded border bg-gray-50 text-gray-700 border-gray-200">
                                    {item.source}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => pickDraft(item)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                              disabled={!isAdmin || draft.status !== 'IN_PROGRESS' || draft.current_turn_team_side !== 'A'}
                            >
                              Pick p/ A
                            </button>
                            <button
                              onClick={() => pickDraft(item)}
                              className="text-sm px-3 py-2 rounded border hover:bg-gray-50"
                              disabled={!isAdmin || draft.status !== 'IN_PROGRESS' || draft.current_turn_team_side !== 'B'}
                            >
                              Pick p/ B
                            </button>
                          </div>
                        </div>
                      ))}
                      {draft.remaining_pool.length === 0 && <div className="text-sm text-gray-500">Nenhum.</div>}
                    </div>
                  </div>

                  <div className="mt-4 border-t pt-4">
                    <div className="font-bold mb-2">Picks</div>
                    <div className="space-y-2">
                      {draft.picks.map(p => (
                        <div key={p.id} className="border rounded p-2 flex items-center justify-between">
                          <div className="min-w-0">
                            <div className="font-semibold truncate">
                              #{p.pick_number} • Team {p.team_side}:{' '}
                              {p.item.type === 'MEMBER'
                                ? p.item.nickname || p.item.user.full_name || p.item.user.email
                                : p.item.name}
                            </div>
                          </div>
                        </div>
                      ))}
                      {draft.picks.length === 0 && <div className="text-sm text-gray-500">Nenhum pick ainda.</div>}
                    </div>
                  </div>

                  {isAdmin && draft.status === 'IN_PROGRESS' && (
                    <button onClick={finishDraft} className="mt-4 w-full border px-4 py-2 rounded hover:bg-gray-50">
                      Finalizar draft
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

