CREATE TABLE IF NOT EXISTS holdings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  name TEXT,
  market TEXT DEFAULT 'A',
  quantity REAL NOT NULL DEFAULT 0,
  cost_price REAL NOT NULL,
  strategy_horizon TEXT DEFAULT 'swing',
  initial_thesis TEXT,
  stop_loss REAL,
  take_profit REAL,
  max_loss_pct REAL,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings(symbol);

CREATE TABLE IF NOT EXISTS watchlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  name TEXT,
  market TEXT DEFAULT 'A',
  thesis TEXT,
  buy_zone_low REAL,
  buy_zone_high REAL,
  trigger_condition TEXT,
  invalidation_condition TEXT,
  priority INTEGER DEFAULT 3,
  status TEXT DEFAULT 'watching',
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol);
CREATE INDEX IF NOT EXISTS idx_watchlist_status ON watchlist(status);

CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  source TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_symbol ON market_snapshots(symbol);

CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  action TEXT NOT NULL,
  strength REAL,
  price REAL,
  reason_json TEXT,
  source_snapshot_id INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY (source_snapshot_id) REFERENCES market_snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at);
