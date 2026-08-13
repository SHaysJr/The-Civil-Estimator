import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'estimator.db'


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


SCHEMA = '''
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id=1),
    company_name TEXT NOT NULL DEFAULT '',
    company_address TEXT NOT NULL DEFAULT '',
    company_phone TEXT NOT NULL DEFAULT '',
    default_tax_rate REAL NOT NULL DEFAULT 0.10,
    default_overhead_rate REAL NOT NULL DEFAULT 0.10,
    default_profit_rate REAL NOT NULL DEFAULT 0.20,
    default_target_profit_per_day_min REAL,
    default_target_profit_per_day_max REAL,
    fuel_surcharge_per_ton REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    customer TEXT NOT NULL DEFAULT '',
    address_line TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    zip_code TEXT NOT NULL DEFAULT '',
    estimator TEXT NOT NULL DEFAULT '',
    bid_date TEXT NOT NULL DEFAULT '',
    date_due TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    is_mpc INTEGER NOT NULL DEFAULT 0,
    tax_rate REAL NOT NULL DEFAULT 0.10,
    overhead_rate REAL NOT NULL DEFAULT 0.10,
    profit_rate REAL NOT NULL DEFAULT 0.20,
    bedding_jurisdiction TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scope_name TEXT NOT NULL,
    profit_rate REAL,
    target_profit_per_day_min REAL,
    target_profit_per_day_max REAL,
    override_profit_target INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS labor_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    reg_hourly_rate REAL NOT NULL DEFAULT 0,
    ot_hourly_rate REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS equipment_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    day_rate REAL NOT NULL DEFAULT 0,
    week_rate REAL NOT NULL DEFAULT 0,
    month_rate REAL NOT NULL DEFAULT 0,
    fuel_capacity_gal REAL NOT NULL DEFAULT 0,
    fuel_price_per_gal REAL NOT NULL DEFAULT 0,
    category TEXT
);

CREATE TABLE IF NOT EXISTS material_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    unit_cost REAL NOT NULL DEFAULT 0,
    production_rate REAL,
    companion_material_id INTEGER,
    companion_ratio REAL,
    is_mobilization INTEGER NOT NULL DEFAULT 0,
    pipe_type TEXT,
    is_depth_priced INTEGER NOT NULL DEFAULT 0,
    production_rate_0_6 REAL,
    production_rate_6_8 REAL,
    production_rate_8_10 REAL,
    production_rate_10_12 REAL,
    production_rate_12_15 REAL,
    production_rate_15_18 REAL,
    production_rate_18_plus REAL,
    is_tax_exempt INTEGER NOT NULL DEFAULT 0,
    nominal_diameter_in REAL,
    is_bedding_calculated INTEGER NOT NULL DEFAULT 0,
    bedding_unit_cost_per_cy REAL,
    pipe_material_id INTEGER,
    pipe_size_id INTEGER,
    is_fitting INTEGER NOT NULL DEFAULT 0,
    pipe_fitting_id INTEGER
);

CREATE TABLE IF NOT EXISTS material_companions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    companion_material_id INTEGER NOT NULL,
    ratio REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dirt_aggregate_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    per_ton_cost REAL,
    per_ton_delivery_cost REAL,
    fuel_surcharge_applies INTEGER,
    tons_per_cy REAL
);

CREATE TABLE IF NOT EXISTS section_crew (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    labor_rate_id INTEGER REFERENCES labor_rates(id),
    count INTEGER NOT NULL DEFAULT 1,
    role_name_snapshot TEXT NOT NULL,
    reg_hourly_rate_snapshot REAL NOT NULL,
    ot_hourly_rate_snapshot REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS section_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    equipment_rate_id INTEGER REFERENCES equipment_rates(id),
    machine_id_snapshot TEXT NOT NULL,
    description_snapshot TEXT NOT NULL,
    day_rate_snapshot REAL NOT NULL,
    week_rate_snapshot REAL NOT NULL,
    month_rate_snapshot REAL NOT NULL,
    fuel_capacity_gal_snapshot REAL NOT NULL DEFAULT 0,
    fuel_price_per_gal_snapshot REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    material_rate_id INTEGER REFERENCES material_rates(id),
    description TEXT NOT NULL,
    unit TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    unit_cost REAL NOT NULL DEFAULT 0,
    production_rate REAL,
    bedding_cost REAL NOT NULL DEFAULT 0,
    depth_band TEXT,
    bedding_rule_id INTEGER,
    bedding_quantity_cy REAL NOT NULL DEFAULT 0,
    bedding_unit_cost_per_cy REAL NOT NULL DEFAULT 0,
    bedding_confidence TEXT,
    bedding_warning TEXT,
    pipe_type TEXT,
    nominal_diameter_in REAL,
    is_tax_exempt INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipe_materials (id INTEGER PRIMARY KEY, category TEXT, material_name TEXT, spec_code TEXT);
CREATE TABLE IF NOT EXISTS pipe_sizes (id INTEGER PRIMARY KEY, material_id INTEGER, pipe_name TEXT, pipe_size TEXT, length_ft REAL);
CREATE TABLE IF NOT EXISTS pipe_fittings (id INTEGER PRIMARY KEY, material_id INTEGER, fitting TEXT);
CREATE TABLE IF NOT EXISTS pipe_joints (id INTEGER PRIMARY KEY, material_id INTEGER, joint_type TEXT);
CREATE TABLE IF NOT EXISTS pipe_applications (id INTEGER PRIMARY KEY, material_id INTEGER, application TEXT);
CREATE TABLE IF NOT EXISTS rcp_sizes_weights (id INTEGER PRIMARY KEY, nominal_id_in TEXT, wall_thickness_in TEXT, outside_diameter_in TEXT, weight_lbs_per_ft REAL);
CREATE TABLE IF NOT EXISTS typical_laying_lengths (id INTEGER PRIMARY KEY, material TEXT, common_laying_lengths TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS city_counties (id INTEGER PRIMARY KEY, state TEXT, county TEXT, city_or_town TEXT, level TEXT, utilities TEXT, notes TEXT);

CREATE TABLE IF NOT EXISTS bedding_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    system_type TEXT NOT NULL,
    pipe_material TEXT NOT NULL,
    nominal_diameter_in REAL NOT NULL,
    applies_all_sizes INTEGER NOT NULL DEFAULT 0,
    pipe_od_in REAL NOT NULL,
    bedding_class TEXT NOT NULL,
    depth_below_in REAL NOT NULL DEFAULT 0,
    haunch_to_springline INTEGER NOT NULL DEFAULT 0,
    envelope_above_crown_in REAL NOT NULL DEFAULT 0,
    trench_side_clearance_in REAL NOT NULL DEFAULT 0,
    trench_width_in REAL NOT NULL DEFAULT 0,
    bedding_material_spec TEXT,
    compaction_requirement TEXT,
    bedding_volume_per_lf_cf REAL NOT NULL DEFAULT 0,
    bedding_volume_per_100_lf_cy REAL NOT NULL DEFAULT 0,
    data_confidence TEXT,
    source_document TEXT,
    prohibited INTEGER NOT NULL DEFAULT 0,
    UNIQUE(state, jurisdiction, system_type, pipe_material, nominal_diameter_in, bedding_class)
);
'''


def _ensure_column(conn, table, column, ddl):
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Lightweight migrations keep an existing V2 database usable.
        _ensure_column(conn, 'line_items', 'depth_band', 'TEXT')
        _ensure_column(conn, 'line_items', 'bedding_rule_id', 'INTEGER')
        _ensure_column(conn, 'line_items', 'bedding_quantity_cy', 'REAL NOT NULL DEFAULT 0')
        _ensure_column(conn, 'line_items', 'bedding_unit_cost_per_cy', 'REAL NOT NULL DEFAULT 0')
        _ensure_column(conn, 'line_items', 'bedding_confidence', 'TEXT')
        _ensure_column(conn, 'line_items', 'bedding_warning', 'TEXT')
        _ensure_column(conn, 'bedding_rules', 'applies_all_sizes', 'INTEGER NOT NULL DEFAULT 0')
        conn.execute("INSERT OR IGNORE INTO app_settings(id, company_name) VALUES (1, 'Northwest Contracting Services')")
        conn.commit()
