/**
 * WebSocket client with auto-reconnect.
 *
 * Display-only UI: we only receive broadcast messages (no sending).
 */
export function createWsClient({ url, onMessage, onStatus }) {
  let ws = null;
  let shouldReconnect = true;
  let retryMs = 500;

  function connect() {
    onStatus?.("connecting");
    ws = new WebSocket(url);

    ws.addEventListener("open", () => {
      retryMs = 500;
      onStatus?.("connected");
    });

    ws.addEventListener("message", (event) => {
      try {
        onMessage?.(JSON.parse(event.data));
      } catch {
        console.error("WebSocket message is not valid JSON:", event.data);
      }
    });

    ws.addEventListener("close", () => {
      onStatus?.("disconnected");
      if (!shouldReconnect) return;

      setTimeout(() => {
        retryMs = Math.min(Math.floor(retryMs * 1.7), 5000);
        connect();
      }, retryMs);
    });

    ws.addEventListener("error", (e) => {
      console.error("WebSocket error:", e);
    });
  }

  function close() {
    shouldReconnect = false;
    ws?.close();
  }

  return { connect, close };
}
