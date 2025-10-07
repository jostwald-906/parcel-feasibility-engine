# PostgreSQL Migration Summary

## Overview

Successfully migrated Parcel Feasibility Engine from SQLite to PostgreSQL for production deployment on Railway.

## Changes Made

### 1. Configuration Updates

**File: `/app/core/config.py`**
- Updated `DATABASE_URL` to use environment variable with Field descriptor
- Default: SQLite for development (`sqlite:///./parcel_feasibility.db`)
- Production: PostgreSQL from Railway environment variable

```python
DATABASE_URL: str = Field(
    default="sqlite:///./parcel_feasibility.db",
    description="Database connection string (PostgreSQL in production, SQLite in dev)"
)
```

### 2. Railway PostgreSQL Setup

**PostgreSQL Service Created:**
- Service Name: `Postgres`
- Database: `railway`
- Region: `us-west2`
- Version: PostgreSQL 17
- Storage: 5GB volume with auto-backups

**Environment Variables:**
- `DATABASE_URL` - Internal connection (within Railway network)
- `DATABASE_PUBLIC_URL` - External connection (for local development/migrations)

**Connection Details:**
- Internal: `postgresql://postgres:***@postgres.railway.internal:5432/railway`
- Public: `postgresql://postgres:***@yamabiko.proxy.rlwy.net:42117/railway`

### 3. Alembic Migration Setup

**Initialized Alembic:**
```bash
alembic init alembic
```

**Configuration Files:**
- `alembic.ini` - Main configuration
- `alembic/env.py` - Environment setup with SQLModel metadata
- `alembic/versions/` - Migration scripts directory

**Key Configuration (alembic/env.py):**
```python
# Import all models for autogenerate
from app.models.user import User
from app.models.subscription import Subscription, APIUsage

# Use SQLModel metadata
target_metadata = SQLModel.metadata

# Set DATABASE_URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

### 4. Database Schema

**Created Tables:**

**users**
- `id` (PRIMARY KEY)
- `email` (UNIQUE, indexed)
- `full_name`
- `hashed_password`
- `is_active`
- `is_verified`
- `created_at`
- `updated_at`

**subscriptions**
- `id` (PRIMARY KEY)
- `user_id` (FOREIGN KEY → users.id, indexed)
- `stripe_customer_id` (UNIQUE, indexed)
- `stripe_subscription_id` (UNIQUE, indexed)
- `status` (ENUM: ACTIVE, PAST_DUE, UNPAID, CANCELED, etc.)
- `plan` (ENUM: FREE, PRO)
- `current_period_start`
- `current_period_end`
- `cancel_at_period_end`
- `created_at`
- `updated_at`

**api_usage**
- `id` (PRIMARY KEY)
- `user_id` (FOREIGN KEY → users.id, indexed)
- `endpoint` (indexed)
- `method`
- `status_code`
- `timestamp` (indexed)
- `parcel_apn`

**Migration File:**
```
alembic/versions/c437fda93595_initial_schema_with_users_subscriptions_.py
```

## Local Testing

### Setup Local PostgreSQL

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create test database
createdb parcel_feasibility_test
```

### Run Migrations Locally

```bash
# Set DATABASE_URL to local PostgreSQL
export DATABASE_URL="postgresql://localhost/parcel_feasibility_test"

# Run migrations
./venv/bin/alembic upgrade head

# Verify tables created
psql parcel_feasibility_test -c "\dt"
```

### Test Application with PostgreSQL

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://localhost/parcel_feasibility_test"

# Run application
./venv/bin/uvicorn app.main:app --reload --port 8000
```

## Railway Deployment

### Deployment Status

✅ **Application Deployed:** https://parcel-feasibility-engine-production.up.railway.app
✅ **PostgreSQL Connected:** `postgres.railway.internal:5432/railway`
✅ **Health Check Passing:** Database connection verified

### Running Migrations on Railway

**Option 1: Using Railway CLI (Recommended)**

```bash
# From project root
railway run bash scripts/run_migrations.sh
```

**Option 2: Manual via Railway Dashboard**

1. Go to Railway Dashboard → Parcel Feasibility Engine project
2. Select the `parcel-feasibility-engine` service
3. Click "Deploy" → "Run Command"
4. Enter command: `alembic upgrade head`
5. Click "Run"

**Option 3: SSH into Railway container**

```bash
# SSH into running container
railway run bash

