import assert from 'node:assert/strict';
import test from 'node:test';
import { readStoredText, writeStoredText } from '../src/browserStorage.ts';

type StorageStub = Pick<Storage, 'getItem' | 'setItem'>;

function withStorage(storage: StorageStub, run: () => void): void {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
  try {
    run();
  } finally {
    if (descriptor) Object.defineProperty(globalThis, 'localStorage', descriptor);
    else Reflect.deleteProperty(globalThis, 'localStorage');
  }
}

test('reads and writes text using browser storage', () => {
  const values = new Map<string, string>();
  const storage = {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  };

  withStorage(storage, () => {
    assert.equal(writeStoredText('save', '{"v":1}'), true);
    assert.equal(readStoredText('save'), '{"v":1}');
    assert.equal(readStoredText('missing'), null);
  });
});

test('reports browser storage failures to callers', () => {
  const storage = {
    getItem: () => { throw new Error('blocked'); },
    setItem: () => { throw new Error('quota'); },
  };

  withStorage(storage, () => {
    assert.equal(readStoredText('save'), null);
    assert.equal(writeStoredText('save', 'value'), false);
  });
});
