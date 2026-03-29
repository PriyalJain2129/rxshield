/** Same-origin in dev (Vite proxy) so Flask session cookies work; direct URL for production builds. */
const API_BASE_URL = import.meta.env.DEV ? "/api" : "http://127.0.0.1:5000/api";

const fetchOpts: RequestInit = { credentials: "include" };

export type User = { name: string; email?: string };

// --- 1. AUTHENTICATION ---
export const login = async (email: string, password: string): Promise<User> => {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    ...fetchOpts,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error((data && data.message) || "Login failed");
  }
  const name = data.user?.name ?? "";
  return { name, email: email.trim() };
};

export const signup = async (userData: any) => {
  const response = await fetch(`${API_BASE_URL}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userData),
    ...fetchOpts,
  });
  return response.json();
};

export const logout = async () => {
  const response = await fetch(`${API_BASE_URL}/logout`, { method: "POST", ...fetchOpts });
  return response.json();
};

export const getCurrentUser = async (): Promise<User | null> => {
  const response = await fetch(`${API_BASE_URL}/me`, { ...fetchOpts });
  if (!response.ok) return null;
  return response.json();
};

// --- 2. DATA RETRIEVAL (Updated for UI Fixes) ---
export const addPatient = async (patientData: any) => {
  const response = await fetch(`${API_BASE_URL}/add-patient`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patientData),
    ...fetchOpts,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error((data && data.message) || "Failed to register patient");
  }
  return data;
};

/** Pass-through list from GET /api/patients (ordered newest-first server-side). No filtering. */
export const getPatients = async () => {
  const response = await fetch(`${API_BASE_URL}/patients`, { ...fetchOpts });
  const data = await response.json();
  return Array.isArray(data) ? data : [];
};

export const getDrugs = async () => {
  const response = await fetch(`${API_BASE_URL}/drugs`, { ...fetchOpts });
  return response.json();
};

// --- 3. SAFETY ENGINE & ORDERS ---
export const checkOrder = async (patientId: string, drugName: string, dosage: number) => {
  const response = await fetch(`${API_BASE_URL}/check-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id: patientId, drug_name: drugName, dosage: dosage }),
    ...fetchOpts,
  });
  const data = await response.json();
  
  // Ensure we check for existence of data.alerts before mapping
  if (!data.alerts) return [];
  
  return data.alerts.map((a: any) => ({
    rule: a.rule,
    status: (a.type || "warning").toLowerCase() as "danger" | "warning",
    message: a.msg
  }));
};

export const createOrder = async (orderData: any) => {
  const response = await fetch(`${API_BASE_URL}/create-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderData),
    ...fetchOpts,
  });
  return response.json();
};

export const getOrders = async () => {
  const response = await fetch(`${API_BASE_URL}/orders`, { ...fetchOpts });
  return response.json();
};

export const getAlerts = async () => {
  const response = await fetch(`${API_BASE_URL}/alerts`, { ...fetchOpts });
  return response.json();
};