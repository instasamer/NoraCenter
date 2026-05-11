const clients = new Set()

function addClient(res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  })
  res.write('data: {"type":"connected"}\n\n')
  clients.add(res)
  return () => clients.delete(res)
}

function broadcastUpdate(type, data) {
  const msg = `data: ${JSON.stringify({ type, ...data })}\n\n`
  for (const client of clients) {
    try { client.write(msg) } catch (_) { clients.delete(client) }
  }
}

module.exports = { addClient, broadcastUpdate }
