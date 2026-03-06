const ADMIN_KEY_STORAGE = "sentinela_admin_key";

export function getAdminKey() {
  try {
    return window.localStorage.getItem(ADMIN_KEY_STORAGE) || "";
  } catch {
    return "";
  }
}

export function setAdminKey(key) {
  try {
    window.localStorage.setItem(ADMIN_KEY_STORAGE, key);
  } catch {
    // ignore storage errors
  }
}

export async function adminFetch(url, options = {}) {
  let key = getAdminKey();
  if (!key) {
    key = window.prompt("Informe a chave de administrador:");
    if (key) {
      setAdminKey(key);
    }
  }

  const headers = {
    ...(options.headers || {}),
    "X-Admin-Key": key || "",
    "X-Role": "admin"
  };

  return fetch(url, {
    ...options,
    headers
  });
}