# Inside container, run:
alembic upgrade head
exit
```

### Verifying Migration

Check tables exist on Railway PostgreSQL:

```bash
# Using Railway CLI
railway run --service Postgres psql -c "\dt"

# Should show:
# - alembic_version
# - users
# - subscriptions
# - api_usage
```

## Migration Commands

### Create New Migration

```bash
# After modifying models
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Local
export DATABASE_URL="postgresql://localhost/parcel_feasibility_test"
alembic upgrade head

# Railway (via CLI)
railway run alembic upgrade head

# Railway (inside container)
railway run bash
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### View Migration History

```bash
# Current revision
alembic current

# Migration history
alembic history

# Show all revisions
alembic history --verbose
```

## Benefits of PostgreSQL Migration

### Production Readiness
- **Concurrent Writes:** Multi-user environment support
- **ACID Compliance:** Data integrity guarantees
- **Connection Pooling:** Efficient resource management
- **Automatic Backups:** Railway daily backups included

### Scalability
- **Performance:** Better query optimization and indexing
- **Storage:** 5GB volume (expandable)
- **Concurrent Connections:** Handles multiple simultaneous users

### Feature Support
- **User Accounts:** Authentication and authorization ready
- **Saved Analyses:** Store user analysis history
- **Subscriptions:** Stripe payment integration ready
- **API Usage Tracking:** Monitor and limit API usage

## Environment Variables

### Development (Local)

```bash
# .env file
DATABASE_URL=sqlite:///./parcel_feasibility.db
# OR for local PostgreSQL testing:
DATABASE_URL=postgresql://localhost/parcel_feasibility_test
```

### Production (Railway)

```bash
# Set automatically by Railway PostgreSQL plugin
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

## Troubleshooting

### Connection Errors

**Error:** `could not translate host name "postgres.railway.internal"`
- **Cause:** Trying to connect to internal Railway hostname from outside Railway network
- **Solution:** Use `DATABASE_PUBLIC_URL` for external connections

### Migration Conflicts

**Error:** `Target database is not up to date`
- **Solution:** Check current revision with `alembic current` and upgrade to head

### Missing Tables

**Error:** `relation "users" does not exist`
- **Solution:** Run migrations: `alembic upgrade head`

### Permission Errors

**Error:** `permission denied for table users`
- **Solution:** Verify DATABASE_URL has correct credentials

## Next Steps

1. **Run Migrations on Railway:**
   ```bash
   railway run bash scripts/run_migrations.sh
   ```

2. **Verify Tables Created:**
   ```bash
   railway run --service Postgres psql -c "\dt"
   ```

3. **Test User Registration:**
   - POST to `/api/v1/auth/register` endpoint
   - Verify user created in database

4. **Monitor Database:**
   - Railway Dashboard → Postgres service → Metrics
   - Check disk usage, connections, query performance

5. **Set up Database Backups:**
   - Railway auto-backups enabled by default
   - Manual backup: Railway Dashboard → Postgres → Backups

## References

- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **SQLModel Documentation:** https://sqlmodel.tiangolo.com/
- **Railway PostgreSQL:** https://docs.railway.app/databases/postgresql
- **PostgreSQL 17 Docs:** https://www.postgresql.org/docs/17/

## Migration Checklist

- [x] PostgreSQL service provisioned on Railway
- [x] DATABASE_URL environment variable set
- [x] Config.py updated to use DATABASE_URL from environment
- [x] Alembic initialized with migrations
- [x] Initial migration created (users, subscriptions, api_usage tables)
- [x] Local testing with PostgreSQL successful
- [x] Code committed and pushed to Railway
- [x] Application deployed with PostgreSQL connection
- [ ] **Migrations run on Railway production database** (Manual step required)
- [ ] Tables verified in production database
- [ ] User registration endpoint tested

## Success Criteria

✅ PostgreSQL provisioned on Railway
✅ DATABASE_URL environment variable set
✅ psycopg2-binary and alembic added to requirements.txt
✅ Alembic initialized with migrations
✅ Database schema created (tables exist locally)
✅ Application connects to PostgreSQL successfully
✅ Local testing with PostgreSQL works
✅ Production deployment uses PostgreSQL
⏳ **Final Step:** Run migrations on Railway production database

---

**Generated:** 2025-10-07
**Database Version:** PostgreSQL 17
**Migration Revision:** c437fda93595
