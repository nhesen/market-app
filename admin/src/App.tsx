import { Navigate, Route, Routes } from "react-router-dom";
import {
  BarChart3,
  Building2,
  Camera,
  ClipboardCheck,
  FileText,
  Gauge,
  HeartPulse,
  LayoutDashboard,
  ListChecks,
  Logs,
  PackageSearch,
  Repeat,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Login } from "./components/Login";
import {
  BranchLayout,
  HeadLayout,
  NavItem,
  PlatformLayout,
} from "./layouts/RoleLayout";
import { session } from "./services/api";
import * as Branch from "./features/branch/pages";
import * as AuditManagement from "./features/branch/auditManagement";
import * as Head from "./features/head/pages";
import * as ExtendedHead from "./features/head/extendedContent";
import * as Platform from "./features/platform/pages";

const branchNav: NavItem[] = [
  { to: "/branch", label: "Dashboard", icon: <LayoutDashboard /> },
  { to: "/branch/reports", label: "Reportlar", icon: <FileText /> },
  { to: "/branch/suggestions", label: "Təkliflər", icon: <BarChart3 /> },
  { to: "/branch/incidents", label: "Incidentlər", icon: <ListChecks /> },
  { to: "/branch/audits", label: "Staff auditləri", icon: <ClipboardCheck /> },
  {
    to: "/branch/audit-templates",
    label: "Audit şablonları",
    icon: <ClipboardCheck />,
  },
  {
    to: "/branch/quality-flags",
    label: "Keyfiyyət flagları",
    icon: <ShieldCheck />,
  },
  { to: "/branch/re-audits", label: "Təkrar audit", icon: <Repeat /> },
  { to: "/branch/cameras", label: "Kameralar", icon: <Camera /> },
  { to: "/branch/camera-events", label: "Kamera hadisələri", icon: <Camera /> },
  { to: "/branch/staff", label: "Filial əməkdaşları", icon: <Users /> },
  { to: "/branch/settings", label: "Filial ayarları", icon: <Settings /> },
];
const headNav: NavItem[] = [
  { to: "/head", label: "Şəbəkə dashboard", icon: <LayoutDashboard /> },
  {
    to: "/head/branches/compare",
    label: "Filial müqayisəsi",
    icon: <Building2 />,
  },
  {
    to: "/head/analytics",
    label: "Əməliyyat analitikası",
    icon: <BarChart3 />,
  },
  { to: "/head/scores", label: "Score sıralaması", icon: <Gauge /> },
  { to: "/head/incidents", label: "Bütün incidentlər", icon: <ListChecks /> },
  { to: "/head/content", label: "Kontent xülasəsi", icon: <PackageSearch /> },
  { to: "/head/news", label: "Xəbərlər", icon: <FileText /> },
  { to: "/head/products", label: "Məhsullar", icon: <PackageSearch /> },
  { to: "/head/categories", label: "Kateqoriyalar", icon: <PackageSearch /> },
  { to: "/head/prices", label: "Filial qiymətləri", icon: <PackageSearch /> },
  { to: "/head/campaigns", label: "Kampaniyalar", icon: <BarChart3 /> },
  {
    to: "/head/loyalty-offers",
    label: "Loyalty təklifləri",
    icon: <BarChart3 />,
  },
  { to: "/head/branches", label: "Filiallar", icon: <Building2 /> },
  { to: "/head/staff", label: "Staff overview", icon: <Users /> },
  { to: "/head/cameras", label: "Kamera overview", icon: <Camera /> },
];
const platformNav: NavItem[] = [
  { to: "/platform", label: "Dashboard", icon: <LayoutDashboard /> },
  {
    to: "/platform/organisations",
    label: "Organisation-lar",
    icon: <Building2 />,
  },
  { to: "/platform/branches/new", label: "Filial yarat", icon: <Building2 /> },
  { to: "/platform/admins", label: "Administratorlar", icon: <Users /> },
  { to: "/platform/modules", label: "Modullar", icon: <Settings /> },
  {
    to: "/platform/health/system",
    label: "System health",
    icon: <HeartPulse />,
  },
  {
    to: "/platform/health/database",
    label: "Database health",
    icon: <HeartPulse />,
  },
  { to: "/platform/health/vision", label: "Vision health", icon: <Camera /> },
  { to: "/platform/storage", label: "Storage usage", icon: <Gauge /> },
  { to: "/platform/usage", label: "Tenant usage", icon: <BarChart3 /> },
  { to: "/platform/settings", label: "System settings", icon: <Settings /> },
  { to: "/platform/logs", label: "Loglar", icon: <Logs /> },
  { to: "/platform/demo-reset", label: "Demo reset", icon: <Repeat /> },
];

