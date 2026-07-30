import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, UseFormReturn } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { operationsApi } from "../../services/api";
import {
  DataTable,
  Loading,
  MediaViewer,
  Modal,
  Page,
  StatusBadge,
} from "../../components/ui";

type Template = {
  id: string;
  name: string;
  description: string;
  category: string;
  branch_id?: string;
  required_product_count: number;
  require_unique_products: boolean;
  require_photo: boolean;
  require_expiry_date: boolean;
  default_priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  expected_min_duration_seconds: number;
  recurrence_type: "NONE" | "DAILY" | "WEEKLY" | "MONTHLY";
  active: boolean;
  updated_at: string;
};
type Staff = {
  id: string;
  full_name: string;
  email: string;
  branch_id: string;
  is_active: boolean;
};
type Audit = {
  id: string;
  title: string;
  assignee_id: string;
  priority: string;
  status: string;
  item_count: number;
  required_count: number;
  due_at: string;
  completed_at?: string;
};
const templateSchema = z.object({
  name: z.string().min(3),
  description: z.string().min(3),
  category: z.string().min(2),
  required_product_count: z.number().int().min(1).max(100),
  require_unique_products: z.boolean(),
  require_photo: z.boolean(),
  require_expiry_date: z.boolean(),
  default_priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  expected_min_duration_seconds: z.number().int().min(30),
  recurrence_type: z.enum(["NONE", "DAILY", "WEEKLY", "MONTHLY"]),
  active: z.boolean(),
  branch_id: z.string().optional(),
});
type TemplateForm = z.infer<typeof templateSchema>;
const taskSchema = z.object({
  template_id: z.string().min(1),
  assignee_id: z.string().min(1),
  due_at: z.string().min(1),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  instructions: z.string().max(3000).optional(),
});
type TaskForm = z.infer<typeof taskSchema>;
const reauditSchema = z.object({
  original_task_id: z.string().min(1),
  assignee_id: z.string().min(1),
  due_at: z.string().min(1),
});
type ReauditForm = z.infer<typeof reauditSchema>;

