from sqlalchemy import inspect, text
from src.config.database import Base, engine
from src import models
def migrate():
    Base.metadata.create_all(engine)
    # 已有数据卷的增量列升级（新部署由 create_all 一次到位）
    with engine.begin() as conn:
        insp = inspect(conn)
        def add_column(table, column, ddl):
            if insp.has_table(table) and column not in [c['name'] for c in insp.get_columns(table)]:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {ddl}'))
        add_column('reports', 'product_id', 'product_id INTEGER NULL')
        add_column('reports', 'pending_version_id', 'pending_version_id INTEGER NULL')
        add_column('deliveries', 'conclusion_version_id', 'conclusion_version_id INTEGER NULL')
        if conn.dialect.name == 'mysql' and insp.has_table('reports'):
            for c in insp.get_columns('reports'):
                if c['name'] == 'job_id' and not c['nullable']:
                    conn.execute(text('ALTER TABLE reports MODIFY COLUMN job_id INT NULL'))
if __name__=='__main__':migrate()