export default function App() {
  const user = session.user();
  if (!session.hasToken() || !user) return <Login />;
  const home =
    user.role === "BRANCH_ADMIN"
      ? "/branch"
      : user.role === "HEAD_OFFICE_ADMIN"
        ? "/head"
        : "/platform";
  return (
    <Routes>
      <Route path="/" element={<Navigate to={home} replace />} />
      {user.role === "BRANCH_ADMIN" ? (
        <Route path="branch" element={<BranchLayout items={branchNav} />}>
          <Route index element={<Branch.BranchDashboard />} />
          <Route path="reports" element={<Branch.ReportsPage />} />
          <Route path="reports/:id" element={<Branch.ReportDetailPage />} />
          <Route path="suggestions" element={<Branch.SuggestionsPage />} />
          <Route path="incidents" element={<Branch.IncidentsPage />} />
          <Route path="incidents/:id" element={<Branch.IncidentDetailPage />} />
          <Route
            path="audits"
            element={<AuditManagement.AuditManagementPage />}
          />
          <Route
            path="audits/:id"
            element={<AuditManagement.AuditDetailPage />}
          />
          <Route
            path="audit-templates"
            element={<AuditManagement.AuditTemplatesPage />}
          />
          <Route path="quality-flags" element={<Branch.QualityFlagsPage />} />
          <Route
            path="re-audits"
            element={<AuditManagement.ReAuditManagementPage />}
          />
          <Route path="cameras" element={<Branch.CamerasPage />} />
          <Route path="camera-events" element={<Branch.CameraEventsPage />} />
          <Route path="staff" element={<Branch.BranchStaffPage />} />
          <Route
            path="staff/:id"
            element={<AuditManagement.StaffQualityDetailPage />}
          />
          <Route path="settings" element={<Branch.BranchSettingsPage />} />
        </Route>
      ) : null}
      {user.role === "HEAD_OFFICE_ADMIN" ? (
        <Route path="head" element={<HeadLayout items={headNav} />}>
          <Route index element={<Head.NetworkDashboard />} />
          <Route
            path="branches/compare"
            element={<Head.BranchComparisonPage />}
          />
          <Route path="analytics" element={<Head.OperationalAnalyticsPage />} />
          <Route path="scores" element={<Head.ScoreRankingPage />} />
          <Route path="incidents" element={<Branch.IncidentsPage all />} />
          <Route
            path="incidents/:id"
            element={<Branch.IncidentDetailPage base="/head" />}
          />
          <Route path="content" element={<Head.ContentOverviewPage />} />
          <Route path="news" element={<Head.NewsPage />} />
          <Route path="products" element={<Head.ProductsPage />} />
          <Route path="categories" element={<Head.CategoriesPage />} />
          <Route path="prices" element={<Head.PricesPage />} />
          <Route path="campaigns" element={<Head.CampaignsPage />} />
          <Route
            path="campaigns/:id/products"
            element={<ExtendedHead.CampaignProductsPage />}
          />
          <Route
            path="loyalty-offers"
            element={<ExtendedHead.LoyaltyOffersPage />}
          />
          <Route path="branches" element={<Head.BranchesPage />} />
          <Route path="staff" element={<Head.StaffOverviewPage />} />
          <Route path="cameras" element={<Head.CameraOverviewPage />} />
        </Route>
      ) : null}
      {user.role === "PLATFORM_ADMIN" ? (
        <Route path="platform" element={<PlatformLayout items={platformNav} />}>
          <Route index element={<Platform.PlatformDashboard />} />
          <Route
            path="organisations"
            element={<Platform.OrganisationsPage />}
          />
          <Route
            path="organisations/:id"
            element={<Platform.OrganisationDetailPage />}
          />
          <Route
            path="branches/new"
            element={<Platform.BranchCreationPage />}
          />
          <Route path="admins" element={<Platform.AdminAccountsPage />} />
          <Route path="modules" element={<Platform.ModulesPage />} />
          <Route path="health/system" element={<Platform.SystemHealthPage />} />
          <Route
            path="health/database"
            element={<Platform.DatabaseHealthPage />}
          />
          <Route path="health/vision" element={<Platform.VisionHealthPage />} />
          <Route path="storage" element={<Platform.StorageUsagePage />} />
          <Route path="usage" element={<Platform.TenantUsagePage />} />
          <Route path="settings" element={<Platform.SystemSettingsPage />} />
          <Route path="logs" element={<Platform.LogsPage />} />
          <Route path="demo-reset" element={<Platform.DemoResetPage />} />
        </Route>
      ) : null}
      <Route path="*" element={<Navigate to={home} replace />} />
    </Routes>
  );
}
