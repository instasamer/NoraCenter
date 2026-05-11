const Database = require('better-sqlite3')
const path = require('path')
const fs = require('fs')

const dataDir = path.join(__dirname, '..', 'data')
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true })

const db = new Database(path.join(dataDir, 'picker.db'))

db.pragma('journal_mode = WAL')

db.exec(`
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1
  );

  CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    notified_at DATETIME,
    re_notified_at DATETIME,
    warned_at DATETIME,
    on_way_at DATETIME,
    present_at DATETIME,
    picked_at DATETIME,
    skipped_at DATETIME,
    phone_error INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
  );

  CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL UNIQUE,
    subscription TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`)

module.exports = db
