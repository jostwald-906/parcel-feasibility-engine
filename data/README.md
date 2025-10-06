# Data Directory

This directory contains downloaded RHNA (Regional Housing Needs Allocation) data from California HCD.

## Files

### `sb35_determinations.csv`

Official HCD SB35 determination data for all California jurisdictions.

- **Source:** California Open Data Portal
- **URL:** https://data.ca.gov/dataset/sb-35-data
- **Direct download:** https://data.ca.gov/dataset/bfa37117-b20a-4675-a2c5-8ab353668ba8/resource/348134ad-a8fb-4c1a-b22a-c896d45667af/download/sb-35-determination-data.csv
- **Update frequency:** Biweekly (HCD updates)
- **Jurisdictions:** 539 California cities and counties
- **Used by:** `app/services/rhna_service.py`

**Important:** This file is NOT committed to git. You must download it manually or run the update script.

### `sb35_determinations.csv.backup`

Backup of the previous version, created automatically by update script.

### `rhna_metadata.txt`

Metadata about the last update (download date, source URL, file hash).

## Initial Setup

To download the data for the first time:

```bash
# Option 1: Run the update script
python scripts/update_rhna_data.py

# Option 2: Download manually
curl -L -o data/sb35_determinations.csv "https://data.ca.gov/dataset/bfa37117-b20a-4675-a2c5-8ab353668ba8/resource/348134ad-a8fb-4c1a-b22a-c896d45667af/download/sb-35-determination-data.csv"
```

## Updating Data

### Manual Update

```bash
python scripts/update_rhna_data.py
```

### Automated Update (Cron)

Add to crontab for weekly updates (Sundays at 2am):

```bash
0 2 * * 0 cd /path/to/project && /path/to/venv/bin/python scripts/update_rhna_data.py >> logs/rhna_update.log 2>&1
```

## Data Format

The CSV contains columns:

- `County`: County name
- `Jurisdiction`: City/county name
- `10%`: "Yes" if 10% affordability requirement
- `50%`: "Yes" if 50% affordability requirement
- `Exempt`: "Yes" if jurisdiction met RHNA targets
- `Above MOD % Complete`: Above-moderate RHNA progress percentage
- `Planning Period Progress`: Overall RHNA progress
- `Last APR`: Date of last Annual Progress Report
- ... and many more columns with detailed RHNA data

## Important Notes

1. **Not in Version Control:** Data files are excluded from git to avoid large commits
2. **Download Required:** Each developer/deployment must download data
3. **Stale Data Warning:** If data is >30 days old, consider updating
4. **Fallback Available:** Service works without data (uses conservative defaults)
5. **Verify with HCD:** Always verify critical determinations with local planning department

## Troubleshooting

### "RHNA data file not found"

This is expected on first setup. Download the data:

```bash
python scripts/update_rhna_data.py
```

### "Service will use fallback logic"

The service loads successfully but has no data. It will return estimated values with warnings. Download data to get official HCD determinations.

### "Data validation failed"

The downloaded file may be corrupted or have unexpected format. Try downloading again:

```bash
rm data/sb35_determinations.csv
python scripts/update_rhna_data.py
```

If backup exists, it will be restored automatically.

## For More Information

- **Integration docs:** `docs/RHNA_INTEGRATION.md`
- **Research:** `docs/RHNA_API_RESEARCH.md`
- **Service code:** `app/services/rhna_service.py`
- **Update script:** `scripts/update_rhna_data.py`
- **Tests:** `tests/test_rhna_service.py`
- **Examples:** `example_rhna_usage.py`
