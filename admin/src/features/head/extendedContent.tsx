import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { contentApi, operationsApi } from "../../services/api";
import {
  DataTable,
  Loading,
  Modal,
  Page,
  StatusBadge,
} from "../../components/ui";

const offerSchema = z.object({
  title_az: z.string().min(2),
  title_en: z.string().min(2),
  description_az: z.string().min(2),
  description_en: z.string().min(2),
  points_cost: z.number().int().min(0),
  image_url: z.string().min(1),
  valid_until: z.string().min(1),
  active: z.boolean(),
});
type OfferForm = z.infer<typeof offerSchema>;
const emptyOffer: OfferForm = {
  title_az: "",
  title_en: "",
  description_az: "",
  description_en: "",
  points_cost: 100,
  image_url: "/assets/reward.svg",
  valid_until: "",
  active: true,
};
export function LoyaltyOffersPage() {
  const client = useQueryClient(),
    q = useQuery({
      queryKey: ["loyalty-offers"],
      queryFn: contentApi.loyaltyOffers,
    }),
    [open, setOpen] = useState(false),
    [editing, setEditing] = useState<{ id: string } & OfferForm>(),
    form = useForm<OfferForm>({
      resolver: zodResolver(offerSchema),
      defaultValues: emptyOffer,
    }),
    mutation = useMutation({
      mutationFn: (value: OfferForm) =>
        editing
          ? contentApi.updateLoyaltyOffer(editing.id, value)
          : contentApi.createLoyaltyOffer(value),
      onSuccess: () => {
        setOpen(false);
        setEditing(undefined);
        form.reset(emptyOffer);
        client.invalidateQueries({ queryKey: ["loyalty-offers"] });
      },
    }),
    remove = useMutation({
      mutationFn: contentApi.deleteLoyaltyOffer,
      onSuccess: () =>
        client.invalidateQueries({ queryKey: ["loyalty-offers"] }),
    });
  function show(item?: { id: string } & OfferForm) {
    setEditing(item);
    form.reset(item ?? emptyOffer);
    setOpen(true);
  }
  return (
    <Page
      title="Loyalty təklifləri"
      subtitle="Organisation-a scoped bonus təklifləri və müştəri tətbiqində görünürlük"
      actions={
        <button className="btn" onClick={() => show()}>
          + Təklif yarat
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
              { key: "title_az", label: "Başlıq" },
              { key: "points_cost", label: "Bonus qiyməti" },
              { key: "valid_until", label: "Son tarix" },
              {
                key: "active",
                label: "Status",
                render: (r) => (
                  <StatusBadge value={r.active ? "ACTIVE" : "INACTIVE"} />
                ),
              },
              {
                key: "actions",
                label: "Əməliyyat",
                render: (r) => (
                  <div className="inline">
                    <button
                      className="btn secondary small"
                      onClick={() => show(r)}
                    >
                      Redaktə
                    </button>
                    <button
                      className="btn danger small"
                      onClick={() => remove.mutate(r.id)}
                    >
                      Sil
                    </button>
                  </div>
                ),
              },
            ]}
          />
        )}
      </section>
      {open ? (
        <Modal
          title={
            editing ? "Loyalty təklifini redaktə et" : "Loyalty təklifi yarat"
          }
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
          <div className="form">
            {[
              ["title_az", "Başlıq AZ"],
              ["title_en", "Başlıq EN"],
              ["description_az", "Təsvir AZ"],
              ["description_en", "Təsvir EN"],
              ["image_url", "Şəkil URL"],
            ].map(([key, label]) => (
              <label className="field" key={key}>
                {label}
                <input {...form.register(key as keyof OfferForm)} />
              </label>
            ))}
            <label className="field">
              Bonus qiyməti
              <input type="number" {...form.register("points_cost", { valueAsNumber: true })} />
            </label>
            <label className="field">
              Son tarix
              <input type="date" {...form.register("valid_until")} />
            </label>
            <label className="check">
              <input type="checkbox" {...form.register("active")} />
              Aktiv
            </label>
          </div>
          {mutation.error ? (
            <p className="error">{mutation.error.message}</p>
          ) : null}
        </Modal>
      ) : null}
    </Page>
  );
}

const linkSchema = z.object({
  product_id: z.string().min(1),
  branch_id: z.string().min(1),
  discount_price: z.number().positive(),
});
type LinkForm = z.infer<typeof linkSchema>;
export function CampaignProductsPage() {
  const { id } = useParams(),
    client = useQueryClient(),
    links = useQuery({
      queryKey: ["campaign-products", id],
      queryFn: () => contentApi.campaignProducts(id!),
    }),
    products = useQuery({
      queryKey: ["products"],
      queryFn: contentApi.products,
    }),
    branches = useQuery({
      queryKey: ["branches"],
      queryFn: operationsApi.branches,
    }),
    form = useForm<LinkForm>({
      resolver: zodResolver(linkSchema),
      defaultValues: { product_id: "", branch_id: "", discount_price: 0 },
    }),
    add = useMutation({
      mutationFn: (value: LinkForm) =>
        contentApi.addCampaignProduct(id!, value),
      onSuccess: () =>
        client.invalidateQueries({ queryKey: ["campaign-products", id] }),
    }),
    remove = useMutation({
      mutationFn: contentApi.deleteCampaignProduct,
      onSuccess: () =>
        client.invalidateQueries({ queryKey: ["campaign-products", id] }),
    });
  return (
    <Page
      title="Kampaniya məhsulları"
      subtitle="Məhsul, filial və endirim qiyməti əlaqələri"
    >
      <div className="content">
        <form
          className="card form"
          onSubmit={form.handleSubmit((v) => add.mutate(v))}
        >
          <label className="field">
            Məhsul
            <select {...form.register("product_id")}>
              <option value="">Seçin</option>
              {products.data?.map((x) => (
                <option value={x.id} key={x.id}>
                  {x.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Filial
            <select {...form.register("branch_id")}>
              <option value="">Seçin</option>
              {branches.data?.map((x) => (
                <option value={x.id} key={x.id}>
                  {x.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Endirim qiyməti
            <input
              type="number"
              step=".01"
              {...form.register("discount_price", { valueAsNumber: true })}
            />
          </label>
          <button className="btn">Əlavə et</button>
          {add.error ? <p className="error">{add.error.message}</p> : null}
        </form>
        <section className="card">
          <DataTable
            rows={links.data ?? []}
            columns={[
              { key: "product_id", label: "Məhsul ID" },
              { key: "branch_id", label: "Filial ID" },
              { key: "discount_price", label: "Endirim qiyməti" },
              {
                key: "action",
                label: "Əməliyyat",
                render: (r) => (
                  <button
                    className="btn danger small"
                    onClick={() => remove.mutate(r.id)}
                  >
                    Sil
                  </button>
                ),
              },
            ]}
          />
        </section>
      </div>
    </Page>
  );
}
