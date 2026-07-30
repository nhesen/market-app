export type Role = "BRANCH_ADMIN" | "HEAD_OFFICE_ADMIN" | "PLATFORM_ADMIN";
export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  organisation_id: string | null;
  branch_id: string | null;
};
export type Incident = {
  id: string;
  branch_id: string;
  source: string;
  category: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  responsible_department?: string;
  assigned_staff_id?: string;
  assigned_admin_id?: string;
  sla_due_at?: string;
  is_overdue: boolean;
  rejection_reason?: string;
  resolution_reason?: string;
  reopening_reason?: string;
  resolution_actor_type?: string;
  created_at: string;
  allowed_transitions: string[];
  history: Array<{
    from_status?: string;
    status: string;
    note: string;
    internal_note?: string;
    customer_note?: string;
    actor_type: string;
    created_at: string;
  }>;
  notes: Array<{
    id: string;
    visibility: string;
    note: string;
    created_at: string;
  }>;
  attachments: Array<{ url: string; mime_type: string; name: string }>;
};
const root = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
export const mediaUrl = (value?: string) =>
  value
    ? /^https?:/.test(value)
      ? value
      : root.replace(/\/api\/v1\/?$/, "") + value
    : "";
let token = localStorage.getItem("martiq_admin_token") ?? "";
let refreshToken = localStorage.getItem("martiq_admin_refresh") ?? "";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response = await fetch(root + path, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (response.status === 401 && refreshToken && !path.startsWith("/auth/")) {
    const renewed = await fetch(root + "/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (renewed.ok) {
      const data = await renewed.json();
      token = data.access_token;
      refreshToken = data.refresh_token ?? refreshToken;
      localStorage.setItem("martiq_admin_token", token);
      localStorage.setItem("martiq_admin_refresh", refreshToken);
      response = await fetch(root + path, {
        ...init,
        headers: {
          ...(init.body ? { "Content-Type": "application/json" } : {}),
          Authorization: `Bearer ${token}`,
          ...init.headers,
        },
      });
    }
  }
  if (response.status === 401) {
    session.logout();
    location.reload();
    throw new Error("Sessiya bitib");
  }
  if (response.status === 403)
    throw new Error("Bu əməliyyat üçün icazəniz yoxdur");
  if (!response.ok) {
    let message = "Sorğu tamamlanmadı";
    try {
      message = (await response.json()).detail ?? message;
    } catch {
      message = `Sorğu tamamlanmadı (${response.status})`;
    }
    throw new Error(message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
});
export const session = {
  login: async (email: string, password: string) => {
    const data = await request<{
      access_token: string;
      refresh_token: string;
      user: AdminUser;
    }>("/auth/login", json("POST", { email, password }));
    if (
      !["BRANCH_ADMIN", "HEAD_OFFICE_ADMIN", "PLATFORM_ADMIN"].includes(
        data.user.role,
      )
    )
      throw new Error("Bu hesab admin panel üçün deyil");
    token = data.access_token;
    refreshToken = data.refresh_token;
    localStorage.setItem("martiq_admin_token", token);
    localStorage.setItem("martiq_admin_refresh", refreshToken);
    localStorage.setItem("martiq_admin_user", JSON.stringify(data.user));
    return data.user;
  },
  user: () => {
    try {
      return JSON.parse(
        localStorage.getItem("martiq_admin_user") ?? "null",
      ) as AdminUser | null;
    } catch {
      return null;
    }
  },
  hasToken: () => Boolean(token),
  logout: () => {
    token = "";
    refreshToken = "";
    localStorage.removeItem("martiq_admin_token");
    localStorage.removeItem("martiq_admin_refresh");
    localStorage.removeItem("martiq_admin_user");
  },
};
export const operationsApi = {
  analytics: (params: Record<string, string> = {}) =>
    request<any>(`/admin/operational-analytics?${new URLSearchParams(params)}`),
  dashboard: () => request<any>("/admin/dashboard"),
  reports: (params: Record<string, string> = {}) =>
    request<any[]>(`/admin/reports?${new URLSearchParams(params)}`),
  report: (id: string) => request<any>(`/admin/reports/${id}`),
  suggestions: () => request<any[]>("/admin/suggestions"),
  updateSuggestion: (id: string, status: string, admin_note: string) =>
    request<any>(
      `/admin/suggestions/${id}`,
      json("PATCH", { status, admin_note }),
    ),
  incidents: (params: Record<string, string> = {}) =>
    request<Incident[]>(`/admin/incidents?${new URLSearchParams(params)}`),
  updateIncident: (id: string, body: any) =>
    request<Incident>(`/admin/incidents/${id}`, json("PATCH", body)),
  addIncidentNote: (id: string, note: string, customer_visible: boolean) =>
    request<any>(
      `/admin/incidents/${id}/notes`,
      json("POST", { note, customer_visible }),
    ),
  audits: () => request<any[]>("/admin/audits"),
  audit: (id: string) => request<any>(`/admin/audits/${id}`),
  templates: () => request<any[]>("/admin/audit-templates"),
  createTemplate: (body: any) =>
    request<any>("/admin/audit-templates", json("POST", body)),
  updateTemplate: (id: string, body: any) =>
    request<any>(`/admin/audit-templates/${id}`, json("PUT", body)),
  assignAudit: (body: any) =>
    request<any>("/admin/audit-tasks", json("POST", body)),
  flags: (params: Record<string, string> = {}) =>
    request<any[]>(`/admin/audit-quality-flags?${new URLSearchParams(params)}`),
  resolveFlag: (id: string, resolved: boolean) =>
    request<any>(`/admin/audit-quality-flags/${id}?resolved=${resolved}`, {
      method: "PATCH",
    }),
  reaudits: () => request<any[]>("/admin/re-audits"),
  createReaudit: (body: any) =>
    request<any>("/admin/re-audits", json("POST", body)),
  staff: () => request<any[]>("/admin/staff"),
  staffQuality: (id: string) =>
    request<any>(`/admin/staff/${id}/quality-score`),
  branches: () => request<any[]>("/admin/branches"),
  updateBranch: (id: string, body: any) =>
    request<any>(`/admin/branches/${id}`, json("PATCH", body)),
  cameras: () => request<any[]>("/admin/cameras"),
  cameraRules: () => request<any[]>("/admin/camera-rules"),
  updateCameraRule: (id: string, body: any) =>
    request<any>(`/admin/camera-rules/${id}`, json("PATCH", body)),
  cameraEvents: () => request<any[]>("/admin/camera-events"),
  falseAlert: (id: string) =>
    request<any>(`/admin/camera-events/${id}/false-alert`, json("POST", {})),
  visionHealth: () => request<any[]>("/admin/vision-health"),
};
export const contentApi = {
  products: () => request<any[]>("/admin/products"),
  createProduct: (body: any) =>
    request<any>("/admin/products", json("POST", body)),
  updateProduct: (id: string, body: any) =>
    request<any>(`/admin/products/${id}`, json("PATCH", body)),
  deleteProduct: (id: string) =>
    request<void>(`/admin/products/${id}`, { method: "DELETE" }),
  categories: () => request<any[]>("/admin/categories"),
  createCategory: (name: string) =>
    request<any>("/admin/categories", json("POST", { name })),
  deleteCategory: (id: string) =>
    request<void>(`/admin/categories/${id}`, { method: "DELETE" }),
  prices: () => request<any[]>("/admin/prices"),
  setPrice: (body: any) => request<any>("/admin/prices", json("POST", body)),
  deletePrice: (id: string) =>
    request<void>(`/admin/prices/${id}`, { method: "DELETE" }),
  news: () => request<any[]>("/admin/news"),
  createNews: (body: any) => request<any>("/admin/news", json("POST", body)),
  updateNews: (id: string, body: any) =>
    request<any>(`/admin/news/${id}`, json("PATCH", body)),
  deleteNews: (id: string) =>
    request<void>(`/admin/news/${id}`, { method: "DELETE" }),
  campaigns: () => request<any[]>("/admin/campaigns"),
  createCampaign: (body: any) =>
    request<any>("/admin/campaigns", json("POST", body)),
  updateCampaign: (id: string, body: any) =>
    request<any>(`/admin/campaigns/${id}`, json("PATCH", body)),
  deleteCampaign: (id: string) =>
    request<void>(`/admin/campaigns/${id}`, { method: "DELETE" }),
  campaignProducts: (id: string) =>
    request<any[]>(`/admin/campaigns/${id}/products`),
  addCampaignProduct: (id: string, body: any) =>
    request<any>(`/admin/campaigns/${id}/products`, json("POST", body)),
  deleteCampaignProduct: (id: string) =>
    request<void>(`/admin/campaign-products/${id}`, { method: "DELETE" }),
  loyaltyOffers: () => request<any[]>("/admin/loyalty-offers"),
  createLoyaltyOffer: (body: any) =>
    request<any>("/admin/loyalty-offers", json("POST", body)),
  updateLoyaltyOffer: (id: string, body: any) =>
    request<any>(`/admin/loyalty-offers/${id}`, json("PUT", body)),
  deleteLoyaltyOffer: (id: string) =>
    request<void>(`/admin/loyalty-offers/${id}`, { method: "DELETE" }),
  logs: () => request<any[]>("/admin/logs"),
  network: () => request<any[]>("/admin/network-analytics"),
};
export const platformApi = {
  organisations: () => request<any[]>("/platform/organisations"),
  organisation: (id: string) => request<any>(`/platform/organisations/${id}`),
  createOrganisation: (name: string) =>
    request<any>("/platform/organisations", json("POST", { name })),
  updateOrganisation: (id: string, body: any) =>
    request<any>(`/platform/organisations/${id}`, json("PATCH", body)),
  createBranch: (body: any) =>
    request<any>("/platform/branches", json("POST", body)),
  admins: () => request<any[]>("/platform/admins"),
  createAdmin: (body: any) =>
    request<any>("/platform/admins", json("POST", body)),
  updateAdmin: (id: string, body: any) =>
    request<any>(`/platform/admins/${id}`, json("PATCH", body)),
  modules: () => request<any[]>("/platform/modules"),
  setModule: (body: any) =>
    request<any>("/platform/modules", json("PUT", body)),
  health: () => request<any>("/platform/health"),
  usage: () => request<any>("/platform/usage"),
  tenantUsage: () => request<any[]>("/platform/tenant-usage"),
  settings: () => request<any[]>("/platform/settings"),
  setSetting: (body: any) =>
    request<any>("/platform/settings", json("PUT", body)),
  logs: () => request<any[]>("/admin/logs"),
  demoReset: () =>
    request<any>(
      "/platform/demo-reset",
      json("POST", { confirmation: "RESET_DEMO" }),
    ),
};
