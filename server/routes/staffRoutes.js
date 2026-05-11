const express = require('express')
const router = express.Router()
const multer = require('multer')
const { parse } = require('csv-parse/sync')
const db = require('../db')
const { sendPushToPhone } = require('../pushService')
const { broadcastUpdate, addClient } = require('../sseService')

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 2 * 1024 * 1024 } })

function requirePin(req, res, next) {
  const pin = req.headers['x-staff-pin'] || req.query.pin
  if (pin !== (process.env.STAFF_PIN || '1234')) {
    return res.status(401).json({ error: 'PIN incorrecto' })
  }
  next()
}

router.use(requirePin)

router.get('/events', (req, res) => {
  const remove = addClient(res)
  req.on('close', remove)
})

router.get('/session', (req, res) => {
  const session = db.prepare('SELECT * FROM sessions WHERE active=1 ORDER BY created_at DESC LIMIT 1').get()
  if (!session) return res.json({ session: null, players: [] })
  const players = db.prepare('SELECT * FROM players WHERE session_id=? ORDER BY position').all(session.id)
  res.json({ session, players })
})

router.post('/session', (req, res) => {
  const { name } = req.body
  if (!name) return res.status(400).json({ error: 'Name required' })
  db.prepare('UPDATE sessions SET active=0').run()
  const id = Date.now().toString(36)
  db.prepare('INSERT INTO sessions (id, name) VALUES (?, ?)').run(id, name)
  broadcastUpdate('session-created', { sessionId: id, name })
  res.json({ id, name })
})

router.post('/session/load', upload.single('csv'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' })
  const session = db.prepare('SELECT * FROM sessions WHERE active=1 ORDER BY created_at DESC LIMIT 1').get()
  if (!session) return res.status(404).json({ error: 'No hay sesión activa' })

  try {
    const text = req.file.buffer.toString('utf-8')
    let records
    for (const delimiter of [',', ';', '\t']) {
      try {
        records = parse(text, { columns: true, skip_empty_lines: true, trim: true, delimiter })
        if (records.length > 0) break
      } catch (_) { continue }
    }
    if (!records || records.length === 0) return res.status(400).json({ error: 'CSV vacío o inválido' })

    db.prepare('DELETE FROM players WHERE session_id=?').run(session.id)

    const insert = db.prepare('INSERT INTO players (session_id, position, name, phone) VALUES (?, ?, ?, ?)')
    const insertAll = db.transaction((rows) => {
      let count = 0
      for (const row of rows) {
        const keys = Object.keys(row).map(k => k.toLowerCase().trim())
        const get = (candidates) => {
          for (const c of candidates) {
            const k = Object.keys(row).find(k => k.toLowerCase().trim() === c)
            if (k && row[k]) return row[k].toString().trim()
          }
          return null
        }
        const position = get(['posición', 'posicion', 'position', 'pos', '#'])
        const name = get(['nombre', 'name', 'jugador', 'player'])
        const phone = get(['teléfono', 'telefono', 'phone', 'móvil', 'movil', 'tel'])
        if (position && name && phone) {
          insert.run(session.id, parseInt(position), name, phone)
          count++
        }
      }
      return count
    })
    const count = insertAll(records)
    broadcastUpdate('session-loaded', { count })
    res.json({ success: true, count })
  } catch (err) {
    res.status(400).json({ error: 'Error al parsear CSV: ' + err.message })
  }
})

router.post('/notify/:id', async (req, res) => {
  const player = db.prepare('SELECT * FROM players WHERE id=?').get(req.params.id)
  if (!player) return res.status(404).json({ error: 'Player not found' })

  db.prepare(`
    UPDATE players SET status='notified', notified_at=CURRENT_TIMESTAMP,
    re_notified_at=NULL, warned_at=NULL WHERE id=?
  `).run(player.id)

  const results = await sendPushToPhone(player.phone, {
    title: '🏆 Te toca elegir premio',
    body: `${player.name}, es tu turno. Acércate a la zona de picking.`
  })
  const allFailed = results.length > 0 && results.every(r => !r.success)
  if (allFailed) db.prepare('UPDATE players SET phone_error=1 WHERE id=?').run(player.id)

  broadcastUpdate('player-update', { playerId: player.id, status: 'notified' })
  res.json({ success: true, pushResults: results })
})

router.post('/renotify/:id', async (req, res) => {
  const player = db.prepare('SELECT * FROM players WHERE id=?').get(req.params.id)
  if (!player) return res.status(404).json({ error: 'Player not found' })
  await sendPushToPhone(player.phone, {
    title: '⚠️ Recuerda: Te toca elegir premio',
    body: `${player.name}, ¡aún te estamos esperando!`
  })
  res.json({ success: true })
})

router.post('/mark-present/:id', (req, res) => {
  db.prepare(`UPDATE players SET status='present', present_at=CURRENT_TIMESTAMP WHERE id=?`).run(req.params.id)
  broadcastUpdate('player-update', { playerId: req.params.id, status: 'present' })
  res.json({ success: true })
})

router.post('/mark-picked/:id', (req, res) => {
  db.prepare(`UPDATE players SET status='picked', picked_at=CURRENT_TIMESTAMP WHERE id=?`).run(req.params.id)
  broadcastUpdate('player-update', { playerId: req.params.id, status: 'picked' })
  res.json({ success: true })
})

router.post('/skip/:id', (req, res) => {
  db.prepare(`UPDATE players SET status='skipped', skipped_at=CURRENT_TIMESTAMP WHERE id=?`).run(req.params.id)
  broadcastUpdate('player-update', { playerId: req.params.id, status: 'skipped' })
  res.json({ success: true })
})

router.post('/update-phone/:id', (req, res) => {
  const { phone } = req.body
  if (!phone) return res.status(400).json({ error: 'Phone required' })
  db.prepare('UPDATE players SET phone=?, phone_error=0 WHERE id=?').run(phone.trim(), req.params.id)
  broadcastUpdate('player-update', { playerId: req.params.id, phone })
  res.json({ success: true })
})

module.exports = router
