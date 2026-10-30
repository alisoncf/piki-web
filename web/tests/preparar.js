// O jsdom não tem ResizeObserver, que o QLayout do Quasar usa.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
