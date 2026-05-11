import React, { useState, useEffect, useCallback, useRef } from 'react'

const STATUS_LABELS = {
  pending: 'En espera',
  notified: '🏆 ¡Es tu turno!',
  're-notified': '⚠️ Te estamos esperando',
  warned: '🚨 Último aviso',
  'on-way': '🚶 En camino',
  present: '✅ Presente',
  picked: '🎁 Premio elegido',
  skipped: '⏭ Saltado',
  error: '⚠️ Error de notificación'
}

const ACTIVE_STATUSES = ['notified', 're-notified', 'warned']

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)))
}

async function trySubscribePush(phone) {
  if (!('Notification' in window) || !('serviceWorker' in navigator)) return
  try {
    const permission = await Notification.requestPermission()
    if (permission !== 'granted') return
    const reg = await navigator.serviceWorker.ready
    const res = await fetch('/api/push/vapid-public-key')
    const { key } = await res.json()
    if (!key) return
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(key)
    })
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, subscription: sub.toJSON() })
    })
  } catch (_) {}
}

export default function PlayerPage() {
  const [phone, setPhone] = useState(() => localStorage.getItem('pp_phone') || '')
  const [registered, setRegistered] = useState(false)
  const [player, setPlayer] = useState(null)
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [onWaySent, setOnWaySent] = useState(false)
  const pollRef = useRef(null)

  const fetchStatus = useCallback(async (ph) => {
    try {
      const res = await fetch(`/api/player/status?phone=${encodeURIComponent(ph)}`)
      if (!res.ok) return
      const data = await res.json()
      setPlayer(data.player)
      setSession(data.session)
    } catch (_) {}
  }, [])

  useEffect(() => {
    if (!registered) return
    fetchStatus(phone)
    pollRef.current = setInterval(() => fetchStatus(phone), 3000)
    return () => clearInterval(pollRef.current)
  }, [registered, phone, fetchStatus])

  async function handleRegister(e) {
    e.preventDefault()
    if (!phone.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/player/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: phone.trim() })
      })
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Error'); setLoading(false); return }
      localStorage.setItem('pp_phone', phone.trim())
      setPlayer(data.player)
      setSession(data.session)
      setRegistered(true)
      trySubscribePush(phone.trim())
    } catch (_) {
      setError('Error de conexión')
    }
    setLoading(false)
  }

  async function handleOnWay() {
    setOnWaySent(true)
    await fetch('/api/player/on-way', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: phone.trim() })
    })
  }

  function handleLogout() {
    localStorage.removeItem('pp_phone')
    setPhone('')
    setRegistered(false)
    setPlayer(null)
  }

  if (!registered) {
    return (
      <div className="page page-center">
        <div className="player-page">
          <div className="card">
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{ fontSize: 48 }}>🏆</div>
              <h1 style={{ fontSize: 24, marginTop: 8 }}>Commander Prize Picker</h1>
              <p className="text-muted mt-8">Introduce tu número de móvil para entrar en la lista de premios</p>
            </div>
            <form onSubmit={handleRegister}>
              <input
                type="tel"
                placeholder="Número de móvil (ej. 612345678)"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                autoFocus
                style={{ fontSize: 20, textAlign: 'center', letterSpacing: 2 }}
              />
              {error && <p style={{ color: 'var(--danger)', marginTop: 10, fontSize: 14, textAlign: 'center' }}>{error}</p>}
              <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: 16, padding: 14, fontSize: 16 }} disabled={loading}>
                {loading ? 'Verificando...' : 'Entrar'}
              </button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  if (!player) return (
    <div className="page page-center">
      <p className="text-muted">Cargando...</p>
    </div>
  )

  const isActive = ACTIVE_STATUSES.includes(player.status)
  const isWarn   = player.status === 'warned'

  return (
    <div className="page page-center">
      <div className="player-page">
        <div className={`card ${isWarn ? 'warn-pulse' : isActive ? 'pulse' : ''}`}
          style={{ border: isWarn ? '2px solid var(--danger)' : isActive ? '2px solid var(--accent)' : '1px solid var(--border)' }}>
          <div style={{ textAlign: 'center' }}>
            <p className="text-muted" style={{ fontSize: 13 }}>
              {session?.name} · Posición #{player.position}
            </p>
            <p style={{ fontSize: 28, fontWeight: 800, margin: '12px 0 8px' }}>{player.name}</p>
            <span className={`badge badge-${player.status}`}>{STATUS_LABELS[player.status] || player.status}</span>

            {isActive && (
              <div style={{ marginTop: 24 }}>
                <p style={{ fontSize: 16, marginBottom: 16 }}>¡Es tu momento! Acércate a la zona de premios.</p>
                {!onWaySent && player.status !== 'on-way' ? (
                  <button className="btn-info" style={{ width: '100%', padding: 14, fontSize: 16 }} onClick={handleOnWay}>
                    🚶 Estoy en camino
                  </button>
                ) : (
                  <p style={{ color: 'var(--cyan)', fontWeight: 600 }}>✓ El staff ya sabe que vas</p>
                )}
              </div>
            )}

            {player.status === 'on-way' && (
              <div style={{ marginTop: 16 }}>
                <p style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 18 }}>🚶 ¡Perfecto! Ahora ve a la zona de premios.</p>
              </div>
            )}

            {player.status === 'pending' && (
              <p className="text-muted" style={{ marginTop: 16 }}>
                Mantén esta página abierta. Recibirás un aviso cuando sea tu turno.
              </p>
            )}

            {player.status === 'picked' && (
              <p style={{ color: 'var(--success)', fontWeight: 600, marginTop: 16, fontSize: 18 }}>
                🎁 ¡Has elegido tu premio! ¡Enhorabuena!
              </p>
            )}

            {player.status === 'skipped' && (
              <p style={{ color: 'var(--text-muted)', marginTop: 16 }}>
                Tu turno fue saltado. Habla con el staff si crees que fue un error.
              </p>
            )}
          </div>
        </div>

        <button className="btn-ghost" style={{ width: '100%', marginTop: 12, fontSize: 13 }} onClick={handleLogout}>
          Cambiar número
        </button>
      </div>
    </div>
  )
}
