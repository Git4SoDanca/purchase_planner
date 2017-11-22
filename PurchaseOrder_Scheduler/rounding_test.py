import math

def roundup(x,y):
  return int(math.ceil(x/y))*y;


print(roundup(3,4))
print(roundup(7,4))
print(roundup(9,4))
print(roundup(3,12))
print(roundup(15,12))
print(roundup(3,11))
print(roundup(8,12))
