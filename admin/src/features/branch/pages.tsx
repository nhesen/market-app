import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { mediaUrl, operationsApi, session } from "../../services/api";
import {
  DataTable,
  DetailLink,
  Loading,
  MediaViewer,
  Metric,
  MiniChart,
  Modal,
  Page,
  StatusBadge,
  Timeline,
} from "../../components/ui";

const useData = (key: string, fn: () => Promise<any>) =>
  useQuery({ queryKey: [key], queryFn: fn });
export function BranchDashboard() {
  const dashboard = useData("dashboard", operationsApi.dashboard),
    analytics = useData("branch-analytics", operationsApi.analytics),
    incidents = useData("incidents", operationsApi.incidents),
    audits = useData("audits", operationsApi.audits),
    events = useData("camera-events", operationsApi.cameraEvents),
    reports = useData("reports", () => operationsApi.reports());
  if (dashboard.isLoading || analytics.isLoading) return <Loading />;
  const a = analytics.data.summary,
    overdue = (incidents.data ?? []).filter((x: any) => x.is_overdue),
    overdueAudits = (audits.data ?? []).filter(
      (x: any) => new Date(x.due_at) < new Date() && x.status !== "COMPLETED",
    );
  return (
    <Page
      title="Filial dashboard"
      subtitle="Filialda hazırda nə baş verdiyini göstərən real əməliyyat görünüşü"
    >
      <div className="grid">
        <Metric label="Açıq incidentlər" value={a.open} />
        <Metric label="Kritik incidentlər" value={a.critical} />
        <Metric label="Gecikmiş incidentlər" value={a.overdue} />
        <Metric label="Bu gün həll edilən" value={a.resolved_today} />
        <Metric
          label="Orta həll müddəti"
          value={`${a.average_resolution_hours} saat`}
        />
        <Metric label="Auto-resolve faizi" value={`${a.auto_resolve_rate}%`} />
        <Metric
          label="Report təsdiq faizi"
          value={`${a.customer_verification_rate}%`}
        />
        <Metric
          label="Audit tamamlama faizi"
          value={`${a.audit_completion_rate}%`}
        />
        <Metric
          label="Smart Store Score"
          value={`${dashboard.data.smart_store_score}/100`}
          hint={dashboard.data.score_explanation}
        />
      </div>
      <div className="content spaced">
        <section className="card">
          <h2>Son incidentlər</h2>
          <DataTable
            rows={(incidents.data ?? []).slice(0, 6)}
            columns={[
              {
                key: "title",
                label: "Hadisə",
                render: (r) => (
                  <DetailLink
                    to={`/branch/incidents/${r.id}`}
                    label={r.title}
                  />
                ),
              },
              { key: "source", label: "Mənbə" },
              {
                key: "status",
                label: "Status",
                render: (r) => <StatusBadge value={r.status} />,
              },
            ]}
          />
          <h2>Gecikmiş incidentlər</h2>
          <DataTable
            rows={overdue.slice(0, 5)}
            columns={[
              {
                key: "title",
                label: "Hadisə",
                render: (r) => (
                  <DetailLink
                    to={`/branch/incidents/${r.id}`}
                    label={r.title}
                  />
                ),
              },
              {
                key: "sla_due_at",
                label: "SLA",
                render: (r) => new Date(r.sla_due_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        </section>
        <section className="card">
          <h2>Mənbələr üzrə incidentlər</h2>
          <MiniChart
            rows={analytics.data.by_source}
            labelKey="name"
            valueKey="value"
          />
          <h2>Kateqoriyalar</h2>
          <MiniChart
            rows={analytics.data.by_category}
            labelKey="name"
            valueKey="value"
          />
        </section>
        <section className="card">
          <h2>Gözləyən müştəri reportları</h2>
          <DataTable
            rows={(reports.data ?? [])
              .filter(
                (x: any) =>
                  !["MANUALLY_RESOLVED", "REJECTED"].includes(
                    x.incident?.status,
                  ),
              )
              .slice(0, 5)}
            columns={[
              { key: "tracking_number", label: "İzləmə" },
              {
                key: "title",
                label: "Report",
                render: (r) => (
                  <DetailLink to={`/branch/reports/${r.id}`} label={r.title} />
                ),
              },
            ]}
          />
          <h2>Gecikmiş auditlər</h2>
          <DataTable
            rows={overdueAudits.slice(0, 5)}
            columns={[
              { key: "title", label: "Audit" },
              {
                key: "due_at",
                label: "Son vaxt",
                render: (r) => new Date(r.due_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        </section>
        <section className="card">
          <h2>Son kamera hadisələri</h2>
          <DataTable
            rows={(events.data ?? []).slice(0, 5)}
            columns={[
              { key: "rule", label: "Qayda" },
              { key: "detection_engine", label: "Engine" },
              {
                key: "status",
                label: "Status",
                render: (r) => <StatusBadge value={r.status} />,
              },
            ]}
          />
          <h2>Audit statusları</h2>
          <MiniChart
            rows={Object.entries(
              (audits.data ?? []).reduce(
                (a: any, x: any) => ({
                  ...a,
                  [x.status]: (a[x.status] ?? 0) + 1,
                }),
                {},
              ),
            ).map(([status, count]) => ({ status, count }))}
            labelKey="status"
            valueKey="count"
          />
        </section>
      </div>
    </Page>
  );
}

export function ReportsPage() {
  const [filters, setFilters] = useState({
      search: "",
      category: "",
      status: "",
    }),
    q = useQuery({
      queryKey: ["reports", filters],
      queryFn: () =>
        operationsApi.reports(
          Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
        ),
    });
  return (
    <Page
      title="Müştəri reportları"
      subtitle="Filiala scoped axtarış, kateqoriya və status filtrləri"
    >
      <section className="card">
        <div className="filters">
          <label className="field">
            Axtarış
            <input
              value={filters.search}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value })
              }
            />
          </label>
          <label className="field">
            Kateqoriya
            <select
              value={filters.category}
              onChange={(e) =>
                setFilters({ ...filters, category: e.target.value })
              }
            >
              <option value="">Hamısı</option>
              {[
                "PRODUCT",
                "PRICE",
                "SHELF",
                "CLEANLINESS",
                "SAFETY",
                "CUSTOMER_SERVICE",
                "OTHER",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Status
            <select
              value={filters.status}
              onChange={(e) =>
                setFilters({ ...filters, status: e.target.value })
              }
            >
              <option value="">Hamısı</option>
              {[
                "NEW",
                "PRECHECK",
                "VERIFICATION_REQUIRED",
                "VERIFIED",
                "ASSIGNED",
                "IN_PROGRESS",
                "MANUALLY_RESOLVED",
                "REJECTED",
                "REOPENED",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
        </div>
        {q.isLoading ? (
          <Loading />
        ) : (
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "tracking_number", label: "İzləmə" },
              {
                key: "title",
                label: "Başlıq",
                render: (r) => (
                  <DetailLink to={`/branch/reports/${r.id}`} label={r.title} />
                ),
              },
              { key: "category", label: "Kateqoriya" },
              { key: "subcategory", label: "Alt kateqoriya" },
              {
                key: "status",
                label: "Status",
                render: (r) => <StatusBadge value={r.incident.status} />,
              },
              {
                key: "incident_id",
                label: "Linked incident",
                render: (r) => (
                  <DetailLink
                    to={`/branch/incidents/${r.incident_id}`}
                    label={r.incident_id.slice(0, 8)}
                  />
                ),
              },
              {
                key: "created_at",
                label: "Tarix",
                render: (r) => new Date(r.created_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        )}
      </section>
    </Page>
  );
}
export function ReportDetailPage() {
  const { id } = useParams(),
    client = useQueryClient(),
    q = useQuery({
      queryKey: ["report", id],
      queryFn: () => operationsApi.report(id!),
    }),
    [action, setAction] = useState<"VERIFIED" | "REJECTED" | null>(null),
    [reason, setReason] = useState("");
  const mutation = useMutation({
    mutationFn: async () => {
      let current=q.data.incident;
      if(current.status==="NEW")current=await operationsApi.updateIncident(q.data.incident_id,{status:"PRECHECK",internal_note:"Branch administrator started report precheck.",customer_note:"Müraciət ilkin yoxlamaya alındı."});
      if(action==="VERIFIED"&&current.status==="PRECHECK"&&current.allowed_transitions.includes("VERIFICATION_REQUIRED"))current=await operationsApi.updateIncident(q.data.incident_id,{status:"VERIFICATION_REQUIRED",internal_note:"Report evidence review completed.",customer_note:"Müraciət sübutları yoxlanılır."});
      return operationsApi.updateIncident(q.data.incident_id, {
        status: action,
        internal_note:
          reason || "Customer report verified by branch administrator.",
        customer_note:
          action === "VERIFIED"
            ? "Müraciət filial tərəfindən təsdiqləndi."
            : "Müraciət filial tərəfindən rədd edildi.",
        ...(action === "REJECTED" ? { rejection_reason: reason } : {}),
      });
    },
    onSuccess: () => {
      setAction(null);
      setReason("");
      client.invalidateQueries({ queryKey: ["report", id] });
    },
  });
  if (q.isLoading) return <Loading />;
  if (q.error) return <Loading error={q.error} />;
  const incident = q.data.incident;
  return (
    <Page
      title={q.data.title}
      subtitle={`${q.data.tracking_number} · ${q.data.category}`}
    >
      <div className="case">
        <section className="card">
          <div className="inline">
            <StatusBadge value={incident.status} />
            <StatusBadge value={incident.priority} />
          </div>
          <h2>Təsvir</h2>
          <p>{q.data.description}</p>
          <MediaViewer media={q.data.media} />
          <h2>Status tarixçəsi</h2>
          <Timeline items={incident.history} />
        </section>
        <aside className="card">
          <h2>Report məlumatları</h2>
          <p>
            <b>Müştəri:</b> {q.data.customer?.full_name ?? "Anonim"}
          </p>
          <p>
            <b>Barkod:</b> {q.data.barcode ?? "—"}
          </p>
          <p>
            <b>Alt kateqoriya:</b> {q.data.subcategory ?? "—"}
          </p>
          <p>
            <b>Linked incident:</b> {q.data.incident_id}
          </p>
          <Link
            className="btn action"
            to={`/branch/incidents/${q.data.incident_id}`}
          >
            Linked incidenti aç
          </Link>
          {["NEW","PRECHECK","VERIFICATION_REQUIRED"].includes(incident.status) ? (
            <button
              className="btn action"
              onClick={() => setAction("VERIFIED")}
            >
              Təsdiqlə
            </button>
          ) : null}
          {["NEW","PRECHECK","VERIFICATION_REQUIRED"].includes(incident.status) ? (
            <button
              className="btn danger action"
              onClick={() => setAction("REJECTED")}
            >
              Rədd et
            </button>
          ) : null}
          <Link className="btn secondary action" to="/branch/reports">
            Geri
          </Link>
        </aside>
      </div>
      {action ? (
        <Modal
          title={action === "REJECTED" ? "Reportu rədd et" : "Reportu təsdiqlə"}
          onClose={() => setAction(null)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setAction(null)}>
                Ləğv et
              </button>
              <button
                className="btn"
                disabled={action === "REJECTED" && reason.trim().length < 3}
                onClick={() => mutation.mutate()}
              >
                Təsdiqlə
              </button>
            </>
          }
        >
          <label className="field">
            Qeyd və səbəb
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required={action === "REJECTED"}
            />
          </label>
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}

export function SuggestionsPage() {
  const client = useQueryClient(),
    q = useData("suggestions", operationsApi.suggestions),
    [selected,setSelected]=useState<{id:string;status:string}|null>(null),
    [adminNote,setAdminNote]=useState(""),
    mutation = useMutation({
      mutationFn: () => operationsApi.updateSuggestion(selected!.id,selected!.status,adminNote),
      onSuccess: () => {setSelected(null);setAdminNote("");client.invalidateQueries({ queryKey: ["suggestions"] })},
    });
  return (
    <Page
      title="Rəhbərliyə təkliflər"
      subtitle="Filial və ümumi organisation təklifləri"
    >
      <section className="card">
        <DataTable
          rows={q.data ?? []}
          columns={[
            { key: "tracking_number", label: "İzləmə" },
            { key: "title", label: "Təklif" },
            { key: "category", label: "Kateqoriya" },
            {
              key: "status",
              label: "Status",
              render: (r) => <StatusBadge value={r.status} />,
            },
            {
              key: "actions",
              label: "Əməliyyat",
              render: (r) => (
                <div className="inline">{["UNDER_REVIEW","PLANNED","IMPLEMENTED","REJECTED"].map(status=><button key={status} className={`btn ${status==="REJECTED"?"danger":"secondary"} small`} onClick={()=>setSelected({id:r.id,status})}>{status.replaceAll("_"," ")}</button>)}</div>
              ),
            },
          ]}
        />
      </section>
      {selected?<Modal title="Təklif statusunu yenilə" onClose={()=>setSelected(null)} actions={<><button className="btn secondary" onClick={()=>setSelected(null)}>Ləğv et</button><button className="btn" disabled={(selected.status==="REJECTED"||selected.status==="IMPLEMENTED")&&adminNote.trim().length<3} onClick={()=>mutation.mutate()}>Yadda saxla</button></>}><p><StatusBadge value={selected.status}/></p><label className="field">Rəhbərlik qeydi<textarea value={adminNote} onChange={e=>setAdminNote(e.target.value)} required={selected.status==="REJECTED"}/></label>{mutation.error?<p className="error">{mutation.error.message}</p>:null}</Modal>:null}
    </Page>
  );
}

export function IncidentsPage({ all = false }: { all?: boolean }) {
  const [filters, setFilters] = useState({
      search: "",
      source: "",
      priority: "",
      status: "",
      department: "",
      overdue_only: "",
    }),
    q = useQuery({
      queryKey: ["incidents", filters],
      queryFn: () =>
        operationsApi.incidents(
          Object.fromEntries(
            Object.entries(filters).filter(([, value]) => value),
          ),
        ),
    });
  return (
    <Page
      title={all ? "Bütün incidentlər" : "Filial incidentləri"}
      subtitle="Real backend filtrləri ilə vahid incident axını"
    >
      <section className="card">
        <div className="filters">
          <label className="field">
            Axtarış
            <input
              value={filters.search}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value })
              }
            />
          </label>
          <label className="field">
            Mənbə
            <select
              value={filters.source}
              onChange={(e) =>
                setFilters({ ...filters, source: e.target.value })
              }
            >
              <option value="">Hamısı</option>
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
              value={filters.priority}
              onChange={(e) =>
                setFilters({ ...filters, priority: e.target.value })
              }
            >
              <option value="">Hamısı</option>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Status
            <select
              value={filters.status}
              onChange={(e) =>
                setFilters({ ...filters, status: e.target.value })
              }
            >
              <option value="">Hamısı</option>
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
          <label className="check">
            <input
              type="checkbox"
              checked={filters.overdue_only === "true"}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  overdue_only: e.target.checked ? "true" : "",
                })
              }
            />
            Yalnız gecikmiş
          </label>
        </div>
        {q.isLoading ? (
          <Loading />
        ) : (
          <DataTable
            rows={q.data ?? []}
            columns={[
              {
                key: "preview",
                label: "Media",
                render: (r) =>
                  r.attachments?.[0]?.mime_type?.startsWith("image/") ? (
                    <img
                      className="thumb"
                      src={mediaUrl(r.attachments[0].url)}
                      alt="Incident evidence"
                    />
                  ) : (
                    <img
                      className="thumb"
                      src={mediaUrl(
                        r.source === "CAMERA_EVENT"
                          ? "/assets/retail-camera-v2.png"
                          : "/assets/retail-news-v2.png",
                      )}
                      alt="Retail incident"
                    />
                  ),
              },
              {
                key: "title",
                label: "Hadisə",
                render: (r) => (
                  <DetailLink
                    to={`${all ? "/head" : "/branch"}/incidents/${r.id}`}
                    label={r.title}
                  />
                ),
              },
              { key: "source", label: "Mənbə" },
              {
                key: "priority",
                label: "Prioritet",
                render: (r) => <StatusBadge value={r.priority} />,
              },
              {
                key: "status",
                label: "Status",
                render: (r) => <StatusBadge value={r.status} />,
              },
              { key: "department", label: "Şöbə" },
              {
                key: "created_at",
                label: "Tarix",
                render: (r) => new Date(r.created_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        )}
      </section>
    </Page>
  );
}
export function IncidentDetailPage({ base = "/branch" }: { base?: string }) {
  const { id } = useParams(),
    navigate = useNavigate(),
    client = useQueryClient(),
    q = useData("incidents", operationsApi.incidents),
    item = q.data?.find((row: any) => row.id === id),
    [note, setNote] = useState(""),
    [customerVisible, setCustomerVisible] = useState(false),
    [nextStatus, setNextStatus] = useState<string | null>(null),
    [reason, setReason] = useState(""),
    [department, setDepartment] = useState("BRANCH_MANAGEMENT"),
    [slaHours, setSlaHours] = useState("24");
  const transition = useMutation({
    mutationFn: () => {
      const status = nextStatus!;
      const body: any = {
        status,
        internal_note: `${status.replaceAll("_", " ")} transition completed by admin.`,
        customer_note: `Müraciət statusu yeniləndi: ${status.replaceAll("_", " ")}.`,
      };
      if (status === "ASSIGNED")
        Object.assign(body, {
          responsible_department: department,
          assigned_admin_id: session.user()?.id,
          sla_hours: Number(slaHours),
        });
      if (status === "REJECTED") body.rejection_reason = reason;
      if (status === "MANUALLY_RESOLVED") body.resolution_reason = reason;
      if (status === "REOPENED") body.reopening_reason = reason;
      return operationsApi.updateIncident(id!, body);
    },
    onSuccess: () => {
      setNextStatus(null);
      setReason("");
      client.invalidateQueries({ queryKey: ["incidents"] });
    },
  });
  const addNote = useMutation({
    mutationFn: () => operationsApi.addIncidentNote(id!, note, customerVisible),
    onSuccess: () => {
      setNote("");
      client.invalidateQueries({ queryKey: ["incidents"] });
    },
  });
  if (!item) return <Loading error={q.error} />;
  return (
    <Page title={item.title} subtitle={`${item.source} · ${item.category}`}>
      <div className="case">
        <section className="card">
          <div className="inline">
            <StatusBadge value={item.priority} />
            <StatusBadge value={item.status} />
            {item.is_overdue ? <StatusBadge value="OVERDUE" /> : null}
          </div>
          <p>{item.description}</p>
          <MediaViewer media={item.attachments} />
          <h2>Status tarixçəsi</h2>
          <Timeline items={item.history} />
          <h2>Qeydlər</h2>
          {item.notes?.map((entry: any) => (
            <div className="event" key={entry.id}>
              <StatusBadge value={entry.visibility} />
              <p>{entry.note}</p>
            </div>
          ))}
          <label className="field">
            Yeni qeyd
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={customerVisible}
              onChange={(event) => setCustomerVisible(event.target.checked)}
            />{" "}
            Müştəriyə görünür
          </label>
          <button
            className="btn"
            disabled={note.length < 2}
            onClick={() => addNote.mutate()}
          >
            Qeyd əlavə et
          </button>
        </section>
        <aside className="card">
          <h2>Lifecycle</h2>
          <p>
            <b>Şöbə:</b> {item.responsible_department ?? "—"}
          </p>
          <p>
            <b>SLA:</b>{" "}
            {item.sla_due_at
              ? new Date(item.sla_due_at).toLocaleString("az-AZ")
              : "—"}
          </p>
          <p>
            <b>Staff:</b> {item.assigned_staff_id ?? "—"}
          </p>
          <p>
            <b>Admin:</b> {item.assigned_admin_id ?? "—"}
          </p>
          {item.rejection_reason ? (
            <p>
              <b>Rədd:</b> {item.rejection_reason}
            </p>
          ) : null}
          {item.resolution_reason ? (
            <p>
              <b>Həll:</b> {item.resolution_reason} (
              {item.resolution_actor_type})
            </p>
          ) : null}
          {item.reopening_reason ? (
            <p>
              <b>Yenidən açılma:</b> {item.reopening_reason}
            </p>
          ) : null}
          {item.allowed_transitions.map((status: string) => (
            <button
              className="btn action"
              key={status}
              onClick={() => setNextStatus(status)}
            >
              {status.replaceAll("_", " ")}
            </button>
          ))}
          {transition.error ? (
            <p className="error">{transition.error.message}</p>
          ) : null}
          <button
            className="btn secondary action"
            onClick={() => navigate(`${base}/incidents`)}
          >
            Geri
          </button>
          {nextStatus ? (
            <Modal
              title="Status əməliyyatı"
              onClose={() => setNextStatus(null)}
              actions={
                <>
                  <button
                    className="btn secondary"
                    onClick={() => setNextStatus(null)}
                  >
                    Ləğv et
                  </button>
                  <button
                    className="btn"
                    disabled={
                      (nextStatus === "REJECTED" ||
                        nextStatus === "MANUALLY_RESOLVED" ||
                        nextStatus === "REOPENED") &&
                      reason.trim().length < 3
                    }
                    onClick={() => transition.mutate()}
                  >
                    Təsdiqlə
                  </button>
                </>
              }
            >
              {nextStatus === "ASSIGNED" ? (
                <>
                  <label className="field">
                    Məsul şöbə
                    <select
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                    >
                      {[
                        "CLEANING",
                        "SHELF_AND_STOCK",
                        "QUALITY_CONTROL",
                        "SECURITY",
                        "CUSTOMER_SERVICE",
                        "CHECKOUT_OPERATIONS",
                        "BRANCH_MANAGEMENT",
                        "MAINTENANCE",
                        "OTHER",
                      ].map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    SLA (saat)
                    <input
                      type="number"
                      min="1"
                      value={slaHours}
                      onChange={(e) => setSlaHours(e.target.value)}
                    />
                  </label>
                </>
              ) : null}
              {["REJECTED", "MANUALLY_RESOLVED", "REOPENED"].includes(
                nextStatus,
              ) ? (
                <label className="field">
                  Səbəb
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    required
                  />
                </label>
              ) : (
                <p>
                  Bu status keçidini təsdiqləyin:{" "}
                  <b>{nextStatus.replaceAll("_", " ")}</b>
                </p>
              )}
            </Modal>
          ) : null}
        </aside>
      </div>
    </Page>
  );
}

function SimpleResource({
  title,
  subtitle,
  queryKey,
  queryFn,
  columns,
}: {
  title: string;
  subtitle: string;
  queryKey: string;
  queryFn: () => Promise<any[]>;
  columns: Array<{ key: string; label: string; render?: (r: any) => any }>;
}) {
  const q = useData(queryKey, queryFn);
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
export const StaffAuditsPage = () => (
  <SimpleResource
    title="Staff auditləri"
    subtitle="Tapşırıq, progress və completion vaxtları"
    queryKey="audits"
    queryFn={operationsApi.audits}
    columns={[
      { key: "title", label: "Tapşırıq" },
      { key: "priority", label: "Prioritet" },
      {
        key: "status",
        label: "Status",
        render: (r) => <StatusBadge value={r.status} />,
      },
      {
        key: "item_count",
        label: "Məhsul",
        render: (r) => `${r.item_count}/${r.required_count}`,
      },
      {
        key: "due_at",
        label: "Son vaxt",
        render: (r) => new Date(r.due_at).toLocaleString("az-AZ"),
      },
    ]}
  />
);
export function QualityFlagsPage() {
  const client = useQueryClient(),
    [filters, setFilters] = useState({ severity: "", resolved: "" }),
    q = useQuery({
      queryKey: ["flags", filters],
      queryFn: () =>
        operationsApi.flags(
          Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
        ),
    }),
    mutation = useMutation({
      mutationFn: ({ id, resolved }: { id: string; resolved: boolean }) =>
        operationsApi.resolveFlag(id, resolved),
      onSuccess: () => client.invalidateQueries({ queryKey: ["flags"] }),
    });
  return (
    <Page
      title="Audit keyfiyyət flagları"
      subtitle="Filtrlənən proses nəzarəti; avtomatik intizam qərarı deyil"
    >
      <section className="card">
        <div className="filters">
          <label className="field">
            Səviyyə
            <select
              value={filters.severity}
              onChange={(e) =>
                setFilters({ ...filters, severity: e.target.value })
              }
            >
              <option value="">Hamısı</option>
              <option>WARNING</option>
              <option>ERROR</option>
            </select>
          </label>
          <label className="field">
            Həll statusu
            <select
              value={filters.resolved}
              onChange={(e) =>
                setFilters({ ...filters, resolved: e.target.value })
              }
            >
              <option value="">Hamısı</option>
              <option value="false">Açıq</option>
              <option value="true">Həll edilib</option>
            </select>
          </label>
        </div>
        <DataTable
          rows={q.data ?? []}
          columns={[
            { key: "code", label: "Kod" },
            { key: "message", label: "İzah" },
            {
              key: "severity",
              label: "Səviyyə",
              render: (r) => <StatusBadge value={r.severity} />,
            },
            {
              key: "resolved",
              label: "Status",
              render: (r) => (
                <StatusBadge value={r.resolved ? "RESOLVED" : "OPEN"} />
              ),
            },
            {
              key: "created_at",
              label: "Tarix",
              render: (r) => new Date(r.created_at).toLocaleString("az-AZ"),
            },
            {
              key: "action",
              label: "Əməliyyat",
              render: (r) => (
                <button
                  className="btn secondary small"
                  onClick={() =>
                    mutation.mutate({ id: r.id, resolved: !r.resolved })
                  }
                >
                  {r.resolved ? "Yenidən aç" : "Həll et"}
                </button>
              ),
            },
          ]}
        />
      </section>
    </Page>
  );
}
export const ReAuditsPage = () => (
  <SimpleResource
    title="Təkrar auditlər"
    subtitle="İlkin və təkrar nəticələrin uyğunluğu"
    queryKey="reaudits"
    queryFn={operationsApi.reaudits}
    columns={[
      { key: "original_condition", label: "İlkin" },
      { key: "re_audit_condition", label: "Təkrar" },
      {
        key: "status",
        label: "Status",
        render: (r) => <StatusBadge value={r.status} />,
      },
      {
        key: "consistent",
        label: "Uyğunluq",
        render: (r) =>
          r.consistent == null
            ? "Gözləyir"
            : r.consistent
              ? "Uyğundur"
              : "Mismatch",
      },
    ]}
  />
);
export function CamerasPage() {
  const client = useQueryClient(),
    q = useData("vision", operationsApi.visionHealth),
    [editing, setEditing] = useState<any>(),
    [form, setForm] = useState({
      threshold: "0",
      trigger_frames: "15",
      clear_frames: "30",
      enabled: true,
    }),
    mutation = useMutation({
      mutationFn: () =>
        operationsApi.updateCameraRule(editing.id, {
          threshold: Number(form.threshold),
          trigger_frames: Number(form.trigger_frames),
          clear_frames: Number(form.clear_frames),
          enabled: form.enabled,
        }),
      onSuccess: () => {
        setEditing(null);
        client.invalidateQueries({ queryKey: ["vision"] });
      },
    }),
    rows = (q.data ?? []).flatMap((camera: any) =>
      camera.rules.map((rule: any) => ({
        ...rule,
        camera: camera.name,
        thumbnail_url: camera.thumbnail_url,
        source_type: camera.source_type,
      })),
    );
  function edit(row: any) {
    setEditing(row);
    setForm({
      threshold: String(row.threshold),
      trigger_frames: String(row.trigger_persistence),
      clear_frames: String(row.clear_persistence),
      enabled: row.enabled ?? true,
    });
  }
  return (
    <Page
      title="Filial kamera qaydaları"
      subtitle="MP4 simulyasiya mənbəyidir, RTSP deyil; hər hadisədə engine açıq göstərilir"
    >
      <section className="card">
        {q.isLoading ? (
          <Loading />
        ) : (
          <DataTable
            rows={rows}
            columns={[
              {
                key: "preview",
                label: "Görüntü",
                render: (r) => (
                  <img
                    className="thumb"
                    src={mediaUrl(r.thumbnail_url)}
                    alt={`${r.camera} thumbnail`}
                  />
                ),
              },
              { key: "camera", label: "Kamera" },
              { key: "rule_type", label: "Qayda" },
              { key: "detection_engine", label: "Engine" },
              { key: "roi", label: "ROI" },
              { key: "threshold", label: "Hədd" },
              {
                key: "persistence",
                label: "Persistence",
                render: (r) =>
                  `${r.trigger_persistence} / ${r.clear_persistence}`,
              },
              {
                key: "current_state",
                label: "State",
                render: (r) => <StatusBadge value={r.current_state} />,
              },
              {
                key: "approximate_fps",
                label: "Təxmini FPS",
                render: (r) => r.approximate_fps?.toFixed?.(1) ?? "—",
              },
              {
                key: "action",
                label: "Əməliyyat",
                render: (r) => (
                  <button
                    className="btn secondary small"
                    onClick={() => edit(r)}
                  >
                    Konfiqurasiya
                  </button>
                ),
              },
            ]}
          />
        )}
      </section>
      {editing ? (
        <Modal
          title="Kamera qaydasını yenilə"
          onClose={() => setEditing(null)}
          actions={
            <>
              <button
                className="btn secondary"
                onClick={() => setEditing(null)}
              >
                Ləğv et
              </button>
              <button
                className="btn"
                disabled={
                  Number(form.trigger_frames) < 2 ||
                  Number(form.clear_frames) < 2
                }
                onClick={() => mutation.mutate()}
              >
                Yadda saxla
              </button>
            </>
          }
        >
          <p>
            <b>{editing.camera}</b> · {editing.rule_type} ·{" "}
            {editing.detection_engine}
          </p>
          <label className="field">
            Hədd
            <input
              type="number"
              step=".01"
              min="0"
              max="100"
              value={form.threshold}
              onChange={(e) => setForm({ ...form, threshold: e.target.value })}
            />
          </label>
          <label className="field">
            Trigger persistence
            <input
              type="number"
              min="2"
              value={form.trigger_frames}
              onChange={(e) =>
                setForm({ ...form, trigger_frames: e.target.value })
              }
            />
          </label>
          <label className="field">
            Clear persistence
            <input
              type="number"
              min="2"
              value={form.clear_frames}
              onChange={(e) =>
                setForm({ ...form, clear_frames: e.target.value })
              }
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Aktiv
          </label>
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}
export function CameraEventsPage() {
  const client = useQueryClient(),
    q = useData("camera-events", operationsApi.cameraEvents),
    [falseAlertId,setFalseAlertId]=useState<string|null>(null),
    reject = useMutation({
      mutationFn: operationsApi.falseAlert,
      onSuccess: () => {
        setFalseAlertId(null);
        client.invalidateQueries({ queryKey: ["camera-events"] });
        client.invalidateQueries({ queryKey: ["incidents"] });
      },
    });
  return (
    <Page
      title="Kamera hadisələri"
      subtitle="Engine və evidence açıq göstərilir; hər tapıntı insan yoxlaması tələb edir"
    >
      <section className="card">
        <DataTable
          rows={q.data ?? []}
          columns={[
            { key: "rule", label: "Qayda" },
            { key: "detection_engine", label: "Engine" },
            { key: "roi", label: "ROI" },
            { key: "trigger_score", label: "Score" },
            { key: "detected_frames", label: "Trigger kadr" },
            { key: "clear_frames", label: "Clear kadr" },
            {
              key: "status",
              label: "Status",
              render: (r) => <StatusBadge value={r.status} />,
            },
            {
              key: "evidence",
              label: "Evidence",
              render: (r) =>
                r.evidence
                  ?.map((x: any) => `frame ${x.frame_number} · ${x.engine}`)
                  .join(", ") || "—",
            },
            {
              key: "actions",
              label: "Əməliyyat",
              render: (r) => (
                <button
                  className="btn danger small"
                  disabled={r.status === "REJECTED"}
                  onClick={() => setFalseAlertId(r.id)}
                >
                  Yanlış siqnal
                </button>
              ),
            },
          ]}
        />
      </section>
      {falseAlertId?<Modal title="Yanlış siqnalı təsdiqlə" onClose={()=>setFalseAlertId(null)} actions={<><button className="btn secondary" onClick={()=>setFalseAlertId(null)}>Ləğv et</button><button className="btn danger" onClick={()=>reject.mutate(falseAlertId)}>Yanlış siqnal kimi işarələ</button></>}><p>Hadisə rədd ediləcək və linked incident lifecycle tarixçəsinə administrator qərarı yazılacaq.</p></Modal>:null}
    </Page>
  );
}
export const BranchStaffPage = () => (
  <SimpleResource
    title="Filial əməkdaşları"
    subtitle="Audit performansı və izahedilə bilən keyfiyyət görünüşü"
    queryKey="staff"
    queryFn={operationsApi.staff}
    columns={[
      {
        key: "full_name",
        label: "Ad",
        render: (r) => (
          <DetailLink to={`/branch/staff/${r.id}`} label={r.full_name} />
        ),
      },
      { key: "email", label: "E-poçt" },
      {
        key: "is_active",
        label: "Aktiv",
        render: (r) => (r.is_active ? "Bəli" : "Xeyr"),
      },
    ]}
  />
);
export function BranchSettingsPage() {
  const client = useQueryClient(),
    q = useData("branches", operationsApi.branches),
    branch = q.data?.[0],
    mutation = useMutation({
      mutationFn: (form: any) => operationsApi.updateBranch(branch.id, form),
      onSuccess: () => client.invalidateQueries({ queryKey: ["branches"] }),
    });
  if (!branch) return <Loading />;
  return (
    <Page title="Filial ayarları" subtitle="Ad, ünvan, iş saatı və açıq status">
      <BranchForm initial={branch} onSave={(value) => mutation.mutate(value)} />
    </Page>
  );
}
function BranchForm({
  initial,
  onSave,
}: {
  initial: any;
  onSave: (v: any) => void;
}) {
  const [form, setForm] = useState({
    name: initial.name,
    address: initial.address,
    hours: initial.hours,
    is_open: initial.is_open,
    services: (initial.services ?? []).join(", "),
  });
  return (
    <form
      className="card form"
      onSubmit={(event) => {
        event.preventDefault();
        onSave({
          ...form,
          services: form.services
            .split(",")
            .map((x: string) => x.trim())
            .filter(Boolean),
        });
      }}
    >
      {["name", "address", "hours", "services"].map((key) => (
        <label className="field" key={key}>
          {key}
          <input
            value={(form as any)[key]}
            onChange={(e) => setForm({ ...form, [key]: e.target.value })}
          />
        </label>
      ))}
      <small className="muted">
        Xidmətləri vergüllə ayırın: PARKING, DELIVERY, ACCESSIBILITY
      </small>
      <label className="check">
        <input
          type="checkbox"
          checked={form.is_open}
          onChange={(e) => setForm({ ...form, is_open: e.target.checked })}
        />{" "}
        Filial açıqdır
      </label>
      <button className="btn">Yadda saxla</button>
    </form>
  );
}
