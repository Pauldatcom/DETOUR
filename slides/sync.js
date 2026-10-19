(() => {
  const key = 'detour-slide-state-v1';
  const channelName = 'detour-slides-v1';
  const source = Math.random().toString(36).slice(2);
  const seen = new Set();
  const listeners = new Set();
  const requests = new Set();
  let channel = null;

  function valid(message) {
    return message && message.type === 'slide' && [1, 2, 3, 4, 5, 6, 7].includes(message.day)
      && Number.isInteger(message.index) && message.index >= 0;
  }
  function receive(message) {
    if (!message || message.source === source || seen.has(message.id)) return;
    seen.add(message.id);
    if (message.type === 'request') {
      requests.forEach(fn => fn());
    } else if (valid(message)) {
      listeners.forEach(fn => fn(message.day, message.index));
    }
  }
  if ('BroadcastChannel' in window) {
    channel = new BroadcastChannel(channelName);
    channel.addEventListener('message', event => receive(event.data));
  }
  window.addEventListener('storage', event => {
    if (event.key !== key || !event.newValue) return;
    try { receive(JSON.parse(event.newValue)); } catch (_) { /* Ignore invalid storage. */ }
  });
  function send(message) {
    const packet = { ...message, source, id: `${source}-${Date.now()}-${Math.random()}` };
    try { localStorage.setItem(key, JSON.stringify(packet)); } catch (_) { /* Channel may still work. */ }
    if (channel) channel.postMessage(packet);
  }
  window.DeckSync = {
    publish(day, index) { send({ type: 'slide', day, index }); },
    request() {
      if (channel) channel.postMessage({ type: 'request', source, id: `${source}-${Date.now()}` });
    },
    onSlide(fn) { listeners.add(fn); },
    onRequest(fn) { requests.add(fn); },
    lastSlide() {
      try {
        const packet = JSON.parse(localStorage.getItem(key));
        return valid(packet) ? packet : null;
      } catch (_) { return null; }
    }
  };
})();
