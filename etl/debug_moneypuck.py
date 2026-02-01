"""Debug script for MoneyPuck data loading."""
import sys
sys.path.insert(0, '.')

from etl.src.extract.moneypuck import MoneyPuckClient
from etl.src.db import fetch_one, fetch_all

# Test 1: Fetch MoneyPuck data
print("=== Fetching MoneyPuck data for 2023-24 ===")
with MoneyPuckClient() as client:
    df = client.get_skater_stats(2023)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Check situation column
    if "situation" in df.columns:
        print(f"Situations: {df['situation'].unique()}")
        df_all = df[df["situation"] == "all"]
        print(f"Rows with situation='all': {len(df_all)}")
    else:
        df_all = df

    # Check player ID column
    print(f"\nFirst 5 player IDs in MoneyPuck:")
    if "playerId" in df.columns:
        print(df_all["playerId"].head(10).tolist())
    else:
        print(f"No 'playerId' column. Available columns: {list(df.columns)}")

# Test 2: Check our players table
print("\n=== Checking players in database ===")
result = fetch_all("SELECT nhl_id, name FROM players LIMIT 5")
print("First 5 players in DB:")
for r in result:
    print(f"  {r['nhl_id']}: {r['name']}")

# Test 3: Check if MoneyPuck IDs match our DB
print("\n=== Matching test ===")
if "playerId" in df.columns:
    mp_ids = df_all["playerId"].head(10).tolist()
    for mp_id in mp_ids:
        result = fetch_one("SELECT id, name FROM players WHERE nhl_id = %s", (int(mp_id),))
        if result:
            print(f"  {mp_id} -> MATCH: {result['name']}")
        else:
            print(f"  {mp_id} -> NO MATCH")
