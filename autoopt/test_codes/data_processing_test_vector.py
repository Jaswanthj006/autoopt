import numpy as np
SIZE = 20000000
data = [i for i in range(SIZE)]
squares = [x * x for x in data]
cubes = [x * x * x for x in data]
filtered = []
for x in squares:
    if x % 3 == 0:
        filtered.append(x)
total = sum(filtered)
result = 0
for i in range(5000000):
    result += i % 7 * (i % 13)
print('Total:', total)
print('Result:', result)