const db = require('./db')
const { sendPushToPhone } = require('./pushService')
const { broadcastUpdate } = require('./sseService')

const RENOTIFY_MS = 20 * 1000
const WARN_MS = 60 * 1000

function startTimers() {
  setInterval(async () => {
    const now = Math.floor(Date.now() / 1000)

    const toRenotify = db.prepare(`
      SELECT * FROM players
      WHERE status = 'notified'
        AND notified_at IS NOT NULL
        AND (${now} - strftime('%s', notified_at)) >= ${RENOTIFY_MS / 1000}
    `).all()

    for (const p of toRenotify) {
      db.prepare(`UPDATE players SET status='re-notified', re_notified_at=CURRENT_TIMESTAMP WHERE id=?`).run(p.id)
      await sendPushToPhone(p.phone, {
        title: '⚠️ Recuerda: Te toca elegir premio',
        body: `${p.name}, seguimos esperándote. Acércate ya a la zona de picking.`
      })
      broadcastUpdate('player-update', { playerId: p.id, status: 're-notified' })
    }

    const toWarn = db.prepare(`
      SELECT * FROM players
      WHERE status = 're-notified'
        AND notified_at IS NOT NULL
        AND (${now} - strftime('%s', notified_at)) >= ${WARN_MS / 1000}
    `).all()

    for (const p of toWarn) {
      db.prepare(`UPDATE players SET status='warned', warned_at=CURRENT_TIMESTAMP WHERE id=?`).run(p.id)
      await sendPushToPhone(p.phone, {
        title: '🚨 Último aviso',
        body: `${p.name}, si no apareces en breve podrías perder tu turno.`
      })
      broadcastUpdate('player-update', { playerId: p.id, status: 'warned' })
    }
  }, 5000)
}

module.exports = { startTimers }
