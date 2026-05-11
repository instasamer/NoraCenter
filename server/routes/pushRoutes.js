const express = require('express')
const router = express.Router()
const db = require('../db')

router.get('/vapid-public-key', (req, res) => {
  res.json({ key: process.env.VAPID_PUBLIC_KEY || null })
})

router.post('/subscribe', (req, res) => {
  const { phone, subscription } = req.body
  if (!phone || !subscription) return res.status(400).json({ error: 'Phone and subscription required' })
  db.prepare(`
    INSERT INTO push_subscriptions (phone, subscription)
    VALUES (?, ?)
    ON CONFLICT(phone) DO UPDATE SET subscription=excluded.subscription, created_at=CURRENT_TIMESTAMP
  `).run(phone, JSON.stringify(subscription))
  res.json({ success: true })
})

module.exports = router
