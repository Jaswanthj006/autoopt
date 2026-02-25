# Includes large data, multiple passes, and heavy computation

SIZE = 20_000_000

# Create large dataset
data = [i for i in range(SIZE)]

# Pass 1: Square values
squares = []
for x in data:
    squares.append(x * x)

# Pass 2: Cube values
cubes = []
for x in data:
    cubes.append(x * x * x)

# Pass 3: Conditional filtering
filtered = []
for x in squares:
    if x % 3 == 0:
        filtered.append(x)

# Pass 4: Aggregation
total = 0
for x in filtered:
    total += x

# Extra heavy mathematical loop
result = 0
for i in range(5_000_000):
    result += (i % 7) * (i % 13)

print("Total:", total)
print("Result:", result)