import "@testing-library/jest-dom/vitest";

// jsdom does not implement scrollTo; ChatWorkspace calls it for auto-scroll.
if (typeof Element !== "undefined" && !Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {};
}

// crypto.randomUUID is used to key messages; provide a deterministic stub.
if (typeof globalThis.crypto === "undefined") {
  // @ts-expect-error minimal shim for the test environment
  globalThis.crypto = {};
}
if (!globalThis.crypto.randomUUID) {
  let counter = 0;
  // @ts-expect-error minimal shim signature
  globalThis.crypto.randomUUID = () => `test-uuid-${counter++}`;
}
