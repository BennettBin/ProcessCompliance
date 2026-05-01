const defaultBaseUrl =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:5174`
    : "http://127.0.0.1:5174";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl;

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  const text = await response.text();
  let payload: unknown = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { message: text };
  }

  if (!response.ok) {
    throw new Error(JSON.stringify(payload));
  }
  return payload as T;
}

export { API_BASE_URL };
