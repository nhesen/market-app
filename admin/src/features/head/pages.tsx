import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { contentApi, operationsApi } from "../../services/api";
import {
  DataTable,
  Loading,
  Metric,
  MiniChart,
  Modal,
  Page,
  StatusBadge,
} from "../../components/ui";

const useData = (key: string, fn: () => Promise<any>) =>
  useQuery({ queryKey: [key], queryFn: fn });
export function NetworkDashboard() {
  const network = useData("network", contentApi.network),
    analytics = useData("network-analytics", operationsApi.analytics);
  const rows = network.data ?? [],
    a = analytics.data?.summary ?? {};
  return (
    <Page
      title="Şəbəkə dashboard"
      subtitle="Supermarket şəbəkəsinin real database əməliyyat göstəriciləri"
    >
      <div className="grid">
        <Metric label="Açıq incidentlər" value={a.open ?? 0} />
        <Metric label="Kritik incidentlər" value={a.critical ?? 0} />
        <Metric label="Gecikmiş incidentlər" value={a.overdue ?? 0} />
        <Metric label="Bu gün həll edilən" value={a.resolved_today ?? 0} />
        <Metric
          label="Orta həll müddəti"
          value={`${a.average_resolution_hours ?? 0} saat`}
        />
        <Metric
          label="Median həll müddəti"
          value={`${a.median_resolution_hours ?? 0} saat`}
        />
        <Metric
          label="Auto-resolve faizi"
          value={`${a.auto_resolve_rate ?? 0}%`}
        />
        <Metric
          label="Manual həll faizi"
          value={`${a.manual_resolve_rate ?? 0}%`}
        />
        <Metric
          label="Report verification"
          value={`${a.customer_verification_rate ?? 0}%`}
        />
        <Metric
          label="Audit completion"
          value={`${a.audit_completion_rate ?? 0}%`}
        />
        <Metric
          label="Re-audit consistency"
          value={`${a.re_audit_consistency_rate ?? 0}%`}
        />
        <Metric
          label="Camera false alerts"
          value={`${a.camera_false_alert_rate ?? 0}%`}
        />
      </div>
      <div className="content spaced">
        <section className="card">
          <h2>Smart Store Score sıralaması</h2>
          <MiniChart rows={rows} labelKey="branch" valueKey="score" />
        </section>
        <Chart title="Mənbələr" rows={analytics.data?.by_source ?? []} />
        <Chart title="Statuslar" rows={analytics.data?.by_status ?? []} />
        <Chart
          title="Təkrarlanan problemlər"
          rows={analytics.data?.recurring_issues ?? []}
        />
      </div>
    </Page>
  );
}
export function BranchComparisonPage() {
  const q = useData("network", contentApi.network),
    rows = q.data ?? [];
  return (
    <Page
      title="Filial müqayisəsi"
      subtitle="Score, risk, SLA, audit və kamera keyfiyyəti"
    >
      <div className="content">
        <section className="card">
          <DataTable
            rows={rows}
            columns={[
              { key: "branch", label: "Filial" },
              {
                key: "score",
                label: "Score",
                render: (r) => <b>{r.score}/100</b>,
              },
              { key: "open_incidents", label: "Açıq" },
              { key: "critical_incidents", label: "Kritik" },
              { key: "overdue", label: "Gecikmiş" },
              { key: "average_resolution_hours", label: "Orta həll" },
              {
                key: "audit_completion_rate",
                label: "Audit completion",
                render: (r) => `${r.audit_completion_rate}%`,
              },
              {
                key: "camera_false_alert_rate",
                label: "False alert",
                render: (r) => `${r.camera_false_alert_rate}%`,
              },
            ]}
          />
        </section>
        <section className="card">
          <h2>Filial xəritəsi</h2>
          <div
            className="spatial"
            role="img"
            aria-label="Filialların sxematik məkan görünüşü"
          >
            {rows.map((row: any, index: number) => (
              <div
                className="map-pin"
                key={row.branch}
                style={{
                  left: `${22 + ((index * 31) % 65)}%`,
                  top: `${25 + ((index * 37) % 60)}%`,
                }}
                title={`${row.branch}: ${row.score}`}
              >
                <span>{index + 1}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Page>
  );
}
export function OperationalAnalyticsPage() {
  const branches = useData("branches", operationsApi.branches),
    [filters, setFilters] = useState<Record<string, string>>({}),
    analytics = useQuery({
      queryKey: ["operational-analytics", filters],
      queryFn: () =>
        operationsApi.analytics(
          Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
        ),
    }),
    data = analytics.data;
  return (
    <Page
      title="Əməliyyat analitikası"
      subtitle="Real database KPI-ları və backend filtrləri"
    >
      <form className="card filters" onSubmit={(e) => e.preventDefault()}>
        <label className="field">
          Filial
          <select
            value={filters.branch_id ?? ""}
            onChange={(e) =>
              setFilters({ ...filters, branch_id: e.target.value })
            }
          >
            <option value="">Bütün filiallar</option>
            {branches.data?.map((b: any) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          Status
          <select
            value={filters.status ?? ""}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">Bütün statuslar</option>
            {[
              "NEW",
              "PRECHECK",
              "VERIFICATION_REQUIRED",
              "VERIFIED",
              "ASSIGNED",
              "IN_PROGRESS",
              "RESOLUTION_CANDIDATE",
              "AUTO_RESOLVED",
              "MANUALLY_RESOLVED",
              "REJECTED",
              "REOPENED",
              "CANCELLED",
            ].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Mənbə
          <select
            value={filters.source ?? ""}
            onChange={(e) => setFilters({ ...filters, source: e.target.value })}
          >
            <option value="">Bütün mənbələr</option>
            {[
              "CUSTOMER_REPORT",
              "STAFF_AUDIT",
              "CAMERA_EVENT",
              "MANUAL_ADMIN_ENTRY",
            ].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Prioritet
          <select
            value={filters.priority ?? ""}
            onChange={(e) =>
              setFilters({ ...filters, priority: e.target.value })
            }
          >
            <option value="">Bütün prioritetlər</option>
            {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Kateqoriya
          <select
            value={filters.category ?? ""}
            onChange={(e) =>
              setFilters({ ...filters, category: e.target.value })
            }
          >
            <option value="">Bütün kateqoriyalar</option>
            {[
              "PRODUCT",
              "PRICE",
              "SHELF",
              "CLEANLINESS",
              "SAFETY",
              "CUSTOMER_SERVICE",
              "CAMERA",
              "OTHER",
            ].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Başlanğıc
          <input
            type="datetime-local"
            value={filters.date_from ?? ""}
            onChange={(e) =>
              setFilters({ ...filters, date_from: e.target.value })
            }
          />
        </label>
        <label className="field">
          Son
          <input
            type="datetime-local"
            value={filters.date_to ?? ""}
            onChange={(e) =>
              setFilters({ ...filters, date_to: e.target.value })
            }
          />
        </label>
        <button
          type="button"
          className="btn secondary"
          onClick={() => setFilters({})}
        >
          Filterləri sıfırla
        </button>
      </form>
      {analytics.isLoading ? (
        <Loading />
      ) : data ? (
        <>
          <div className="grid spaced">
            <Metric label="Açıq" value={data.summary.open} />
            <Metric label="Kritik" value={data.summary.critical} />
            <Metric label="Gecikmiş" value={data.summary.overdue} />
            <Metric label="Bu gün həll" value={data.summary.resolved_today} />
            <Metric
              label="Orta həll müddəti"
              value={`${data.summary.average_resolution_hours} saat`}
            />
            <Metric
              label="Median həll müddəti"
              value={`${data.summary.median_resolution_hours} saat`}
            />
            <Metric
              label="Auto-resolve faizi"
              value={`${data.summary.auto_resolve_rate}%`}
            />
            <Metric
              label="Manual həll faizi"
              value={`${data.summary.manual_resolve_rate}%`}
            />
            <Metric
              label="Müştəri təsdiqi"
              value={`${data.summary.customer_verification_rate}%`}
            />
            <Metric
              label="Audit completion"
              value={`${data.summary.audit_completion_rate}%`}
            />
            <Metric
              label="Təkrar audit uyğunluğu"
              value={`${data.summary.re_audit_consistency_rate}%`}
            />
            <Metric
              label="Kamera false-alert"
              value={`${data.summary.camera_false_alert_rate}%`}
            />
          </div>
          <div className="content spaced">
            <Chart title="Mənbə bölgüsü" rows={data.by_source} />
            <Chart title="Status bölgüsü" rows={data.by_status} />
            <Chart title="Kateqoriya bölgüsü" rows={data.by_category} />
            <Chart title="Prioritet bölgüsü" rows={data.by_priority} />
            <Chart title="Saat bölgüsü" rows={data.by_hour} />
            <Chart
              title="Təkrarlanan problemlər"
              rows={data.recurring_issues}
            />
          </div>
        </>
      ) : (
        <Loading error={analytics.error} />
      )}
    </Page>
  );
}
function Chart({ title, rows }: { title: string; rows: any[] }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <MiniChart rows={rows} labelKey="name" valueKey="value" />
    </section>
  );
}
export function ScoreRankingPage() {
  const q = useData("network", contentApi.network);
  return (
    <Page
      title="Smart Store Score sıralaması"
      subtitle="İzah edilə bilən daxili əməliyyat göstəricisi"
    >
      <section className="card">
        <DataTable
          rows={[...(q.data ?? [])].sort((a, b) => b.score - a.score)}
          columns={[
            { key: "rank", label: "#", render: (_, i?: any) => i },
            { key: "branch", label: "Filial" },
            {
              key: "score",
              label: "Score",
              render: (r) => <StatusBadge value={`${r.score}/100`} />,
            },
            { key: "open_incidents", label: "Açıq" },
            { key: "quality_flags", label: "Audit flagı" },
          ]}
        />
      </section>
    </Page>
  );
}

function Resource({
  title,
  subtitle,
  keyName,
  fn,
  columns,
}: {
  title: string;
  subtitle: string;
  keyName: string;
  fn: () => Promise<any[]>;
  columns: any[];
}) {
  const q = useData(keyName, fn);
  return (
    <Page title={title} subtitle={subtitle}>
      <section className="card">
        {q.isLoading ? (
          <Loading />
        ) : (
          <DataTable rows={q.data ?? []} columns={columns} />
        )}
      </section>
    </Page>
  );
}
export const BranchesPage = () => (
  <Resource
    title="Filiallar"
    subtitle="Organisation filial kataloqu"
    keyName="branches"
    fn={operationsApi.branches}
    columns={[
      { key: "name", label: "Filial" },
      { key: "address", label: "Ünvan" },
      { key: "hours", label: "İş saatı" },
      {
        key: "is_open",
        label: "Status",
        render: (r: any) => (
          <StatusBadge value={r.is_open ? "OPEN" : "CLOSED"} />
        ),
      },
    ]}
  />
);
export const StaffOverviewPage = () => (
  <Resource
    title="Staff overview"
    subtitle="Bütün organisation əməkdaşları"
    keyName="staff"
    fn={operationsApi.staff}
    columns={[
      { key: "full_name", label: "Ad" },
      { key: "email", label: "E-poçt" },
      { key: "branch_id", label: "Filial" },
      {
        key: "is_active",
        label: "Aktiv",
        render: (r: any) => (r.is_active ? "Bəli" : "Xeyr"),
      },
    ]}
  />
);
export const CameraOverviewPage = () => (
  <Resource
    title="Kamera overview"
    subtitle="Hybrid pipeline telemetry; controlled MP4 RTSP deyil"
    keyName="vision"
    fn={operationsApi.visionHealth}
    columns={[
      { key: "name", label: "Kamera" },
      { key: "source_type", label: "Mənbə" },
      {
        key: "source_active",
        label: "Status",
        render: (r: any) => (
          <StatusBadge value={r.source_active ? "ACTIVE" : "ERROR"} />
        ),
      },
      { key: "approximate_fps", label: "Təxmini FPS" },
      {
        key: "rules",
        label: "Engine / rule",
        render: (r: any) =>
          r.rules
            ?.map(
              (x: any) =>
                `${x.rule_type}: ${x.detection_engine} [${x.current_state}]`,
            )
            .join("; ") || "—",
      },
      { key: "processing_error", label: "Xəta" },
    ]}
  />
);

export function NewsPage() {
  const client = useQueryClient(),
    q = useData("news", contentApi.news),
    [form, setForm] = useState({
      title_az: "",
      title_en: "",
      summary_az: "",
      summary_en: "",
      image_url: "/assets/news-market.svg",
      branch_id: null,
    }),
    mutation = useMutation({
      mutationFn: () => contentApi.createNews(form),
      onSuccess: () => client.invalidateQueries({ queryKey: ["news"] }),
    });
  return (
    <Page title="Xəbər idarəetməsi" subtitle="Mobil tətbiq üçün AZ/EN xəbərlər">
      <div className="content">
        <CrudForm
          title="Yeni xəbər"
          form={form}
          setForm={setForm}
          onSubmit={() => mutation.mutate()}
        />
        <section className="card">
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "title_az", label: "Başlıq AZ" },
              { key: "title_en", label: "Başlıq EN" },
              {
                key: "published_at",
                label: "Tarix",
                render: (r) =>
                  new Date(r.published_at).toLocaleDateString("az-AZ"),
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => (
                  <div className="inline">
                    <EditorButton
                      title="Xəbəri redaktə et"
                      initial={{
                        title_az: r.title_az,
                        title_en: r.title_en,
                        summary_az: r.summary_az,
                        summary_en: r.summary_en,
                      }}
                      run={(value) =>
                        contentApi.updateNews(r.id, { ...r, ...value })
                      }
                      invalidate="news"
                    />
                    <DeleteButton
                      run={() => contentApi.deleteNews(r.id)}
                      invalidate="news"
                    />
                  </div>
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function ProductsPage() {
  const client = useQueryClient(),
    q = useData("products", contentApi.products),
    [form, setForm] = useState({
      name: "",
      brand: "",
      barcode: "",
      category: "Food",
      price: "",
      discount_price: "",
      image_url: "/assets/product.svg",
    }),
    mutation = useMutation({
      mutationFn: () =>
        contentApi.createProduct({
          ...form,
          price: Number(form.price),
          discount_price: form.discount_price
            ? Number(form.discount_price)
            : null,
        }),
      onSuccess: () => client.invalidateQueries({ queryKey: ["products"] }),
    });
  return (
    <Page title="Məhsul CRUD" subtitle="Organisation məhsul kataloqu">
      <div className="content">
        <CrudForm
          title="Yeni məhsul"
          form={form}
          setForm={setForm}
          onSubmit={() => mutation.mutate()}
        />
        <section className="card">
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "name", label: "Məhsul" },
              { key: "barcode", label: "Barkod" },
              { key: "category", label: "Kateqoriya" },
              {
                key: "price",
                label: "Qiymət",
                render: (r) => `${r.price.toFixed(2)} ₼`,
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => (
                  <div className="inline">
                    <EditorButton
                      title="Məhsulu redaktə et"
                      initial={{
                        name: r.name,
                        brand: r.brand,
                        barcode: r.barcode,
                        category: r.category,
                        price: r.price,
                        discount_price: r.discount_price ?? "",
                      }}
                      run={(value) =>
                        contentApi.updateProduct(r.id, {
                          ...r,
                          ...value,
                          price: Number(value.price),
                          discount_price: value.discount_price
                            ? Number(value.discount_price)
                            : null,
                        })
                      }
                      invalidate="products"
                    />
                    <DeleteButton
                      run={() => contentApi.deleteProduct(r.id)}
                      invalidate="products"
                    />
                  </div>
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function CategoriesPage() {
  const q = useData("categories", contentApi.categories),
    [name, setName] = useState(""),
    client = useQueryClient(),
    mutation = useMutation({
      mutationFn: () => contentApi.createCategory(name),
      onSuccess: () => {
        setName("");
        client.invalidateQueries({ queryKey: ["categories"] });
      },
    });
  return (
    <Page
      title="Kateqoriya CRUD"
      subtitle="Məhsul filterlərinin idarə edilməsi"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <h2>Yeni kateqoriya</h2>
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
              { key: "name", label: "Kateqoriya" },
              {
                key: "delete",
                label: "",
                render: (r) => (
                  <DeleteButton
                    run={() => contentApi.deleteCategory(r.id)}
                    invalidate="categories"
                  />
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function PricesPage() {
  const branches = useData("branches", operationsApi.branches),
    products = useData("products", contentApi.products),
    prices = useData("prices", contentApi.prices),
    client = useQueryClient(),
    [form, setForm] = useState({
      branch_id: "",
      product_id: "",
      price: "",
      previous_price: "",
      available: true,
    }),
    mutation = useMutation({
      mutationFn: () =>
        contentApi.setPrice({
          ...form,
          price: Number(form.price),
          previous_price: form.previous_price
            ? Number(form.previous_price)
            : null,
        }),
      onSuccess: () => client.invalidateQueries({ queryKey: ["prices"] }),
    });
  return (
    <Page
      title="Filial qiymətləri CRUD"
      subtitle="Məhsulun filial üzrə qiymət və mövcudluğu"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <h2>Qiymət təyin et / yenilə</h2>
          <Select
            label="Filial"
            value={form.branch_id}
            options={branches.data ?? []}
            onChange={(value) => setForm({ ...form, branch_id: value })}
          />
          <Select
            label="Məhsul"
            value={form.product_id}
            options={products.data ?? []}
            onChange={(value) => setForm({ ...form, product_id: value })}
          />
          <label className="field">
            Qiymət
            <input
              type="number"
              step=".01"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
          </label>
          <button className="btn">Yadda saxla</button>
        </form>
        <section className="card">
          <DataTable
            rows={prices.data ?? []}
            columns={[
              { key: "branch_id", label: "Filial ID" },
              { key: "product_id", label: "Məhsul ID" },
              { key: "price", label: "Qiymət" },
              { key: "available", label: "Mövcud" },
              {
                key: "delete",
                label: "",
                render: (r) => (
                  <DeleteButton
                    run={() => contentApi.deletePrice(r.id)}
                    invalidate="prices"
                  />
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export function CampaignsPage() {
  const q = useData("campaigns", contentApi.campaigns),
    client = useQueryClient(),
    [form, setForm] = useState({
      title: "",
      description: "",
      starts_on: "",
      ends_on: "",
      published: true,
    }),
    mutation = useMutation({
      mutationFn: () => contentApi.createCampaign(form),
      onSuccess: () => client.invalidateQueries({ queryKey: ["campaigns"] }),
    });
  return (
    <Page
      title="Kampaniya CRUD"
      subtitle="Endirim kampaniyaları, məhsullar, filiallar və qiymətlər"
    >
      <div className="content">
        <CrudForm
          title="Yeni kampaniya"
          form={form}
          setForm={setForm}
          onSubmit={() => mutation.mutate()}
        />
        <section className="card">
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "title", label: "Kampaniya" },
              { key: "starts_on", label: "Başlanğıc" },
              { key: "ends_on", label: "Son" },
              {
                key: "published",
                label: "Status",
                render: (r) => (
                  <StatusBadge value={r.published ? "PUBLISHED" : "DRAFT"} />
                ),
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => (
                  <div className="inline">
                    <Link
                      className="btn small"
                      to={`/head/campaigns/${r.id}/products`}
                    >
                      Məhsullar
                    </Link>
                    <EditorButton
                      title="Kampaniyanı redaktə et"
                      initial={{
                        title: r.title,
                        description: r.description,
                        starts_on: r.starts_on,
                        ends_on: r.ends_on,
                        published: r.published,
                      }}
                      run={(value) =>
                        contentApi.updateCampaign(r.id, { ...r, ...value })
                      }
                      invalidate="campaigns"
                    />
                    <DeleteButton
                      run={() => contentApi.deleteCampaign(r.id)}
                      invalidate="campaigns"
                    />
                  </div>
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
export const ContentOverviewPage = () => {
  const products = useData("products", contentApi.products),
    news = useData("news", contentApi.news),
    campaigns = useData("campaigns", contentApi.campaigns);
  return (
    <Page
      title="Kontent idarəetməsi"
      subtitle="Xəbər, məhsul və kampaniya xülasəsi"
    >
      <div className="grid">
        <Metric label="Məhsul" value={products.data?.length ?? 0} />
        <Metric label="Xəbər" value={news.data?.length ?? 0} />
        <Metric label="Kampaniya" value={campaigns.data?.length ?? 0} />
      </div>
    </Page>
  );
};
function CrudForm({
  title,
  form,
  setForm,
  onSubmit,
}: {
  title: string;
  form: any;
  setForm: (x: any) => void;
  onSubmit: () => void;
}) {
  return (
    <form
      className="card form"
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <h2>{title}</h2>
      {Object.entries(form)
        .filter(([key]) => key !== "branch_id")
        .map(([key, value]) => (
          <label className="field" key={key}>
            {key.replaceAll("_", " ")}
            <input
              type={
                key.includes("_on")
                  ? "date"
                  : typeof value === "number"
                    ? "number"
                    : "text"
              }
              value={String(value ?? "")}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </label>
        ))}
      <button className="btn">Yadda saxla</button>
    </form>
  );
}
function DeleteButton({
  run,
  invalidate,
}: {
  run: () => Promise<void>;
  invalidate: string;
}) {
  const [open, setOpen] = useState(false),
    client = useQueryClient(),
    mutation = useMutation({
      mutationFn: run,
      onSuccess: () => {
        setOpen(false);
        client.invalidateQueries({ queryKey: [invalidate] });
      },
    });
  return (
    <>
      <button className="btn danger small" onClick={() => setOpen(true)}>
        Sil
      </button>
      {open ? (
        <Modal
          title="Silməni təsdiqlə"
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button className="btn danger" onClick={() => mutation.mutate()}>
                Sil
              </button>
            </>
          }
        >
          <p>Bu əməliyyat geri qaytarılmaya bilər.</p>
        </Modal>
      ) : null}
    </>
  );
}
function EditorButton({
  title,
  initial,
  run,
  invalidate,
}: {
  title: string;
  initial: Record<string, any>;
  run: (value: Record<string, any>) => Promise<any>;
  invalidate: string;
}) {
  const [open, setOpen] = useState(false),
    [form, setForm] = useState(initial),
    client = useQueryClient(),
    mutation = useMutation({
      mutationFn: () => run(form),
      onSuccess: () => {
        setOpen(false);
        client.invalidateQueries({ queryKey: [invalidate] });
      },
    });
  return (
    <>
      <button
        className="btn secondary small"
        onClick={() => {
          setForm(initial);
          setOpen(true);
        }}
      >
        Redaktə
      </button>
      {open ? (
        <Modal
          title={title}
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
          {Object.entries(form).map(([key, value]) => (
            <label className="field" key={key}>
              {key.replaceAll("_", " ")}
              {typeof value === "boolean" ? (
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(e) =>
                    setForm({ ...form, [key]: e.target.checked })
                  }
                />
              ) : key.includes("summary") || key === "description" ? (
                <textarea
                  value={String(value ?? "")}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              ) : (
                <input
                  type={
                    key.includes("_on")
                      ? "date"
                      : key.includes("price")
                        ? "number"
                        : "text"
                  }
                  value={String(value ?? "")}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              )}
            </label>
          ))}
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
