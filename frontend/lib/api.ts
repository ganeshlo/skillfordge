import type { ApiEnvelope } from "./types";

const CONFIGURED_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
let memoryToken: string | null = null;
let refreshPromise: Promise<string> | null = null;

function apiUrl() {
  if (typeof window === "undefined") return CONFIGURED_API_URL;
  try {
    const configured = new URL(CONFIGURED_API_URL);
    if (["localhost", "127.0.0.1", "0.0.0.0"].includes(configured.hostname)) {
      configured.hostname = window.location.hostname;
      return configured.toString().replace(/\/$/, "");
    }
  } catch {
    return CONFIGURED_API_URL;
  }
  return CONFIGURED_API_URL;
}

function accessToken() {
  if (memoryToken) return memoryToken;
  if (typeof window !== "undefined") memoryToken = sessionStorage.getItem("learnos_access");
  return memoryToken;
}

export function saveAccessToken(token: string | null) {
  memoryToken = token;
  if (typeof window !== "undefined") {
    if (token) sessionStorage.setItem("learnos_access", token);
    else sessionStorage.removeItem("learnos_access");
  }
}

async function parse<T>(response: Response): Promise<ApiEnvelope<T>> {
  const body = await response.json();
  if (!response.ok) {
    const fields = body?.error?.fields;
    const fieldMessage = fields && Object.values(fields).flat().find(Boolean);
    throw new Error(String(fieldMessage ?? body?.error?.message ?? "Request failed"));
  }
  return body;
}

async function performRefresh() {
  const response = await fetch(`${apiUrl()}/auth/token/refresh/`, { method: "POST", credentials: "include" });
  if (!response.ok) {
    saveAccessToken(null);
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.replace("/login?session=expired");
    }
    throw new Error("Your session expired. Please sign in again.");
  }
  const body = await parse<{ access: string }>(response);
  saveAccessToken(body.data.access);
  return body.data.access;
}

async function refreshAccess() {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  // Public authentication endpoints must never receive a stale bearer token.
  // DRF authenticates credentials before checking AllowAny and would otherwise
  // reject login/registration before processing the submitted form.
  const token = path.startsWith("/auth/") ? null : accessToken();
  const response = await fetch(`${apiUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (response.status === 401 && retry && !path.startsWith("/auth/")) {
    await refreshAccess();
    return api<T>(path, init, false);
  }
  return (await parse<T>(response)).data;
}

export async function apiBlob(path: string, retry = true): Promise<Blob> {
  const token = accessToken();
  const response = await fetch(`${apiUrl()}${path}`, {
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (response.status === 401 && retry) {
    await refreshAccess();
    return apiBlob(path, false);
  }
  if (!response.ok) {
    let message = "Download failed";
    try {
      const body = await response.json();
      message = body?.error?.message ?? message;
    } catch {}
    throw new Error(message);
  }
  return response.blob();
}

export async function apiForm<T>(path: string, form: FormData, retry = true): Promise<T> {
  const token = accessToken();
  const response = await fetch(`${apiUrl()}${path}`, {
    method: "POST",
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (response.status === 401 && retry) {
    await refreshAccess();
    return apiForm<T>(path, form, false);
  }
  return (await parse<T>(response)).data;
}
