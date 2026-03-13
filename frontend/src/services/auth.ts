import { apiJson } from "./api";

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user_id: string;
  email: string;
};

const TOKEN_KEY = "chatdock_token";
const USER_KEY = "chatdock_user_email";

export async function login(email: string, password: string) {
  return apiJson<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string) {
  return apiJson<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function setSession(token: string, email: string) {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, email);
}

export function clearSession() {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function getUserEmail() {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(USER_KEY);
}
