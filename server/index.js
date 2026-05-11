require('dotenv').config()
const express = require('express')
const cors = require('cors')
const path = require('path')

const { configure: configurePush } = require('./pushService')
const { startTimers } = require('./timerService')

configurePush()

const app = express()
app.use(cors())
app.use(express.json())

app.use('/api/player', require('./routes/playerRoutes'))
app.use('/api/staff', require('./routes/staffRoutes'))
app.use('/api/push', require('./routes/pushRoutes'))

if (process.env.NODE_ENV === 'production') {
  const dist = path.join(__dirname, '..', 'dist')
  app.use(express.static(dist))
  app.get('*', (req, res) => res.sendFile(path.join(dist, 'index.html')))
}

const PORT = process.env.PORT || 3001
app.listen(PORT, () => console.log(`Commander Picker running on :${PORT}`))

startTimers()
