CREATE TABLE exchange (
    id INTEGER PRIMARY KEY,
    abbrev VARCHAR(32) NOT NULL,
    ex_name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    country VARCHAR(255),
    currency VARCHAR(64),
    tz_offset TIME,
    created_date DATETIME NOT NULL,
    updated_date DATETIME NOT NULL
);

CREATE TABLE data_vendor (
    id INTEGER NOT NULL,
    vendor_name VARCHAR(64) NOT NULL,
    website_url VARCHAR(255),
    support_email VARCHAR(255),
    created_date DATETIME NOT NULL,
    updated_date DATETIME NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE symbol (
    id INTEGER PRIMARY KEY NOT NULL,
    exchange_id INTEGER,
    ticker VARCHAR(32) NOT NULL,
    instrument VARCHAR(64) NOT NULL,
    sym_name VARCHAR(255),
    sector VARCHAR(255),
    currency VARCHAR(32),
    created_date DATETIME NOT NULL,
    updated_date DATETIME NOT NULL,
    FOREIGN KEY (exchange_id) REFERENCES exchange(id)
);

CREATE TABLE strategy (
    id INTEGER PRIMARY KEY NOT NULL,
    strat_name varchar(255),
    created_date DATETIME NOT NULL
);

CREATE TABLE backtests (
    id INTEGER PRIMARY KEY,
    symbol_id INTEGER,
    strategy_id INTEGER,
    bt_param TEXT,
    init_amt DECIMAL(20, 2),
    strat_ret DECIMAL(10, 4),
    sharpe DECIMAL(10, 4),
    npv DECIMAL(20, 2),
    run_date DATETIME NOT NULL,
    FOREIGN KEY (symbol_id) REFERENCES symbol(id),
    FOREIGN KEY (strategy_id) REFERENCES strategy(id)
);

CREATE TABLE stationarity (
    id INTEGER PRIMARY KEY,
    symbol_id INTEGER,
    look_back INTEGER,
    created_date DATETIME NOT NULL,
    stationary BOOLEAN,
    FOREIGN KEY (symbol_id) REFERENCES symbol(id)
);

CREATE TABLE daily_price (
    id INTEGER PRIMARY KEY,
    data_vendor_id INTEGER,
    symbol_id INTEGER,
    price_date DATETIME,
    created_date DATETIME,
    open_price DECIMAL(19, 4),
    high_price DECIMAL(19, 4),
    low_price DECIMAL(19, 4),
    close_price DECIMAL(19, 4),
    adj_close_price DECIMAL(19, 4),
    volume BIGINT,
    FOREIGN KEY (data_vendor_id) REFERENCES data_vendor(id),
    FOREIGN KEY (symbol_id) REFERENCES symbol(id)
);
