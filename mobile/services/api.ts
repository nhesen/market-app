import * as SecureStore from "expo-secure-store";

export const apiRoot =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const serverRoot = apiRoot.replace(/\/api\/v1\/?$/, "");

export type User = {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  language: "az" | "en";
  role: string;
  organisation_id?: string;
  selected_organisation_id?: string;
  profile_image_url?: string;
  preferred_branch_id?: string;
};
export type Branch = {
  id: string;
  name: string;
  address: string;
  hours: string;
  distance_km: number;
  is_open: boolean;
  image_url?: string;
  services?: string[];
};
export type Product = {
  id: string;
  name: string;
  brand: string;
  package_size?: string;
  barcode: string;
  category: string;
  price: number;
  discount_price?: number;
  image_url?: string;
  available?: boolean;
  branches?: Array<{
    branch_id: string;
    branch_name: string;
    price: number;
    previous_price?: number;
    available: boolean;
  }>;
};
export type HomeData = {
  user: User;
  organisation?: { id: string; name: string };
  selected_branch?: Branch;
  unread_notifications: number;
  news: any[];
  products: Product[];
  discounts: Product[];
  branches: Branch[];
  loyalty: any;
  reports: any[];
};

async function fallbackError(kind: "request" | "network" = "request") {
  const language = await SecureStore.getItemAsync("language");
  if (language === "en")
    return kind === "network"
      ? "Could not connect to the server"
      : "The request could not be completed";
  return kind === "network"
    ? "Serverlə əlaqə yaratmaq mümkün olmadı"
    : "Sorğu tamamlanmadı";
}
async function parseError(response: Response) {
  try {
    const body = await response.json();
    return typeof body.detail === "string"
      ? body.detail
      : await fallbackError();
  } catch {
    return fallbackError("network");
  }
}
const SESSION_VERSION = "2";
async function storeSession(data: any) {
  await SecureStore.setItemAsync("token", data.access_token);
  await SecureStore.setItemAsync("session_role", data.user.role);
  await SecureStore.setItemAsync("session_version", SESSION_VERSION);
  if (data.refresh_token)
    await SecureStore.setItemAsync("refresh_token", data.refresh_token);
  return data.user as User;
}
export async function hasSession() {
  return Boolean(await SecureStore.getItemAsync("token"));
}

export async function restoreSession() {
  if ((await SecureStore.getItemAsync("session_version")) !== SESSION_VERSION) {
    await clearSession();
    return null;
  }
  if (!(await hasSession())) return null;
  try {
    return await request<User>("/auth/me");
  } catch {
    await clearSession();
    return null;
  }
}

