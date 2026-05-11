const express = require('express')
const router = express.Router()
const db = require('../db')
const { broadcastUpdate } = require('../sseService')

function getActiveSession() {
  return db.prepare('SELECT * FROM sessions WHERE active=1 ORDER BY created_at DESC LIMIT 1').get()
}

router.post('/register', (req, res) => {
  const { phone } = req.body
  if (!phone) return res.status(400).json({ error: 'Phone required' })
  const session = getActiveSession()
  if (!session) return res.status(404).json({ error: 'No hay sesión activa' })
  const player = db.prepare('SELECT * FROM players WHERE session_id=? AND phone=?').get(session.id, phone.trim())
  if (!player) return res.status(404).json({ error: 'Número no encontrado en la lista del torneo' })
  res.json({ player, session })
})

router.get('/status', (req, res) => {
  const { phone } = req.query
  if (!phone) return res.status(400).json({ error: 'Phone required' })
  const session = getActiveSession()
  if (!session) return res.status(404).json({ error: 'No hay sesión activa' })
  const player = db.prepare('SELECT * FROM players WHERE session_id=? AND phone=?').get(session.id, phone.trim())
  if (!player) return res.status(404).json({ error: 'Not found' })
  res.json({ player, session })
})

router.post('/on-way', (req, res) => {
  const { phone } = req.body
  if (!phone) return res.status(400).json({ error: 'Phone required' })
  const session = getActiveSession()
  if (!session) return res.status(404).json({ error: 'No hay sesión activa' })
  const player = db.prepare('SELECT * FROM players WHERE session_id=? AND phone=?').get(session.id, phone.trim())
  if (!player) return res.status(404).json({ error: 'Not found' })
  if (!['notified', 're-notified', 'warned'].includes(player.status)) {
    return res.status(400).json({ error: 'No estás en estado notificado' })
  }
  db.prepare(`UPDATE players SET status='on-way', on_way_at=CURRENT_TIMESTAMP WHERE id=?`).run(player.id)
  broadcastUpdate('player-update', { playerId: player.id, status: 'on-way', playerName: player.name })
  res.json({ success: true })
})

module.exports = router