export function AuditTemplatesPage() {
  const client = useQueryClient(),
    q = useQuery<Template[]>({
      queryKey: ["audit-templates"],
      queryFn: operationsApi.templates,
    }),
    [open, setOpen] = useState(false),
    [editing, setEditing] = useState<Template>();
  const form = useForm<TemplateForm>({
    resolver: zodResolver(templateSchema),
    defaultValues: emptyTemplate,
  });
  const mutation = useMutation({
    mutationFn: (value: TemplateForm) =>
      editing
        ? operationsApi.updateTemplate(editing.id, value)
        : operationsApi.createTemplate(value),
    onSuccess: () => {
      setOpen(false);
      setEditing(undefined);
      form.reset(emptyTemplate);
      client.invalidateQueries({ queryKey: ["audit-templates"] });
    },
  });
  function show(item?: Template) {
    setEditing(item);
    form.reset(item ? { ...item } : emptyTemplate);
    setOpen(true);
  }
  return (
    <Page
      title="Audit şablonları"
      subtitle="Təkrar istifadə edilən, filial və təşkilat səviyyəli audit qaydaları"
      actions={
        <button className="btn" onClick={() => show()}>
          + Şablon yarat
        </button>
      }
    >
      <section className="card">
        {q.isLoading ? (
          <Loading />
        ) : (
          <DataTable
            rows={q.data ?? []}
            columns={[
              { key: "name", label: "Ad" },
              { key: "category", label: "Kateqoriya" },
              { key: "required_product_count", label: "Məhsul sayı" },
              {
                key: "require_photo",
                label: "Foto",
                render: (r) => (r.require_photo ? "Bəli" : "Xeyr"),
              },
              {
                key: "require_unique_products",
                label: "Unikal məhsul",
                render: (r) => (r.require_unique_products ? "Bəli" : "Xeyr"),
              },
              {
                key: "active",
                label: "Aktiv",
                render: (r) => (
                  <StatusBadge value={r.active ? "ACTIVE" : "INACTIVE"} />
                ),
              },
              {
                key: "action",
                label: "Əməliyyat",
                render: (r) => (
                  <button
                    className="btn secondary small"
                    onClick={() => show(r)}
                  >
                    Redaktə
                  </button>
                ),
              },
            ]}
          />
        )}
      </section>
      {open ? (
        <Modal
          title={editing ? "Audit şablonunu redaktə et" : "Audit şablonu yarat"}
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button
                className="btn"
                onClick={form.handleSubmit((v) => mutation.mutate(v))}
              >
                Yadda saxla
              </button>
            </>
          }
        >
          <TemplateFields form={form} />
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}

export function AuditManagementPage() {
  const client = useQueryClient(),
    audits = useQuery<Audit[]>({
      queryKey: ["audits"],
      queryFn: operationsApi.audits,
    }),
    templates = useQuery<Template[]>({
      queryKey: ["audit-templates"],
      queryFn: operationsApi.templates,
    }),
    staff = useQuery<Staff[]>({
      queryKey: ["staff"],
      queryFn: operationsApi.staff,
    }),
    [open, setOpen] = useState(false);
  const form = useForm<TaskForm>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      template_id: "",
      assignee_id: "",
      due_at: "",
      priority: "MEDIUM",
      instructions: "",
    },
  });
  const mutation = useMutation({
    mutationFn: (v: TaskForm) =>
      operationsApi.assignAudit({
        ...v,
        due_at: new Date(v.due_at).toISOString(),
      }),
    onSuccess: () => {
      setOpen(false);
      form.reset();
      client.invalidateQueries({ queryKey: ["audits"] });
    },
  });
  return (
    <Page
      title="Staff auditləri"
      subtitle="Şablondan audit yaradın, əməkdaşa təyin edin və nəticəni izləyin"
      actions={
        <div className="inline">
          <Link className="btn secondary" to="/branch/audit-templates">
            Şablonlar
          </Link>
          <button className="btn" onClick={() => setOpen(true)}>
            + Audit təyin et
          </button>
        </div>
      }
    >
      <section className="card">
        {audits.isLoading ? (
          <Loading />
        ) : (
          <DataTable
            rows={audits.data ?? []}
            columns={[
              {
                key: "title",
                label: "Tapşırıq",
                render: (r) => (
                  <Link to={`/branch/audits/${r.id}`}>{r.title}</Link>
                ),
              },
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
              {
                key: "item_count",
                label: "Progress",
                render: (r) => `${r.item_count}/${r.required_count}`,
              },
              {
                key: "due_at",
                label: "Son vaxt",
                render: (r) => new Date(r.due_at).toLocaleString("az-AZ"),
              },
            ]}
          />
        )}
      </section>
      {open ? (
        <Modal
          title="Audit tapşırığı təyin et"
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button
                className="btn"
                onClick={form.handleSubmit((v) => mutation.mutate(v))}
              >
                Təyin et
              </button>
            </>
          }
        >
          <label className="field">
            Şablon
            <select {...form.register("template_id")}>
              <option value="">Seçin</option>
              {templates.data
                ?.filter((x) => x.active)
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
            </select>
            <Error text={form.formState.errors.template_id?.message} />
          </label>
          <label className="field">
            Əməkdaş
            <select {...form.register("assignee_id")}>
              <option value="">Seçin</option>
              {staff.data
                ?.filter((x) => x.is_active)
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.full_name}
                  </option>
                ))}
            </select>
            <Error text={form.formState.errors.assignee_id?.message} />
          </label>
          <label className="field">
            Son tarix
            <input type="datetime-local" {...form.register("due_at")} />
            <Error text={form.formState.errors.due_at?.message} />
          </label>
          <label className="field">
            Prioritet
            <select {...form.register("priority")}>
              <option>LOW</option>
              <option>MEDIUM</option>
              <option>HIGH</option>
              <option>CRITICAL</option>
            </select>
          </label>
          <label className="field">
            Əlavə təlimat
            <textarea {...form.register("instructions")} />
          </label>
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}

