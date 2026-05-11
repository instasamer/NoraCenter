const webpush = require('web-push')
const db = require('./db')

let vapidConfigured = false

function configure() {
  const pub = process.env.VAPID_PUBLIC_KEY
  const priv = process.env.VAPID_PRIVATE_KEY
  const email = process.env.VAPID_EMAIL || 'admin@example.com'
  if (pub && priv) {
    webpush.setVapidDetails('mailto:' + email, pub, priv)
    vapidConfigured = true
  } else {
    console.warn('[push] VAPID keys not set — push notifications disabled')
  }
}

async function sendPushToPhone(phone, payload) {
  if (!vapidConfigured) return []
  const row = db.prepare('SELECT subscription FROM push_subscriptions WHERE phone = ?').get(phone)
  if (!row) return []
  try {
    await webpush.sendNotification(JSON.parse(row.subscription), JSON.stringify(payload))
    return [{ success: true }]
  } catch (err) {
    if (err.statusCode === 410) {
      db.prepare('DELETE FROM push_subscriptions WHERE phone = ?').run(phone)
    }
    return [{ success: false, error: err.message }]
  }
}

module.exports = { configure, sendPushToPhone }
