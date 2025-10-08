#!/usr/bin/env python3
"""
Check database schema to verify users table structure.
"""
import os
from sqlalchemy import create_engine, inspect, text

# Get DATABASE_URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:imtVpGVeNvClMOpQDWtAFosDCOczvLKG@yamabiko.proxy.rlwy.net:42117/railway")

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

# Create inspector
inspector = inspect(engine)

# Check if users table exists
tables = inspector.get_table_names()
print(f"\n📊 Database Tables ({len(tables)}):")
for table in tables:
    print(f"  - {table}")

if "users" in tables:
    print(f"\n✅ Users table found!")
    print(f"\n📋 Users Table Schema:")
    print(f"{'Column':<20} {'Type':<25} {'Nullable':<10} {'Default':<20}")
    print("="*80)

    columns = inspector.get_columns("users")
    for col in columns:
        col_name = col['name']
        col_type = str(col['type'])
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = str(col.get('default', ''))[:20] if col.get('default') else '-'
        print(f"{col_name:<20} {col_type:<25} {nullable:<10} {default:<20}")

    # Check indexes
    print(f"\n🔑 Indexes:")
    indexes = inspector.get_indexes("users")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['column_names']} (unique={idx['unique']})")

    # Check foreign keys
    print(f"\n🔗 Foreign Keys:")
    fks = inspector.get_foreign_keys("users")
    if fks:
        for fk in fks:
            print(f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    else:
        print("  - None")

    # Check alembic version
    print(f"\n📌 Alembic Migration Status:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        if versions:
            for v in versions:
                print(f"  - Current revision: {v[0]}")
        else:
            print("  - No migrations applied")

    # Count rows
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"\n👥 User Count: {count}")

else:
    print(f"\n❌ Users table NOT found!")
    print(f"\nAvailable tables: {', '.join(tables)}")
