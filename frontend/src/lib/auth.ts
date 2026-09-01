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
import api, { AUTH_UNAUTHORIZED_EVENT, AuthConfigResponse, AuthUser } from './api';

/**
 * Fetch /auth/config, retrying a few times on transient failure.
 *
 * bootstrap() runs ONCE at mount, so a single hiccup here decides the whole
 * session. The hosted box is stopped when idle and woken on demand: right after
 * a wake the SPA can load a beat before the backend finishes starting, so the
 * first /auth/config can 5xx or refuse the connection. Riding that out with a
 * short backoff means the common case self-heals with no user action (no manual
 * "restart the browser"). Returns the config, or null only after every attempt
 * failed — the caller then fails SAFE.
 */
async function fetchAuthConfigWithRetry(): Promise<AuthConfigResponse | null> {
  const delaysMs = [0, 500, 1200, 2500];
  for (let attempt = 0; attempt < delaysMs.length; attempt += 1) {
    if (delaysMs[attempt] > 0) {
      await new Promise((resolve) => setTimeout(resolve, delaysMs[attempt]));
    }
    try {
      return await api.auth.config();
    } catch {
      // transient (backend warming up / network): try again
    }
  }
  return null;
}

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
  /** Whether public self-service signup is available (hosted demo only). */
  signupEnabled: boolean;
  /** '' when captcha is off, else 'turnstile' | 'hcaptcha'. */
  captchaProvider: string;
  /** Public captcha site key for the signup widget ('' when off). */
  captchaSiteKey: string;
  /** Bootstrap lifecycle: routes render only once 'ready'. */
  status: AuthStatus;
  /** Fetch /auth/config (+ /auth/me when enforced). Safe to call once at mount. */
  bootstrap: () => Promise<void>;
  login: (username: string, password: string) => Promise<AuthUser>;
  signup: (
    username: string,
    email: string,
    password: string,
    captchaToken?: string,
  ) => Promise<AuthUser>;
  logout: (everywhere?: boolean) => Promise<void>;
  /** Drop the cached user (used by the global 401 handler). */
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  authRequired: false,
  signupEnabled: false,
  captchaProvider: '',
  captchaSiteKey: '',
  status: 'idle',

  bootstrap: async () => {
    if (get().status === 'loading') return;
    set({ status: 'loading' });

    let authRequired = false;
    let signupEnabled = false;
    let captchaProvider = '';
    let captchaSiteKey = '';
    let user: AuthUser | null = null;

    const config = await fetchAuthConfigWithRetry();
    if (config) {
      authRequired = config.auth_required;
      signupEnabled = config.signup_enabled ?? false;
      captchaProvider = config.captcha_provider ?? '';
      captchaSiteKey = config.captcha_site_key ?? '';
      if (authRequired) {
        try {
          user = await api.auth.me();
        } catch {
          // 401 = not logged in; network failure = treat as logged out and
          // let the login flow re-establish the session.
          user = null;
        }
      }
    } else {
      // /auth/config still unreachable after retries. FAIL SAFE: assume auth is
      // required so the app routes to /login (a form the user can act on),
      // never rendering the dashboard shell for an unverified session. The old
      // fail-OPEN default (authRequired=false) rendered the dashboard, whose
      // data calls then 401'd and bounced /login <-> / in a loop that only a
      // full browser restart cleared. A reload or a successful login recovers
      // the moment the backend is reachable again.
      authRequired = true;
    }

    // Never clobber a login that completed while this bootstrap was in
    // flight: the /auth/me probe above may have run before the session
    // cookie existed and report null for a user who is now signed in.
    set((state) => ({
      user: state.user ?? user,
      authRequired,
      signupEnabled,
      captchaProvider,
      captchaSiteKey,
      status: 'ready',
    }));
  },

  login: async (username: string, password: string) => {
    const result = await api.auth.login(username, password);
    set({ user: result.user });
    return result.user;
  },

  signup: async (username: string, email: string, password: string, captchaToken?: string) => {
    const result = await api.auth.signup({
      username,
      email,
      password,
      captcha_token: captchaToken,
    });
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
