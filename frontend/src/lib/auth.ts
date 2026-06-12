/**
 * Constitutional AIOps - Auth state (zustand).
 *
 * Holds the signed-in user and the backend enforcement flag. bootstrap() runs
 * once at App mount: it asks the public /auth/config endpoint whether in-app
 * auth is enforced and, only if so, probes /auth/me for the current session
 * (a 401 simply means "logged out"). While AUTH_REQUIRED is off on the
 * backend the store reports authRequired=false and the UI behaves exactly as
 * before the login system existed.
 *
 * Global 401 handling: lib/api.ts dispatches AUTH_UNAUTHORIZED_EVENT on any
 * non-auth 401 (and redirects to /login); the listener below clears the
 * cached user so the UI never shows a stale identity.
 */

import { create } from 'zustand';
import api, { AUTH_UNAUTHORIZED_EVENT, AuthUser } from './api';

/**
 * localStorage prefix used by useConversationHistory's per-user cache
 * (`aiops.chat.conversations:<username>`). Kept in sync by convention rather
 * than an import so this module and the hook do not form a cycle.
 */
const CHAT_CACHE_PREFIX = 'aiops.chat.conversations';

/** Drop every per-user conversation cache (called on logout). Never throws. */
function clearChatCaches(): void {
  try {
    const doomed: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const key = window.localStorage.key(i);
      if (key && key.startsWith(CHAT_CACHE_PREFIX)) doomed.push(key);
    }
    doomed.forEach((key) => window.localStorage.removeItem(key));
  } catch {
    // Storage may be unavailable (private mode); the cache is best-effort.
  }
}

export type AuthStatus = 'idle' | 'loading' | 'ready';

export interface AuthState {
  user: AuthUser | null;
  /** Whether the backend enforces in-app auth (AUTH_REQUIRED). */
  authRequired: boolean;
  /** Bootstrap lifecycle: routes render only once 'ready'. */
  status: AuthStatus;
  /** Fetch /auth/config (+ /auth/me when enforced). Safe to call once at mount. */
  bootstrap: () => Promise<void>;
  login: (username: string, password: string) => Promise<AuthUser>;
  logout: (everywhere?: boolean) => Promise<void>;
  /** Drop the cached user (used by the global 401 handler). */
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  authRequired: false,
  status: 'idle',

  bootstrap: async () => {
    if (get().status === 'loading') return;
    set({ status: 'loading' });

    let authRequired = false;
    let user: AuthUser | null = null;
    try {
      const config = await api.auth.config();
      authRequired = config.auth_required;
      if (authRequired) {
        try {
          user = await api.auth.me();
        } catch {
          // 401 = not logged in; network failure = treat as logged out and
          // let the login flow re-establish the session.
          user = null;
        }
      }
    } catch {
      // /auth/config unreachable: fall back to the backend default
      // (enforcement off) so a transient hiccup never bricks the SPA.
      authRequired = false;
    }

    // Never clobber a login that completed while this bootstrap was in
    // flight: the /auth/me probe above may have run before the session
    // cookie existed and report null for a user who is now signed in.
    set((state) => ({ user: state.user ?? user, authRequired, status: 'ready' }));
  },

  login: async (username: string, password: string) => {
    const result = await api.auth.login(username, password);
    set({ user: result.user });
    return result.user;
  },

  logout: async (everywhere = false) => {
    try {
      await api.auth.logout(everywhere);
    } catch {
      // Even if the server call fails, clear local state so the UI logs out.
    }
    clearChatCaches();
    set({ user: null });
  },

  clearUser: () => set({ user: null }),
}));

// Global 401s (session expired/revoked mid-use): clear the cached user. The
// redirect itself is handled by lib/api.ts.
if (typeof window !== 'undefined') {
  window.addEventListener(AUTH_UNAUTHORIZED_EVENT, () => {
    useAuthStore.getState().clearUser();
  });
}

export default useAuthStore;