export async function request<T>(
  path: string,
  init?: RequestInit,
  retry = true,
): Promise<T> {
  const token = await SecureStore.getItemAsync("token");
  if (!token) throw new Error("LOGIN_REQUIRED");
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (!(init?.body instanceof FormData))
    headers["Content-Type"] = "application/json";
  const response = await fetch(apiRoot + path, { ...init, headers });
  if (response.status === 401 && retry) {
    const refresh = await SecureStore.getItemAsync("refresh_token");
    if (refresh) {
      const renewed = await fetch(apiRoot + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (renewed.ok) {
        await storeSession(await renewed.json());
        return request<T>(path, init, false);
      }
    }
    await clearSession();
    throw new Error("LOGIN_REQUIRED");
  }
  if (!response.ok) throw new Error(await parseError(response));
  return response.status === 204 ? (undefined as T) : response.json();
}
export async function login(email: string, password: string) {
  const response = await fetch(apiRoot + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return storeSession(await response.json());
}
export async function register(body: unknown) {
  const response = await fetch(apiRoot + "/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return storeSession(await response.json());
}
export async function forgotPassword(email: string) {
  const response = await fetch(apiRoot + "/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
export async function clearSession() {
  await Promise.all([
    SecureStore.deleteItemAsync("token"),
    SecureStore.deleteItemAsync("refresh_token"),
    SecureStore.deleteItemAsync("session_role"),
    SecureStore.deleteItemAsync("session_version"),
    SecureStore.deleteItemAsync("selected_branch_id"),
    SecureStore.deleteItemAsync("selected_market_id"),
  ]);
}
export async function sessionRole() {
  return SecureStore.getItemAsync("session_role");
}
export async function logout() {
  try {
    await request("/auth/logout", { method: "POST" }, false);
  } finally {
    await clearSession();
  }
}
export async function selectedBranchId() {
  return SecureStore.getItemAsync("selected_branch_id");
}
export async function selectBranch(id: string) {
  await request("/profile/preferred-branch", {
    method: "PATCH",
    body: JSON.stringify({ branch_id: id }),
  });
  await SecureStore.setItemAsync("selected_branch_id", id);
}
export async function selectMarket(id: string) {
  const result = await request<{ organisation_id: string; name: string }>(
    "/profile/preferred-market",
    { method: "PATCH", body: JSON.stringify({ organisation_id: id }) },
  );
  await Promise.all([
    SecureStore.setItemAsync("selected_market_id", id),
    SecureStore.deleteItemAsync("selected_branch_id"),
  ]);
  return result;
}
export async function selectedMarketId() {
  return SecureStore.getItemAsync("selected_market_id");
}
export async function recentSearches() {
  try {
    return JSON.parse(
      (await SecureStore.getItemAsync("recent_searches")) ?? "[]",
    ) as string[];
  } catch {
    return [];
  }
}
export async function rememberSearch(value: string) {
  const term = value.trim();
  if (!term) return;
  const items = await recentSearches();
  await SecureStore.setItemAsync(
    "recent_searches",
    JSON.stringify(
      [
        term,
        ...items.filter((x) => x.toLowerCase() !== term.toLowerCase()),
      ].slice(0, 8),
    ),
  );
}
export async function clearRecentSearches() {
  await SecureStore.deleteItemAsync("recent_searches");
}
export function mediaUrl(value?: string) {
  if (!value) return undefined;
  if (/^https?:/.test(value)) return value;
  return serverRoot + value;
}

export const api = {
  home: async () => {
    const id = await selectedBranchId();
    return request<HomeData>(`/home${id ? `?branch_id=${id}` : ""}`);
  },
  reports: () => request<any[]>("/reports"),
  report: (id: string) => request<any>(`/reports/${id}`),
  branches: () => request<Branch[]>("/branches"),
  organisations: async () => {
    const r = await fetch(apiRoot + "/organisations");
    if (!r.ok) throw new Error(await parseError(r));
    return r.json();
  },
  reviewReport: (body: unknown) =>
    request<any>("/reports/ai-review", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createReport: (body: unknown) =>
    request<any>("/reports", { method: "POST", body: JSON.stringify(body) }),
};
export const customerApi = {
  products: (
    params: {
      q?: string;
      category?: string;
      sort?: string;
      branchId?: string;
    } = {},
  ) => {
    const q = new URLSearchParams();
    if (params.q) q.set("q", params.q);
    if (params.category) q.set("category", params.category);
    if (params.sort) q.set("sort", params.sort);
    if (params.branchId) q.set("branch_id", params.branchId);
    return request<Product[]>(`/products?${q}`);
  },
  categories: () => request<string[]>("/product-categories"),
  product: (id: string) => request<Product>(`/products/${id}`),
  barcode: (code: string) => request<Product>(`/products/barcode/${code}`),
  branch: (id: string) => request<Branch>(`/branches/${id}`),
  discounts: (category = "") =>
    request<any[]>(
      `/discounts${category ? `?category=${encodeURIComponent(category)}` : ""}`,
    ),
  discount: (id: string) => request<any>(`/discounts/${id}`),
  favourites: () => request<Product[]>("/favourites/products"),
  favourite: (id: string) =>
    request(`/favourites/products/${id}`, { method: "POST" }),
  unfavourite: (id: string) =>
    request(`/favourites/products/${id}`, { method: "DELETE" }),
  favouriteBranches: () => request<Branch[]>("/favourites/branches"),
  favouriteBranch: (id: string) =>
    request(`/favourites/branches/${id}`, { method: "POST" }),
  unfavouriteBranch: (id: string) =>
    request(`/favourites/branches/${id}`, { method: "DELETE" }),
  campaignFavourites: () => request<string[]>("/favourites/campaigns"),
  favouriteCampaign: (id: string) =>
    request(`/favourites/campaigns/${id}`, { method: "POST" }),
  unfavouriteCampaign: (id: string) =>
    request(`/favourites/campaigns/${id}`, { method: "DELETE" }),
  news: () => request<any[]>("/news"),
  newsDetail: (id: string) => request<any>(`/news/${id}`),
  suggestions: () => request<any[]>("/suggestions"),
  suggestion: (id: string) => request<any>(`/suggestions/${id}`),
  createSuggestion: (body: unknown) =>
    request<any>("/suggestions", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  notifications: () => request<any[]>("/notifications"),
  readNotification: (id: string) =>
    request(`/notifications/${id}/read`, { method: "PATCH" }),
  readAllNotifications: () =>
    request<{ updated: number }>("/notifications/read-all", {
      method: "PATCH",
    }),
  me: () => request<User>("/auth/me"),
  market: () => request<{ id: string; name: string }>("/market"),
  updateProfile: (body: unknown) =>
    request<User>("/profile", { method: "PATCH", body: JSON.stringify(body) }),
  deleteRequest: (reason: string) =>
    request("/profile/delete-request", {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  preferences: () => request<Record<string, boolean>>("/profile/preferences"),
  updatePreferences: (body: Record<string, boolean>) =>
    request<Record<string, boolean>>("/profile/preferences", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  cards: () => request<any[]>("/loyalty/cards"),
  transactions: (id: string) =>
    request<any[]>(`/loyalty/cards/${id}/transactions`),
  offers: () => request<any[]>("/loyalty/offers"),
  offer: (id: string) => request<any>(`/loyalty/offers/${id}`),
};
export async function uploadAsset(
  uri: string,
  type = "image/jpeg",
  onProgress?: (value: number) => void,
) {
  const token = await SecureStore.getItemAsync("token"),
    body = new FormData(),
    extension =
      type === "video/mp4" ? "mp4" : type === "image/png" ? "png" : "jpg";
  body.append("file", {
    uri,
    name: `baxish-evidence.${extension}`,
    type,
  } as any);
  return new Promise<any>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", apiRoot + "/uploads");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total);
    };
    xhr.onerror = async () => reject(new Error(await fallbackError("network")));
    xhr.onload = async () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(1);
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error(await fallbackError()));
        }
      } else {
        try {
          const body = JSON.parse(xhr.responseText);
          reject(new Error(body.detail ?? (await fallbackError())));
        } catch {
          reject(new Error(await fallbackError()));
        }
      }
    };
    xhr.send(body);
  });
}
export async function uploadImage(uri: string) {
  const token = await SecureStore.getItemAsync("token");
  const body = new FormData();
  body.append("file", { uri, name: "capture.jpg", type: "image/jpeg" } as any);
  const response = await fetch(apiRoot + "/ocr/image", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
export const staffApi = {
  audits: () => request<any[]>("/staff/audits"),
  audit: (id: string) => request<any>(`/staff/audits/${id}`),
  dashboard: () => request<any>("/staff/dashboard"),
  quality: () => request<any>("/staff/quality-summary"),
  productByBarcode: (barcode: string) =>
    request<any>(`/staff/products/barcode/${encodeURIComponent(barcode)}`),
  reAudits: () => request<any[]>("/staff/re-audits"),
  completeReAudit: (id: string, condition: string) =>
    request<any>(`/staff/re-audits/${id}/complete`, {
      method: "POST",
      body: JSON.stringify({ condition }),
    }),
  start: (id: string) =>
    request<any>(`/staff/audits/${id}/start`, { method: "POST" }),
  addItem: (id: string, body: unknown) =>
    request<any>(`/staff/audits/${id}/items`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  complete: (id: string) =>
    request<any>(`/staff/audits/${id}/complete`, { method: "POST" }),
};
export const adminApi = {
  dashboard: () => request<any>("/admin/dashboard"),
  incidents: () => request<any[]>("/admin/incidents"),
  reports: () => request<any[]>("/admin/reports"),
  audits: () => request<any[]>("/admin/audits"),
  network: () => request<any[]>("/admin/network-analytics"),
  analytics: () => request<any>("/admin/operational-analytics"),
  platformHealth: () => request<any>("/platform/health"),
  organisations: () => request<any[]>("/platform/organisations"),
  tenantUsage: () => request<any[]>("/platform/tenant-usage"),
};
