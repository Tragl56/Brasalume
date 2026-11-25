import assert from 'node:assert/strict';
import test from 'node:test';
import { clamp, rng } from '../src/coreMath.ts';

test('clamp preserves values inside the bounds and clips the rest', () => {
  assert.equal(clamp(4, 2, 8), 4);
  assert.equal(clamp(-1, 0, 1), 0);
  assert.equal(clamp(2, 0, 1), 1);
});

test('seeded random generators produce the same sequence', () => {
  const first = rng(12345);
  const second = rng(12345);
  assert.deepEqual(Array.from({ length: 5 }, first), Array.from({ length: 5 }, second));
});
