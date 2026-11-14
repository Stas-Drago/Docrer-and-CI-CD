export const id = (prefix) => `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