export function AuditDetailPage() {
  const { id } = useParams(),
    q = useQuery({
      queryKey: ["audit", id],
      queryFn: () => operationsApi.audit(id!),
    });
  if (q.isLoading) return <Loading />;
  if (q.error || !q.data) return <Loading error={q.error} />;
  const x = q.data;
  const duration =
    x.started_at && x.completed_at
      ? Math.round(
          (new Date(x.completed_at).getTime() -
            new Date(x.started_at).getTime()) /
            60000,
        )
      : null;
  return (
    <Page
      title={x.title}
      subtitle={`${x.item_count}/${x.required_count} məhsul · ${x.priority}`}
    >
      <div className="case">
        <section>
          <div className="grid">
            <div className="card">
              <b>Status</b>
              <StatusBadge value={x.status} />
            </div>
            <div className="card">
              <b>Müddət</b>
              <strong>{duration ?? "—"} dəq</strong>
            </div>
          </div>
          <h2>Audit məhsulları</h2>
          {x.items.map(
            (item: {
              id: string;
              product: string;
              barcode: string;
              confirmed_date?: string;
              condition: string;
              photo_key?: string;
              ocr_corrected: boolean;
              note?: string;
            }) => (
              <article className="card spaced" key={item.id}>
                <div className="inline">
                  <h3>{item.product}</h3>
                  <StatusBadge value={item.condition} />
                </div>
                <p>
                  {item.barcode} · {item.confirmed_date ?? "Tarix yoxdur"}
                </p>
                <p>OCR düzəlişi: {item.ocr_corrected ? "Bəli" : "Xeyr"}</p>
                {item.note ? <p>{item.note}</p> : null}
                {item.photo_key ? (
                  <MediaViewer
                    media={[
                      {
                        url: item.photo_key,
                        mime_type: "image/jpeg",
                        name: item.product,
                      },
                    ]}
                  />
                ) : null}
              </article>
            ),
          )}
        </section>
        <aside className="card">
          <h2>Keyfiyyət flagları</h2>
          {x.quality_flags.length ? (
            x.quality_flags.map(
              (flag: {
                id: string;
                code: string;
                message: string;
                severity: string;
              }) => (
                <div className="event" key={flag.id}>
                  <StatusBadge value={flag.severity} />
                  <b>{flag.code}</b>
                  <p>{flag.message}</p>
                </div>
              ),
            )
          ) : (
            <p className="muted">Flag yoxdur</p>
          )}
        </aside>
      </div>
    </Page>
  );
}

