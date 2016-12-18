"""Script for generating sample random game."""
import random as r
import numpy as np
import sys
import os

pro = False
if len(sys.argv) > 1:
    pro = True

print("42"),
for i in xrange(4):
    print "", r.randint(1, 20),
print
print "47",
for i in xrange(4):
    print "", r.randint(1, 20),
print

allspels = []
if pro:
    allspels = map(lambda x: x*4, range(30))
else:
    allspels = range(120)

h1 = allspels[:]
r.shuffle(h1)

h2 = allspels[:]
r.shuffle(h2)

for i in xrange(10):
    print h1[i]
    print h2[i]
