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
    console.log(`[WebSocket] Connecting to ${url}...`);
    onStatus?.("connecting");

    try {
      ws = new WebSocket(url);
    } catch (error) {
      console.error("[WebSocket] Failed to create WebSocket:", error);
      onStatus?.("error");
      // Retry connection
      if (shouldReconnect) {
        setTimeout(() => {
          retryMs = Math.min(Math.floor(retryMs * 1.7), 5000);
          connect();
        }, retryMs);
      }
      return;
    }

    ws.addEventListener("open", () => {
      console.log("[WebSocket] Connected successfully");
      retryMs = 500;
      onStatus?.("connected");
    });

    ws.addEventListener("message", (event) => {
      console.log("[WebSocket] Message received:", event.data);
      try {
        onMessage?.(JSON.parse(event.data));
      } catch (error) {
        console.error("[WebSocket] Message is not valid JSON:", event.data, error);
      }
    });

    ws.addEventListener("close", (event) => {
      console.log(`[WebSocket] Connection closed (code: ${event.code}, reason: ${event.reason || "none"})`);
      onStatus?.("disconnected");

      if (!shouldReconnect) {
        console.log("[WebSocket] Not reconnecting (closed intentionally)");
        return;
      }

      console.log(`[WebSocket] Reconnecting in ${retryMs}ms...`);
      setTimeout(() => {
        retryMs = Math.min(Math.floor(retryMs * 1.7), 5000);
        connect();
      }, retryMs);
    });

    ws.addEventListener("error", (error) => {
      console.error("[WebSocket] Error occurred:", error);
      onStatus?.("error");
    });
  }

  function close() {
    console.log("[WebSocket] Closing connection...");
    shouldReconnect = false;
    ws?.close();
  }

  return { connect, close };
}
