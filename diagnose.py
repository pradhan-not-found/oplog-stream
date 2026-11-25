"""
diagnose.py  — quick connection + insert test
Run: python diagnose.py
"""
import os, time
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGO_URI")

print(f"\n1. URI loaded: {'✅ YES' if uri else '❌ NO — .env not found!'}")
if not uri: exit(1)
print(f"   → {uri[:55]}...")

print("\n2. Connecting to Atlas...")
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    print("   ✅ CONNECTED")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    exit(1)

db  = client["event_streaming"]
col = db["sensor_events"]

print("\n3. Inserting 50 test documents...")
t0 = time.time()
for i in range(50):
    col.insert_one({"test": True, "seq": i, "ts": time.time()})
elapsed = time.time() - t0
print(f"   ✅ 50 docs inserted in {elapsed:.2f}s  ({50/elapsed:.0f} docs/sec)")

count = col.count_documents({})
print(f"\n4. Total docs in collection now: {count}")
print("\n✅ Atlas IS working. Check Metrics tab → Opcounters → zoom to last 5 minutes.")
client.close()