export function ReAuditManagementPage() {
  const client = useQueryClient(),
    q = useQuery({ queryKey: ["reaudits"], queryFn: operationsApi.reaudits }),
    audits = useQuery<Audit[]>({
      queryKey: ["audits"],
      queryFn: operationsApi.audits,
    }),
    staff = useQuery<Staff[]>({
      queryKey: ["staff"],
      queryFn: operationsApi.staff,
    }),
    [open, setOpen] = useState(false),
    form = useForm<ReauditForm>({
      resolver: zodResolver(reauditSchema),
      defaultValues: { original_task_id: "", assignee_id: "", due_at: "" },
    }),
    mutation = useMutation({
      mutationFn: (v: ReauditForm) =>
        operationsApi.createReaudit({
          ...v,
          due_at: new Date(v.due_at).toISOString(),
        }),
      onSuccess: () => {
        setOpen(false);
        client.invalidateQueries({ queryKey: ["reaudits"] });
      },
    });
  return (
    <Page
      title="Təkrar auditlər"
      subtitle="Tamamlanmış auditə başqa əməkdaşla nəzarət təyin edin"
      actions={
        <button className="btn" onClick={() => setOpen(true)}>
          + Təkrar audit
        </button>
      }
    >
      <section className="card">
        <DataTable
          rows={q.data ?? []}
          columns={[
            { key: "original_title", label: "İlkin audit" },
            {
              key: "status",
              label: "Status",
              render: (r) => <StatusBadge value={r.status} />,
            },
            { key: "original_condition", label: "İlkin" },
            { key: "re_audit_condition", label: "Təkrar" },
            {
              key: "consistent",
              label: "Uyğunluq",
              render: (r) =>
                r.consistent == null
                  ? "Gözləyir"
                  : r.consistent
                    ? "Uyğundur"
                    : "Uyğun deyil",
            },
            {
              key: "due_at",
              label: "Son vaxt",
              render: (r) =>
                r.due_at ? new Date(r.due_at).toLocaleString("az-AZ") : "—",
            },
          ]}
        />
      </section>
      {open ? (
        <Modal
          title="Təkrar audit təyin et"
          onClose={() => setOpen(false)}
          actions={
            <>
              <button className="btn secondary" onClick={() => setOpen(false)}>
                Ləğv et
              </button>
              <button
                className="btn"
                onClick={form.handleSubmit((v) => mutation.mutate(v))}
              >
                Təyin et
              </button>
            </>
          }
        >
          <label className="field">
            Tamamlanmış audit
            <select {...form.register("original_task_id")}>
              <option value="">Seçin</option>
              {audits.data
                ?.filter((x) => x.status === "COMPLETED")
                .map((x) => (
                  <option value={x.id} key={x.id}>
                    {x.title}
                  </option>
                ))}
            </select>
          </label>
          <label className="field">
            Başqa əməkdaş
            <select {...form.register("assignee_id")}>
              <option value="">Seçin</option>
              {staff.data?.map((x) => (
                <option value={x.id} key={x.id}>
                  {x.full_name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Son tarix
            <input type="datetime-local" {...form.register("due_at")} />
          </label>
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}

export function StaffQualityDetailPage() {
  const { id } = useParams(),
    staff = useQuery<Staff[]>({
      queryKey: ["staff"],
      queryFn: operationsApi.staff,
    }),
    q = useQuery({
      queryKey: ["staff-quality", id],
      queryFn: () => operationsApi.staffQuality(id!),
    });
  if (q.isLoading) return <Loading />;
  const person = staff.data?.find((x) => x.id === id);
  return (
    <Page
      title={person?.full_name ?? "Əməkdaş keyfiyyəti"}
      subtitle="İzahedilə bilən proses göstəricisi; avtomatik intizam qərarı deyil"
    >
      <div className="grid">
        <div className="card stat">
          <span>Quality score</span>
          <strong>{q.data.score}/100</strong>
        </div>
        <div className="card stat">
          <span>Completion</span>
          <strong>{q.data.completion_rate}%</strong>
        </div>
        <div className="card stat">
          <span>Orta müddət</span>
          <strong>{q.data.average_duration_minutes} dəq</strong>
        </div>
        <div className="card stat">
          <span>Re-audit consistency</span>
          <strong>{q.data.re_audit_consistency}%</strong>
        </div>
      </div>
      <section className="card spaced">
        <h2>Töhfə verən amillər</h2>
        <p>{q.data.explanation}</p>
        <DataTable
          rows={Object.entries(q.data.flags_by_type ?? {}).map(
            ([code, count]) => ({ id: code, code, count }),
          )}
          columns={[
            { key: "code", label: "Flag" },
            { key: "count", label: "Say" },
          ]}
        />
      </section>
    </Page>
  );
}

function TemplateFields({ form }: { form: UseFormReturn<TemplateForm> }) {
  return (
    <div className="form">
      <label className="field">
        Ad
        <input {...form.register("name")} />
        <Error text={form.formState.errors.name?.message} />
      </label>
      <label className="field">
        Təsvir
        <textarea {...form.register("description")} />
      </label>
      <label className="field">
        Kateqoriya
        <input {...form.register("category")} />
      </label>
      <label className="field">
        Məhsul sayı
        <input
          type="number"
          {...form.register("required_product_count", { valueAsNumber: true })}
        />
      </label>
      <label className="field">
        Minimum müddət (saniyə)
        <input
          type="number"
          {...form.register("expected_min_duration_seconds", {
            valueAsNumber: true,
          })}
        />
      </label>
      <label className="field">
        Prioritet
        <select {...form.register("default_priority")}>
          <option>LOW</option>
          <option>MEDIUM</option>
          <option>HIGH</option>
          <option>CRITICAL</option>
        </select>
      </label>
      <label className="field">
        Təkrarlanma
        <select {...form.register("recurrence_type")}>
          <option>NONE</option>
          <option>DAILY</option>
          <option>WEEKLY</option>
          <option>MONTHLY</option>
        </select>
      </label>
      {[
        ["require_unique_products", "Unikal məhsullar"],
        ["require_photo", "Foto tələb olunur"],
        ["require_expiry_date", "Son istifadə tarixi tələb olunur"],
        ["active", "Aktiv"],
      ].map(([key, label]) => (
        <label className="check" key={key}>
          <input
            type="checkbox"
            {...form.register(
              key as
                | "require_unique_products"
                | "require_photo"
                | "require_expiry_date"
                | "active",
            )}
          />
          {label}
        </label>
      ))}
    </div>
  );
}
function Error({ text }: { text?: string }) {
  return text ? <small className="error">{text}</small> : null;
}
const emptyTemplate: TemplateForm = {
  name: "",
  description: "",
  category: "PRODUCT",
  required_product_count: 3,
  require_unique_products: true,
  require_photo: true,
  require_expiry_date: true,
  default_priority: "MEDIUM",
  expected_min_duration_seconds: 60,
  recurrence_type: "NONE",
  active: true,
  branch_id: "",
};
