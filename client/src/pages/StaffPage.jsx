import React, { useState, useEffect, useRef, useCallback } from 'react'

const STATUS_LABELS = {
  pending: 'Pendiente',
  notified: 'Notificado',
  're-notified': 'Renotificado',
  warned: 'Aviso salto',
  'on-way': 'En camino',
  present: 'Presente',
  picked: 'Premio elegido',
  skipped: 'Saltado',
  error: 'Error tel.'
}

const DONE_STATUSES = ['picked', 'skipped']
const ACTIVE_STATUSES = ['notified', 're-notified', 'warned', 'on-way', 'present']

const RENOTIFY_S = 20
const WARN_S = 60

function useApi(pin) {
  const headers = { 'Content-Type': 'application/json', 'x-staff-pin': pin }
  const call = useCallback(async (method, path, body) => {
    const res = await fetch('/api/staff' + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
    return res.json()
  }, [pin])
  return call
}

function ElapsedTimer({ since }) {
  const [secs, setSecs] = useState(0)
  useEffect(() => {
    if (!since) return
    const start = new Date(since).getTime()
    const tick = () => setSecs(Math.floor((Date.now() - start) / 1000))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [since])

  const pct = Math.min((secs / WARN_S) * 100, 100)
  const color = secs >= WARN_S ? 'var(--danger)' : secs >= RENOTIFY_S ? 'var(--warning)' : 'var(--info)'

  return (
    <div className="timer-bar-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
        <span>Tiempo desde notificación</span>
        <span style={{ color, fontWeight: 700 }}>{secs}s</span>
      </div>
      <div className="timer-bar-track">
        <div className="timer-bar-fill" style={{ width: pct + '%', background: color }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
        <span>0s</span>
        <span>Renotif. {RENOTIFY_S}s</span>
        <span>Aviso {WARN_S}s</span>
      </div>
    </div>
  )
}

function PlayerRow({ player, onAction, isCurrentActive }) {
  const [editPhone, setEditPhone] = useState(false)
  const [newPhone, setNewPhone] = useState(player.phone)
  const isDone = DONE_STATUSES.includes(player.status)

  return (
    <div className={`player-row ${isCurrentActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
      <div className="player-row-pos">#{player.position}</div>
      <div className="player-row-info">
        <div className="player-row-name">{player.name}</div>
        {editPhone ? (
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            <input value={newPhone} onChange={e => setNewPhone(e.target.value)}
              style={{ fontSize: 13, padding: '4px 8px' }} />
            <button className="btn-success" style={{ padding: '4px 10px', fontSize: 12 }}
              onClick={() => { onAction('update-phone', { phone: newPhone }); setEditPhone(false) }}>
              ✓
            </button>
            <button className="btn-ghost" style={{ padding: '4px 10px', fontSize: 12 }}
              onClick={() => setEditPhone(false)}>
              ✕
            </button>
          </div>
        ) : (
          <div className="player-row-phone" onClick={() => setEditPhone(true)} style={{ cursor: 'pointer' }}>
            {player.phone} {player.phone_error ? '⚠️' : ''}
          </div>
        )}
      </div>
      <span className={`badge badge-${player.status}`}>{STATUS_LABELS[player.status] || player.status}</span>
      <div className="player-row-actions">
        {player.status === 'pending' && (
          <button className="btn-primary" onClick={() => onAction('notify')}>Notificar</button>
        )}
        {ACTIVE_STATUSES.includes(player.status) && player.status !== 'present' && (
          <>
            <button className="btn-info" onClick={() => onAction('renotify')}>↺</button>
            <button className="btn-success" onClick={() => onAction('mark-present')}>Presente</button>
          </>
        )}
        {player.status === 'present' && (
          <button className="btn-success" onClick={() => onAction('mark-picked')}>Premio ✓</button>
        )}
        {!isDone && (
          <button className="btn-danger" onClick={() => onAction('skip')}>Saltar</button>
        )}
      </div>
    </div>
  )
}

function CurrentPlayerCard({ player, onAction }) {
  if (!player) return null
  const isWarn = ['warned', 're-notified'].includes(player.status)

  return (
    <div className={`card current-player-card ${isWarn ? 'warn' : ''}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p className="current-player-pos">Posición #{player.position}</p>
          <p className="current-player-name">{player.name}</p>
          <p className="current-player-phone">{player.phone} {player.phone_error ? '⚠️ Error tel.' : ''}</p>
          <span className={`badge badge-${player.status}`} style={{ fontSize: 14, padding: '4px 14px' }}>
            {STATUS_LABELS[player.status] || player.status}
          </span>
        </div>
        <button className="btn-danger" style={{ fontSize: 16, padding: '10px 20px' }} onClick={() => onAction('skip')}>
          ⏭ Saltar
        </button>
      </div>

      {player.notified_at && ACTIVE_STATUSES.includes(player.status) && (
        <div style={{ marginTop: 12 }}>
          <ElapsedTimer since={player.notified_at} />
        </div>
      )}

      <div className="controls">
        {player.status === 'pending' && (
          <button className="btn-primary" onClick={() => onAction('notify')}>🔔 Notificar</button>
        )}
        {['notified', 're-notified', 'warned'].includes(player.status) && (
          <>
            <button className="btn-info" onClick={() => onAction('renotify')}>↺ Renotificar</button>
            <button className="btn-success" onClick={() => onAction('mark-present')}>✓ Presente</button>
          </>
        )}
        {player.status === 'on-way' && (
          <button className="btn-success" onClick={() => onAction('mark-present')}>✓ Marcar presente</button>
        )}
        {player.status === 'present' && (
          <button className="btn-success" style={{ fontSize: 16, padding: '12px 24px' }} onClick={() => onAction('mark-picked')}>
            🎁 Premio elegido
          </button>
        )}
      </div>

      {isWarn && (
        <div className="alert alert-warn" style={{ marginTop: 12, marginLeft: 0, marginRight: 0 }}>
          ⚠️ Protocolo de espera cumplido. Puedes saltar al jugador.
        </div>
      )}
    </div>
  )
}

export default function StaffPage() {
  const [pin, setPin] = useState(() => sessionStorage.getItem('staff_pin') || '')
  const [authed, setAuthed] = useState(false)
  const [pinInput, setPinInput] = useState('')
  const [pinError, setPinError] = useState('')

  const [session, setSession] = useState(null)
  const [players, setPlayers] = useState([])
  const [newSessionName, setNewSessionName] = useState('')
  const [showNewSession, setShowNewSession] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef()
  const eventSourceRef = useRef()

  const api = useApi(pin)

  const loadSession = useCallback(async () => {
    try {
      const data = await api('GET', '/session')
      setSession(data.session)
      setPlayers(data.players || [])
    } catch (_) {}
  }, [api])

  useEffect(() => {
    if (!authed) return
    loadSession()

    const es = new EventSource(`/api/staff/events?pin=${encodeURIComponent(pin)}`)
    eventSourceRef.current = es
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (['player-update', 'session-loaded', 'session-created'].includes(msg.type)) {
        loadSession()
      }
    }
    return () => es.close()
  }, [authed, pin, loadSession])

  async function handleLogin(e) {
    e.preventDefault()
    const res = await api('GET', '/session').catch(() => null)
    if (res && !res.error) {
      sessionStorage.setItem('staff_pin', pinInput)
      setPin(pinInput)
      setAuthed(true)
    } else {
      setPinError('PIN incorrecto')
    }
  }

  // Verify saved PIN on mount
  useEffect(() => {
    const saved = sessionStorage.getItem('staff_pin')
    if (saved) {
      fetch('/api/staff/session', { headers: { 'x-staff-pin': saved } })
        .then(r => { if (r.ok) { setPin(saved); setAuthed(true) } })
        .catch(() => {})
    }
  }, [])

  async function handleAction(player, action, extra) {
    if (action === 'notify') await api('POST', `/notify/${player.id}`)
    else if (action === 'renotify') await api('POST', `/renotify/${player.id}`)
    else if (action === 'mark-present') await api('POST', `/mark-present/${player.id}`)
    else if (action === 'mark-picked') await api('POST', `/mark-picked/${player.id}`)
    else if (action === 'skip') await api('POST', `/skip/${player.id}`)
    else if (action === 'update-phone') await api('POST', `/update-phone/${player.id}`, extra)
    loadSession()
  }

  async function handleNewSession(e) {
    e.preventDefault()
    if (!newSessionName.trim()) return
    await api('POST', '/session', { name: newSessionName.trim() })
    setNewSessionName('')
    setShowNewSession(false)
    loadSession()
  }

  async function handleCsvUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const fd = new FormData()
    fd.append('csv', file)
    await fetch('/api/staff/session/load', {
      method: 'POST', headers: { 'x-staff-pin': pin }, body: fd
    })
    setUploading(false)
    loadSession()
    e.target.value = ''
  }

  if (!authed) {
    return (
      <div className="page page-center">
        <div className="card login-card">
          <h2>🛡 Panel del Staff</h2>
          <form onSubmit={handleLogin}>
            <input type="password" placeholder="PIN del staff" value={pinInput}
              onChange={e => setPinInput(e.target.value)} style={{ textAlign: 'center', fontSize: 24, letterSpacing: 6 }} autoFocus />
            {pinError && <p style={{ color: 'var(--danger)', marginTop: 10, textAlign: 'center' }}>{pinError}</p>}
            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: 16, padding: 14, fontSize: 16 }}>
              Entrar
            </button>
          </form>
        </div>
      </div>
    )
  }

  const activePlayer = players.find(p => ACTIVE_STATUSES.includes(p.status))
  const pendingPlayers = players.filter(p => p.status === 'pending')
  const nextPending = pendingPlayers[0]

  return (
    <div className="staff-layout">
      <div className="staff-header">
        <h1>🏆 {session ? session.name : 'Sin sesión'}</h1>
        <button className="btn-ghost" style={{ fontSize: 13 }} onClick={() => setShowNewSession(v => !v)}>
          + Nueva sesión
        </button>
        <button className="btn-ghost" style={{ fontSize: 13 }} onClick={() => fileRef.current.click()} disabled={!session}>
          {uploading ? 'Cargando...' : '📂 Cargar CSV'}
        </button>
        <input ref={fileRef} type="file" accept=".csv,.txt" style={{ display: 'none' }} onChange={handleCsvUpload} />
      </div>

      {showNewSession && (
        <form onSubmit={handleNewSession} style={{ padding: '12px 16px', background: 'var(--surface2)', display: 'flex', gap: 8 }}>
          <input placeholder="Nombre del torneo (ej. Commander FNM 11/05)" value={newSessionName}
            onChange={e => setNewSessionName(e.target.value)} autoFocus />
          <button type="submit" className="btn-primary">Crear</button>
          <button type="button" className="btn-ghost" onClick={() => setShowNewSession(false)}>Cancelar</button>
        </form>
      )}

      <div className="staff-body">
        {!session ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
            <p>Crea una sesión nueva y carga el CSV de El Chucko para empezar.</p>
          </div>
        ) : (
          <>
            {activePlayer ? (
              <CurrentPlayerCard player={activePlayer} onAction={(a, extra) => handleAction(activePlayer, a, extra)} />
            ) : nextPending ? (
              <div className="card" style={{ margin: 16, border: '1px dashed var(--border)', textAlign: 'center' }}>
                <p className="text-muted">Siguiente jugador listo para notificar</p>
                <p style={{ fontSize: 22, fontWeight: 700, margin: '8px 0' }}>#{nextPending.position} — {nextPending.name}</p>
                <button className="btn-primary" style={{ padding: '12px 32px', fontSize: 16 }}
                  onClick={() => handleAction(nextPending, 'notify')}>
                  🔔 Notificar
                </button>
              </div>
            ) : players.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>Carga el CSV con la lista de picking para empezar.</p>
              </div>
            ) : (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--success)' }}>
                <p style={{ fontSize: 24 }}>🎉 ¡Picking completado!</p>
                <p className="text-muted mt-8">Todos los jugadores han elegido su premio.</p>
              </div>
            )}

            <div className="player-list">
              {players.map(p => (
                <PlayerRow
                  key={p.id}
                  player={p}
                  isCurrentActive={ACTIVE_STATUSES.includes(p.status)}
                  onAction={(action, extra) => handleAction(p, action, extra)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
