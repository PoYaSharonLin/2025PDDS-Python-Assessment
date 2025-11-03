# === 1. Create DataFrames (5 points) ===
import pandas as pd


print("✅ df_users:")
print(df_users)
# ✅ df_users:
#   id   name
# 0   1  Alice
# 1   2    Bob

print("\n✅ df_orders:")
print(df_orders)
# ✅ df_orders:
#   user_id  total
# 0        1    100
# 1        1    150
# 2        2    200

# === 2. Merge DataFrames (10 points) ===



print("\n✅ Merged DataFrame:")
print(merged)
# ✅ Merged DataFrame:
#   id   name  user_id  total
# 0   1  Alice        1    100
# 1   1  Alice        1    150
# 2   2    Bob        2    200

# === 3. Create sorted_result (25 points) ===
# 3-1. Group by name (5 points)
# 3-2. Aggregate: count and sum (10 points)
# 3-3. Sort by total_spent descending (5 points)



print("\n✅ Sorted Result:")
print(sorted_result)
# ✅ Sorted Result:
#       num_orders  total_spent
# name                          
# Alice           2          250
# Bob             1          200

# === 4. Print user with highest total spent (5 points) ===



print("\n🏆 Top User:")
print(top_user)
# 🏆 Top User:
# num_orders       2
# total_spent    250
# Name: Alice, dtype: int64