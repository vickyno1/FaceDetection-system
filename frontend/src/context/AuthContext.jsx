/**
 * Authentication Context.
 * Wraps Firebase Web SDK Authentication and supports instant Demo Administrator login.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { initializeApp, getApps } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  signOut as fbSignOut, 
  onAuthStateChanged 
} from 'firebase/auth';

const AuthContext = createContext(null);

// Initialize Firebase Web SDK only if valid apiKey is configured
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

let auth = null;
if (firebaseConfig.apiKey && !firebaseConfig.apiKey.includes('Placeholder')) {
  try {
    const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    auth = getAuth(app);
  } catch (err) {
    console.warn('Firebase Web SDK init warning:', err);
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  // Sync token from localStorage or Firebase
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);

    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');

    if (savedToken && savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
        setRole(parsed.role || 'admin');
        setLoading(false);
        return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
      } catch (e) {
        localStorage.removeItem('auth_user');
        localStorage.removeItem('auth_token');
      }
    }

    if (auth) {
      const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
        if (fbUser) {
          const idToken = await fbUser.getIdToken();
          localStorage.setItem('auth_token', idToken);
          const userData = {
            uid: fbUser.uid,
            email: fbUser.email,
            displayName: fbUser.displayName || 'Administrator',
            role: 'admin',
          };
          setUser(userData);
          setRole('admin');
          localStorage.setItem('auth_user', JSON.stringify(userData));
        } else {
          setUser(null);
          setRole(null);
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
        }
        setLoading(false);
      });
      return () => {
        unsubscribe();
        window.removeEventListener('auth:unauthorized', handleUnauthorized);
      };
    } else {
      setLoading(false);
    }

    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  // Standard Email/Password login
  const login = async (email, password) => {
    if (!auth) {
      throw new Error(
        'Firebase Web SDK is not configured with live credentials. Use Demo Admin Login for local evaluation.'
      );
    }
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await userCredential.user.getIdToken();
    localStorage.setItem('auth_token', idToken);
    const userData = {
      uid: userCredential.user.uid,
      email: userCredential.user.email,
      displayName: userCredential.user.displayName || email.split('@')[0],
      role: 'admin',
    };
    setUser(userData);
    setRole('admin');
    localStorage.setItem('auth_user', JSON.stringify(userData));
    return userData;
  };

  // Instant Demo Administrator Login (for academic evaluators & portfolio testing)
  const loginDemo = () => {
    const demoUser = {
      uid: 'admin-mock-uid-001',
      email: 'admin@attendance.college.edu',
      displayName: 'Dean of Academic Affairs',
      role: 'admin',
    };
    localStorage.setItem('auth_token', 'mock-admin-token');
    localStorage.setItem('auth_user', JSON.stringify(demoUser));
    setUser(demoUser);
    setRole('admin');
    return demoUser;
  };

  const logout = async () => {
    if (auth && auth.currentUser) {
      try {
        await fbSignOut(auth);
      } catch (err) {
        console.warn('Firebase signout error:', err);
      }
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
    setRole(null);
  };

  const value = {
    user,
    role,
    loading,
    isAuthenticated: !!user,
    login,
    loginDemo,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
