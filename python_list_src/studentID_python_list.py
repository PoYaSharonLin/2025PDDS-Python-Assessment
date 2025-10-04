# === 1. Join users with orders (15 points) ===



print("✅ Joined Result:")
print(joined)
# ✅ Joined Result:
# [{'name': 'Alice', 'total': 100}, {'name': 'Alice', 'total': 150}, {'name': 'Bob', 'total': 200}]

# === 2. Group By name (30 points total) ===
# 2-1. Initialize a dictionary (5 points)
# 2-2. Set the "name" in joined as the key in grouped (10 points)
# 2-3. Set the initial value in grouped as a dictionary i.e. {"num_orders": 0, "total_spent": 0} (10 points)
# 2-4. Increment the "num_orders" & "total_spent" (5 points)


print("\n✅ Grouped Result:")
print(grouped)
# ✅ Grouped Result:
# {'Alice': {'num_orders': 2, 'total_spent': 250}, 'Bob': {'num_orders': 1, 'total_spent': 200}}

# === 3. Sort by total_spent descending (15 points) ===
# 3-1. Define sorting function (10 points)
# 3-2. Apply sorting (5 points)



print("\n✅ Sorted Result:")
print(sorted_result)
# ✅ Sorted Result:
# [('Alice', {'num_orders': 2, 'total_spent': 250}), ('Bob', {'num_orders': 1, 'total_spent': 200})]

# === 4. Print top user (10 points) ===



print("\n🏆 Top User:")
print(top_user)
# 🏆 Top User:
# ('Alice', {'num_orders': 2, 'total_spent': 250})