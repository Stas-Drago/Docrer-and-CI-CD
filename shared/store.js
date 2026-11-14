import fs from 'node:fs';
import path from 'node:path';

export function createStore(name) {
  const directory = process.env.DATA_DIR || '/data';
  const file = path.join(directory, `${name}.json`);
  fs.mkdirSync(directory, { recursive: true });
  let state = { records: {}, idempotency: {}, processedEvents: [] };
  if (fs.existsSync(file)) state = { ...state, ...JSON.parse(fs.readFileSync(file, 'utf8')) };
  const save = () => fs.writeFileSync(file, JSON.stringify(state, null, 2));
  return {
    get: (id) => state.records[id],
    all: () => Object.values(state.records),
    put: (record) => { state.records[record.id] = record; save(); return record; },
    update: (id, patch) => { state.records[id] = { ...state.records[id], ...patch }; save(); return state.records[id]; },
    idempotent: (key) => state.idempotency[key],
    remember: (key, value) => { state.idempotency[key] = value; save(); },
    processed: (eventId) => state.processedEvents.includes(eventId),
    markProcessed: (eventId) => { state.processedEvents.push(eventId); save(); }
  };
}
