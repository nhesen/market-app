import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { operationsApi, platformApi } from "../../services/api";
import {
  DataTable,
  DetailLink,
  Loading,
  Metric,
  Modal,
  Page,
  StatusBadge,
} from "../../components/ui";

const useData = (key: string, fn: () => Promise<any>) =>
  useQuery({ queryKey: [key], queryFn: fn });
export function PlatformDashboard() {
  const usage = useData("usage", platformApi.usage),
    health = useData("health", platformApi.health);
  return (
    <Page
      title="Platform dashboard"
      subtitle="Cross-tenant sistem, istifadə və sağlamlıq görünüşü"
    >
      <div className="grid">
        <Metric label="Organisation" value={usage.data?.organisations ?? 0} />
        <Metric label="Filial" value={usage.data?.branches ?? 0} />
        <Metric label="İstifadəçi" value={usage.data?.users ?? 0} />
        <Metric label="Incident" value={usage.data?.incidents ?? 0} />
      </div>
      <div className="grid spaced">
        <Metric label="Sistem" value={health.data?.system.status ?? "—"} />
        <Metric label="Database" value={health.data?.database.status ?? "—"} />
        <Metric label="Vision" value={health.data?.vision.status ?? "—"} />
        <Metric
          label="Storage"
          value={`${health.data?.storage.megabytes ?? 0} MB`}
        />
      </div>
    </Page>
  );
}
export function OrganisationsPage() {
  const q = useData("organisations", platformApi.organisations),
    client = useQueryClient(),
    [name, setName] = useState(""),
    mutation = useMutation({
      mutationFn: () => platformApi.createOrganisation(name),
      onSuccess: () => {
        setName("");
        client.invalidateQueries({ queryKey: ["organisations"] });
      },
    });
  return (
    <Page title="Organisation-lar" subtitle="Tenant yaradılması və detalları">
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <h2>Yeni organisation</h2>
          <label className="field">
            Ad
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <button className="btn">Yarat</button>
        </form>
        <section className="card">
          <DataTable
            rows={q.data ?? []}
            columns={[
              {
                key: "name",
                label: "Organisation",
                render: (r) => (
                  <DetailLink
                    to={`/platform/organisations/${r.id}`}
                    label={r.name}
                  />
                ),
              },
              {
                key: "created_at",
                label: "Yaradılıb",
                render: (r) =>
                  new Date(r.created_at).toLocaleDateString("az-AZ"),
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => <ManageOrganisation item={r} />,
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function OrganisationDetailPage() {
  const { id } = useParams(),
    q = useQuery({
      queryKey: ["organisation", id],
      queryFn: () => platformApi.organisation(id!),
    });
  if (q.isLoading) return <Loading />;
  return (
    <Page
      title={q.data.name}
      subtitle="Organisation filialları və administratorları"
    >
      <div className="content">
        <section className="card">
          <h2>Filiallar</h2>
          <DataTable
            rows={q.data.branches}
            columns={[
              { key: "name", label: "Filial" },
              { key: "address", label: "Ünvan" },
              { key: "hours", label: "Saat" },
            ]}
          />
        </section>
        <section className="card">
          <h2>Administratorlar</h2>
          <DataTable
            rows={q.data.admins}
            columns={[
              { key: "full_name", label: "Ad" },
              { key: "email", label: "E-poçt" },
              {
                key: "role",
                label: "Rol",
                render: (r) => <StatusBadge value={r.role} />,
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function BranchCreationPage() {
  const orgs = useData("organisations", platformApi.organisations),
    [form, setForm] = useState({
      organisation_id: "",
      name: "",
      address: "",
      hours: "08:00–23:00",
    }),
    mutation = useMutation({
      mutationFn: () => platformApi.createBranch(form),
    });
  return (
    <Page title="Filial yarat" subtitle="Seçilmiş tenant daxilində yeni filial">
      <form
        className="card form narrow"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <Select
          label="Organisation"
          value={form.organisation_id}
          options={orgs.data ?? []}
          onChange={(value) => setForm({ ...form, organisation_id: value })}
        />
        {["name", "address", "hours"].map((key) => (
          <label className="field" key={key}>
            {key}
            <input
              value={(form as any)[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </label>
        ))}
        <button className="btn">Filial yarat</button>
        {mutation.isSuccess ? (
          <p className="success">Filial yaradıldı.</p>
        ) : null}
      </form>
    </Page>
  );
}
export function AdminAccountsPage() {
  const admins = useData("admins", platformApi.admins),
    orgs = useData("organisations", platformApi.organisations),
    branches = useData("platform-branches", operationsApi.branches),
    [form, setForm] = useState<{
      organisation_id: string;
      branch_id: string | null;
      email: string;
      full_name: string;
      password: string;
      role: string;
    }>({
      organisation_id: "",
      branch_id: null,
      email: "",
      full_name: "",
      password: "Demo123!",
      role: "HEAD_OFFICE_ADMIN",
    }),
    mutation = useMutation({ mutationFn: () => platformApi.createAdmin(form) });
  const branchOptions = (branches.data ?? []).filter(
    (item: any) => item.organisation_id === form.organisation_id,
  );
  return (
    <Page
      title="Administrator hesabları"
      subtitle="Tenant və filial administratorlarının idarəsi"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <Select
            label="Organisation"
            value={form.organisation_id}
            options={orgs.data ?? []}
            onChange={(value) =>
              setForm({ ...form, organisation_id: value, branch_id: null })
            }
          />
          {["email", "full_name", "password"].map((key) => (
            <label className="field" key={key}>
              {key}
              <input
                type={key === "password" ? "password" : "text"}
                value={(form as any)[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </label>
          ))}
          <label className="field">
            Rol
            <select
              value={form.role}
              onChange={(e) =>
                setForm({ ...form, role: e.target.value, branch_id: null })
              }
            >
              <option>HEAD_OFFICE_ADMIN</option>
              <option>BRANCH_ADMIN</option>
            </select>
          </label>
          {form.role === "BRANCH_ADMIN" ? (
            <Select
              label="Filial"
              value={form.branch_id ?? ""}
              options={branchOptions}
              onChange={(value) => setForm({ ...form, branch_id: value })}
            />
          ) : null}
          <button className="btn">Hesab yarat</button>
        </form>
        <section className="card">
          <DataTable
            rows={admins.data ?? []}
            columns={[
              { key: "full_name", label: "Ad" },
              { key: "email", label: "E-poçt" },
              {
                key: "role",
                label: "Rol",
                render: (r) => <StatusBadge value={r.role} />,
              },
              {
                key: "is_active",
                label: "Aktiv",
                render: (r) => (
                  <StatusBadge value={r.is_active ? "ACTIVE" : "DISABLED"} />
                ),
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => <ManageAdmin item={r} />,
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function ModulesPage() {
  const modules = useData("modules", platformApi.modules),
    orgs = useData("organisations", platformApi.organisations),
    client = useQueryClient(),
    [form, setForm] = useState({
      organisation_id: "",
      module: "VISION",
      enabled: true,
    }),
    mutation = useMutation({
      mutationFn: () => platformApi.setModule(form),
      onSuccess: () => client.invalidateQueries({ queryKey: ["modules"] }),
    });
  return (
    <Page
      title="Modul aktivləşdirmə"
      subtitle="Tenant üzrə məhsul modullarının açılıb-bağlanması"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <Select
            label="Organisation"
            value={form.organisation_id}
            options={orgs.data ?? []}
            onChange={(value) => setForm({ ...form, organisation_id: value })}
          />
          <label className="field">
            Modul
            <select
              value={form.module}
              onChange={(e) => setForm({ ...form, module: e.target.value })}
            >
              {[
                "VISION",
                "AUDITS",
                "CUSTOMER_REPORTS",
                "LOYALTY",
                "CONTENT",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />{" "}
            Aktiv
          </label>
          <button className="btn">Tətbiq et</button>
        </form>
        <section className="card">
          <DataTable
            rows={modules.data ?? []}
            columns={[
              { key: "organisation_id", label: "Tenant" },
              { key: "module", label: "Modul" },
              {
                key: "enabled",
                label: "Status",
                render: (r) => (
                  <StatusBadge value={r.enabled ? "ENABLED" : "DISABLED"} />
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
function HealthPage({
  kind,
  title,
}: {
  kind: "system" | "database" | "vision" | "storage";
  title: string;
}) {
  const q = useData("health", platformApi.health);
  if (q.isLoading) return <Loading />;
  const value = q.data[kind];
  return (
    <Page
      title={title}
      subtitle="Platform operatoru üçün real backend health məlumatı"
    >
      <section className="card health">
        <StatusBadge value={value.status ?? "AVAILABLE"} />
        {Object.entries(value).map(([key, item]) => (
          <p key={key}>
            <b>{key}:</b> {String(item)}
          </p>
        ))}
      </section>
    </Page>
  );
}
export const SystemHealthPage = () => (
  <HealthPage kind="system" title="System health" />
);
export const DatabaseHealthPage = () => (
  <HealthPage kind="database" title="Database health" />
);
export const VisionHealthPage = () => (
  <HealthPage kind="vision" title="Vision health" />
);
export const StorageUsagePage = () => (
  <HealthPage kind="storage" title="Storage usage" />
);
export function TenantUsagePage() {
  const q = useData("tenant-usage", platformApi.tenantUsage);
  return (
    <Page
      title="Tenant usage"
      subtitle="Organisation üzrə filial, istifadəçi, incident və storage"
    >
      <section className="card">
        <DataTable
          rows={q.data ?? []}
          columns={[
            { key: "organisation", label: "Organisation" },
            { key: "branches", label: "Filial" },
            { key: "users", label: "İstifadəçi" },
            { key: "incidents", label: "Incident" },
            {
              key: "storage_bytes",
              label: "Storage",
              render: (r) => `${(r.storage_bytes / 1048576).toFixed(2)} MB`,
            },
          ]}
        />
      </section>
    </Page>
  );
}
export function SystemSettingsPage() {
  const q = useData("settings", platformApi.settings),
    client = useQueryClient(),
    [form, setForm] = useState({
      key: "support_email",
      value: "support@martiq.az",
    }),
    mutation = useMutation({
      mutationFn: () => platformApi.setSetting(form),
      onSuccess: () => client.invalidateQueries({ queryKey: ["settings"] }),
    });
  return (
    <Page
      title="System settings"
      subtitle="Platform səviyyəli açar-dəyər konfiqurasiyası"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          {["key", "value"].map((key) => (
            <label className="field" key={key}>
              {key}
              <input
                value={(form as any)[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </label>
          ))}
          <button className="btn">Yadda saxla</button>
        </form>
        <section className="card">
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "key", label: "Açar" },
              { key: "value", label: "Dəyər" },
              {
                key: "updated_at",
                label: "Yenilənib",
                render: (r) => new Date(r.updated_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function LogsPage() {
  const q = useData("logs", platformApi.logs);
  return (
    <Page
      title="Sistem logları"
      subtitle="Audit edilə bilən idarəetmə əməliyyatları"
    >
      <section className="card">
        <DataTable
          rows={q.data ?? []}
          columns={[
            {
              key: "created_at",
              label: "Tarix",
              render: (r) => new Date(r.created_at).toLocaleString("az-AZ"),
            },
            { key: "action", label: "Əməliyyat" },
            { key: "entity_type", label: "Resurs" },
            { key: "entity_id", label: "ID" },
            { key: "detail", label: "Detal" },
          ]}
        />
      </section>
    </Page>
  );
}
export function DemoResetPage() {
  const [open, setOpen] = useState(false),
    mutation = useMutation({
      mutationFn: platformApi.demoReset,
      onSuccess: () => setOpen(false),
    });
  return (
    <Page
      title="Demo reset"
      subtitle="Seed master data qorunur; reset sorğusu audit loguna yazılır"
    >
      <section className="card danger-zone">
        <h2>Təsdiq tələb olunur</h2>
        <p>
          Bu əməliyyat yalnız platform administratoru üçün əlçatandır və backend
          ayrıca RESET_DEMO təsdiqi tələb edir.
        </p>
        <button className="btn danger" onClick={() => setOpen(true)}>
          Demo reset
        </button>
        {mutation.isSuccess ? (
          <p className="success">Reset sorğusu tamamlandı və loglandı.</p>
        ) : null}
        {open ? (
          <Modal
            title="Demo reset təsdiqi"
            onClose={() => setOpen(false)}
            actions={
              <>
                <button
                  className="btn secondary"
                  onClick={() => setOpen(false)}
                >
                  Ləğv et
                </button>
                <button
                  className="btn danger"
                  onClick={() => mutation.mutate()}
                >
                  Reset et
                </button>
              </>
            }
          >
            <p>Demo məlumatlarını sıfırlamaq istədiyinizi təsdiqləyin.</p>
          </Modal>
        ) : null}
      </section>
    </Page>
  );
}
function ManageOrganisation({ item }: { item: any }) {
  const [open, setOpen] = useState(false),
    [name, setName] = useState(item.name),
    [active, setActive] = useState(item.is_active !== false),
    client = useQueryClient(),
    mutation = useMutation({
      mutationFn: () =>
        platformApi.updateOrganisation(item.id, { name, is_active: active }),
      onSuccess: () => {
        setOpen(false);
        client.invalidateQueries({ queryKey: ["organisations"] });
      },
    });
  return (
    <>
      <button className="btn secondary small" onClick={() => setOpen(true)}>
        İdarə et
      </button>
      {open ? (
        <Modal
          title="Organisation idarəetməsi"
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button className="btn" onClick={() => mutation.mutate()}>
                Yadda saxla
              </button>
            </>
          }
        >
          <label className="field">
            Ad
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />{" "}
            Aktiv tenant
          </label>
        </Modal>
      ) : null}
    </>
  );
}
function ManageAdmin({ item }: { item: any }) {
  const [open, setOpen] = useState(false),
    [name, setName] = useState(item.full_name),
    [active, setActive] = useState(item.is_active),
    client = useQueryClient(),
    mutation = useMutation({
      mutationFn: () =>
        platformApi.updateAdmin(item.id, {
          full_name: name,
          is_active: active,
          branch_id: item.branch_id,
        }),
      onSuccess: () => {
        setOpen(false);
        client.invalidateQueries({ queryKey: ["admins"] });
      },
    });
  return (
    <>
      <button className="btn secondary small" onClick={() => setOpen(true)}>
        İdarə et
      </button>
      {open ? (
        <Modal
          title="Administrator idarəetməsi"
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button className="btn" onClick={() => mutation.mutate()}>
                Yadda saxla
              </button>
            </>
          }
        >
          <label className="field">
            Ad
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />{" "}
            Aktiv hesab
          </label>
        </Modal>
      ) : null}
    </>
  );
}
function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: any[];
  onChange: (x: string) => void;
}) {
  return (
    <label className="field">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Seçin</option>
        {options.map((item) => (
          <option value={item.id} key={item.id}>
            {item.name}
          </option>
        ))}
      </select>
    </label>
  );
}
