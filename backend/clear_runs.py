"""Delete all run history. The catalog is untouched."""

from database.connection import init_pool, transaction

init_pool()

with transaction() as cursor:
    cursor.execute("TRUNCATE noc.test_runs CASCADE")

print("run history cleared")