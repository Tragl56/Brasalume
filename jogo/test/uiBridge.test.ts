import assert from 'node:assert/strict';
import test from 'node:test';
import { getGameUi, setGameUi, subscribeGameUi } from '../src/uiBridge.ts';

test('notifies subscribers only when the published UI state changes', () => {
  const id = 'bridge-test-' + Math.random();
  let notifications = 0;
  const unsubscribe = subscribeGameUi(id, () => notifications++);

  setGameUi(id, { className: 'hud' });
  setGameUi(id, { className: 'hud' });
  assert.equal(notifications, 1);
  assert.equal(getGameUi(id)?.className, 'hud');

  unsubscribe();
  setGameUi(id, { title: 'updated' });
  assert.equal(notifications, 1);
});

test('merges style patches without dropping previously published styles', () => {
  const id = 'bridge-style-test-' + Math.random();
  setGameUi(id, { style: { color: 'red' } });
  setGameUi(id, { style: { width: '100%' } });

  assert.deepEqual(getGameUi(id)?.style, { color: 'red', width: '100%' });
});
