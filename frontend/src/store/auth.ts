"use client";

import { create } from "zustand";

interface AuthState {
  token: string | null;
  userId: string | null;
  role: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, userId: string, mobile: string, role: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  userId: null,
  role: null,
  isAuthenticated: false,
  setAuth: (token, userId, mobile, role) => {
    localStorage.setItem("token", token);
    localStorage.setItem("userId", userId);
    localStorage.setItem("userMobile", mobile);
    localStorage.setItem("userRole", role);
    set({ token, userId, role, isAuthenticated: true });
  },
  logout: () => {
    ["token", "userId", "userMobile", "userRole"].forEach((k) => localStorage.removeItem(k));
    set({ token: null, userId: null, role: null, isAuthenticated: false });
  },
  hydrate: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("userId");
    const role = localStorage.getItem("userRole");
    if (token && userId) set({ token, userId, role, isAuthenticated: true });
  },
}));
