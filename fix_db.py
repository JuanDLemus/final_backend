from django.db import connection

def truncate_app1_tables():
    with connection.cursor() as cursor:
        # 1) get all tables in the current DB
        tables = connection.introspection.table_names()

        # 2) keep only those starting with the prefix
        target = [t for t in tables if t.startswith('app1_')]

        # 3) truncate each one
        for table in target:
            # for Postgres; if you use another engine, switch to DELETE
            sql = f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE;'
            cursor.execute(sql)

# call it
truncate_app1_tables()
