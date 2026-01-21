from src.db.supabase_client import supabase

res = supabase.table("chat_messages").select("*").limit(1).execute()

print("Connected ✅")
print("Data:", res.data)
