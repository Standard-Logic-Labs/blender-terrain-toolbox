"""Negative inside solid. Base is an implicit signed field, not exact distance.
Sphere primitives are exact SDFs. No distance-based skipping is assumed.
"""
import math


class Field:
    def __init__(self, state):
        self.phase = (state['seed'] % 65536) * 0.17320508075688773
        self.operations = [o for o in state['operations'] if o['enabled']]

    def __call__(self, x, y, z):
        height = 24 + 12*math.sin(x/137+self.phase)*math.cos(y/113-self.phase)
        value = z-height
        for op in self.operations:
            cx, cy, cz = op['center']
            d = math.sqrt((x-cx)**2+(y-cy)**2+(z-cz)**2)-op['radius']
            value = max(value, -d) if op['kind'] == 'SPHERE_CUT' else min(value, d)
        return value

    def normal(self, p, epsilon):
        x, y, z = p
        n = (self(x+epsilon,y,z)-self(x-epsilon,y,z),
             self(x,y+epsilon,z)-self(x,y-epsilon,z),
             self(x,y,z+epsilon)-self(x,y,z-epsilon))
        length = math.sqrt(sum(v*v for v in n))
        return tuple(v/length for v in n) if length > 1e-15 else (0., 0., 1.)
