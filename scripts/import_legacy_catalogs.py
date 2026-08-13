"""Import reusable catalogs from a legacy estimator.db without importing old bids.
Usage: python scripts/import_legacy_catalogs.py PATH_TO_OLD_ESTIMATOR_DB
"""
import sqlite3, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from db import connect, init_db

TABLES = [
    'app_settings','labor_rates','equipment_rates','material_rates','material_companions',
    'dirt_aggregate_rates','pipe_materials','pipe_sizes','pipe_fittings','pipe_joints',
    'pipe_applications','rcp_sizes_weights','typical_laying_lengths','city_counties'
]


def common_columns(src, dst, table):
    s={r[1] for r in src.execute(f'pragma table_info({table})')}
    d=[r[1] for r in dst.execute(f'pragma table_info({table})')]
    return [c for c in d if c in s]


def main(path):
    init_db(); src=sqlite3.connect(path); src.row_factory=sqlite3.Row
    with connect() as dst:
        for table in TABLES:
            if not src.execute("select 1 from sqlite_master where type='table' and name=?",(table,)).fetchone():
                continue
            cols=common_columns(src,dst,table)
            if not cols: continue
            dst.execute(f'DELETE FROM {table}')
            names=','.join(cols); marks=','.join('?' for _ in cols)
            for r in src.execute(f'SELECT {names} FROM {table}'):
                dst.execute(f'INSERT INTO {table} ({names}) VALUES ({marks})',tuple(r[c] for c in cols))
        dst.commit()
    print('Catalog/reference import complete. Old bids were not imported.')

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Provide path to legacy estimator.db')
    main(sys.argv[1])
