/* Cookie de sessão é HttpOnly: este componente nunca lê ou armazena seu valor. */
(() => {
  let args, running = false, initialized = false, lastCode = null, lastClear = null;
  let timer, retryTimer, eventId = 0, lastForce = null;
  const parentOrigin = new URL(document.referrer || location.href).origin;
  function send(type, payload = {}) {
    window.parent.postMessage({isStreamlitMessage: true, type, ...payload}, parentOrigin);
  }
  function emit(value) {
    document.getElementById("connection").textContent = value.status === "error"
      ? "Reconectando…" : "Conexão ativa";
    send("streamlit:setComponentValue", {value: {...value, event: `${Date.now()}-${++eventId}`}, dataType: "json"});
  }
  async function request(path, body) {
    const base = args.api_url || `${location.protocol}//${location.hostname}:${args.api_port || 8000}`;
    const response = await fetch(`${base.replace(/\/$/, "")}/sessoes/${path}`, {
      method: "POST", credentials: "include", cache: "no-store",
      headers: {"Content-Type": "application/json", "X-Session-Request": "1"},
      body: JSON.stringify(body || {}), signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      const error = new Error("Sessão indisponível"); error.status = response.status; throw error;
    }
    return response.json();
  }
  async function sync() {
    if (running || !args || retryTimer) return;
    running = true;
    try {
      if (args.clear && args.clear !== lastClear) {
        await request("limpar-cookie");
        lastClear = args.clear; clearInterval(timer);
        initialized = true;
        emit({status: "guest", cleared: args.clear});
      } else if (args.code && args.code !== lastCode) {
        const code = args.code;
        // Não reivindicar o mesmo código duas vezes, mesmo se a resposta se perder.
        lastCode = code;
        let data;
        try { data = await request("vincular", {code}); }
        catch (error) {
          if (error.status === 403) throw error;
          data = await request("restaurar");
        }
        if (data.session_id !== args.session_id) {
          const mismatch = new Error("Vinculação não confirmada"); mismatch.status = 401; throw mismatch;
        }
        initialized = true; authenticated(data);
      } else if (!initialized) {
        const data = await request("restaurar");
        initialized = true; authenticated(data);
      }
    } catch (error) {
      if (error.status === 401) {
        initialized = true; clearInterval(timer);
        emit({status: "guest", claim_failed: Boolean(args.code)});
      } else {
        emit({status: "error", forbidden: error.status === 403});
        initialized = false;
        retryTimer = setTimeout(() => { retryTimer = null; sync(); }, 15000);
      }
    } finally { running = false; }
  }
  function authenticated(data) {
    emit({status: "authenticated", ...data});
    clearInterval(timer);
    timer = setInterval(() => { initialized = false; sync(); }, data.refresh_seconds * 1000);
  }
  window.addEventListener("message", event => {
    if (event.source !== window.parent || event.origin !== parentOrigin || event.data.type !== "streamlit:render") return;
    const nextArgs = event.data.args;
    if (!args || nextArgs.code !== args.code || nextArgs.clear !== args.clear || nextArgs.force !== args.force) {
      clearTimeout(retryTimer); retryTimer = null;
    }
    args = nextArgs;
    if (args.force && args.force !== lastForce) { lastForce = args.force; initialized = false; }
    // Mantém o componente renderizado: WebKit pode suspender timers em iframe sem área.
    send("streamlit:setFrameHeight", {height: 24});
    sync();
  });
  window.addEventListener("online", () => { clearTimeout(retryTimer); retryTimer = null; initialized = false; sync(); });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") { initialized = false; sync(); }
  });
  send("streamlit:componentReady", {apiVersion: 1});
})();
