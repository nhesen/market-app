import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { logout, staffApi } from "../services/api";
import { Card, PageTitle, Screen, State, Status } from "../components/ui";
import { colors } from "../constants/theme";

const conditions = [
  "NORMAL",
  "EXPIRING_SOON",
  "EXPIRED",
  "DAMAGED",
  "INVALID_PRODUCT",
  "UNREADABLE",
];
type Section = "home" | "tasks" | "reaudits" | "quality";

export default function Staff() {
  const [section, setSection] = useState<Section>("home"),
    [filter, setFilter] = useState("ALL"),
    client = useQueryClient();
  const dashboard = useQuery({
    queryKey: ["staff-dashboard"],
    queryFn: staffApi.dashboard,
  });
  const tasks = useQuery({ queryKey: ["audits"], queryFn: staffApi.audits });
  const reAudits = useQuery({
    queryKey: ["re-audits"],
    queryFn: staffApi.reAudits,
  });
  const completeReAudit = useMutation({
    mutationFn: ({ id, condition }: { id: string; condition: string }) =>
      staffApi.completeReAudit(id, condition),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["re-audits"] });
      client.invalidateQueries({ queryKey: ["staff-dashboard"] });
    },
  });
  const rows = (tasks.data ?? []).filter(
    (item: any) => filter === "ALL" || item.status === filter,
  );
  function confirmLogout() {
    Alert.alert("Çıxış", "Staff hesabından çıxmaq istəyirsiniz?", [
      { text: "Ləğv et", style: "cancel" },
      {
        text: "Çıxış",
        style: "destructive",
        onPress: async () => {
          await logout();
          client.clear();
          router.replace("/login");
        },
      },
    ]);
  }
  return (
    <Screen>
      <View style={s.header}>
        <PageTitle
          title="Audit iş paneli"
          subtitle="Kamera dəstəkli məhsul və son istifadə tarixi yoxlaması"
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Çıxış"
          style={[
            s.logout,
            {
              minHeight: 44,
              paddingHorizontal: 13,
              flexDirection: "row",
              alignItems: "center",
              gap: 6,
            },
          ]}
          onPress={confirmLogout}
        >
          <Ionicons name="log-out-outline" size={20} color={colors.red} />
          <Text style={{ color: colors.red, fontWeight: "900" }}>Çıxış</Text>
        </Pressable>
      </View>
      <View style={s.nav}>
        {(
          [
            ["home", "grid-outline", "Xülasə"],
            ["tasks", "clipboard-outline", "Auditlər"],
            ["reaudits", "repeat-outline", "Təkrar"],
            ["quality", "shield-checkmark-outline", "Keyfiyyət"],
          ] as const
        ).map(([value, icon, label]) => (
          <Pressable
            key={value}
            style={[s.navItem, section === value && s.navActive]}
            onPress={() => setSection(value)}
          >
            <Ionicons
              name={icon}
              size={19}
              color={section === value ? colors.blue : colors.muted}
            />
            <Text style={section === value ? s.navTextActive : s.navText}>
              {label}
            </Text>
          </Pressable>
        ))}
      </View>
      <State
        loading={dashboard.isLoading || tasks.isLoading}
        error={dashboard.isError || tasks.isError}
        retry={() => {
          dashboard.refetch();
          tasks.refetch();
        }}
      />
      {section === "home" && dashboard.data ? (
        <>
          <View style={s.stats}>
            <Metric
              value={dashboard.data.today}
              label="Bugünkü audit"
              icon="today-outline"
            />
            <Metric
              value={dashboard.data.overdue}
              label="Gecikmiş"
              icon="time-outline"
              danger
            />
            <Metric
              value={dashboard.data.completed}
              label="Tamamlanan"
              icon="checkmark-circle-outline"
            />
            <Metric
              value={dashboard.data.re_audits}
              label="Təkrar audit"
              icon="repeat-outline"
            />
            <Metric
              value={dashboard.data.quality_flags}
              label="Keyfiyyət flagı"
              icon="flag-outline"
              danger
            />
            <Metric
              value={`${dashboard.data.average_duration_minutes} dəq`}
              label="Orta müddət"
              icon="speedometer-outline"
            />
            <Metric
              value={`${dashboard.data.completion_rate}%`}
              label="Tamamlanma"
              icon="analytics-outline"
            />
          </View>
          <Text style={s.section}>Son tapıntılar</Text>
          <State
            empty={
              !dashboard.data.recent_findings.length
                ? "Problemli tapıntı yoxdur."
                : undefined
            }
          />
          {dashboard.data.recent_findings.map((item: any) => (
            <Card key={item.id}>
              <View style={s.row}>
                <Text style={s.title}>{item.product}</Text>
                <Status value={item.condition} />
              </View>
              <Text style={s.muted}>
                {item.barcode} · {item.confirmed_date}
              </Text>
            </Card>
          ))}
        </>
      ) : null}
      {section === "tasks" ? (
        <>
          <Text style={s.section}>Audit tapşırıqları</Text>
          <View style={s.filters}>
            {["ALL", "ASSIGNED", "IN_PROGRESS", "COMPLETED"].map((value) => (
              <Pressable
                key={value}
                style={[s.filter, filter === value && s.active]}
                onPress={() => setFilter(value)}
              >
                <Text style={filter === value && s.activeText}>{value}</Text>
              </Pressable>
            ))}
          </View>
          <State
            empty={
              !rows.length ? "Bu bölmədə audit tapşırığı yoxdur." : undefined
            }
          />
          {rows.map((task: any) => (
            <Card
              key={task.id}
              onPress={() =>
                router.push({ pathname: "/audit", params: { id: task.id } })
              }
            >
              <View style={s.row}>
                <Status value={task.status} />
                <Text style={s.priority}>{task.priority}</Text>
              </View>
              <Text style={s.title}>{task.title}</Text>
              <Text style={s.muted}>{task.instructions}</Text>
              <Text style={s.meta}>
                {task.item_count}/{task.required_count} məhsul · {task.progress}
                %
              </Text>
              <Text
                style={
                  new Date(task.due_at) < new Date() &&
                  task.status !== "COMPLETED"
                    ? s.danger
                    : s.muted
                }
              >
                Son vaxt: {new Date(task.due_at).toLocaleString("az-AZ")}
              </Text>
            </Card>
          ))}
        </>
      ) : null}
      {section === "reaudits" ? (
        <>
          <Text style={s.section}>Təkrar auditlər</Text>
          <State
            loading={reAudits.isLoading}
            error={reAudits.isError}
            empty={
              !reAudits.data?.length
                ? "Təyin edilmiş təkrar audit yoxdur."
                : undefined
            }
            retry={() => reAudits.refetch()}
          />
          {reAudits.data?.map((item: any) => (
            <Card key={item.id}>
              <View style={s.row}>
                <Text style={s.title}>{item.original_title}</Text>
                <Status value={item.status} />
              </View>
              <Text style={s.muted}>
                Məhsul: {item.original_item?.product} ·{" "}
                {item.original_item?.barcode}
              </Text>
              <View style={s.compare}>
                <View>
                  <Text style={s.small}>İlkin nəticə</Text>
                  <Text style={s.original}>{item.original_condition}</Text>
                </View>
                {item.re_audit_condition ? (
                  <View>
                    <Text style={s.small}>Təkrar nəticə</Text>
                    <Text style={item.consistent ? s.ok : s.danger}>
                      {item.re_audit_condition}
                    </Text>
                  </View>
                ) : null}
              </View>
              {item.status === "ASSIGNED" ? (
                <>
                  <Text style={s.label}>
                    Müstəqil yoxlamanın nəticəsini seçin
                  </Text>
                  <View style={s.conditions}>
                    {conditions.map((condition) => (
                      <Pressable
                        key={condition}
                        style={s.condition}
                        onPress={() =>
                          completeReAudit.mutate({ id: item.id, condition })
                        }
                      >
                        <Text style={s.conditionText}>{condition}</Text>
                      </Pressable>
                    ))}
                  </View>
                </>
              ) : (
                <Text style={item.consistent ? s.ok : s.danger}>
                  {item.consistent
                    ? "Nəticələr uyğundur"
                    : "Uyğunsuzluq flag kimi saxlanıldı"}
                </Text>
              )}
            </Card>
          ))}
        </>
      ) : null}
      {section === "quality" ? (
        <>
          <Text style={s.section}>Keyfiyyət nəzarəti</Text>
          <Text style={s.muted}>
            Bu göstəricilər proses yoxlaması üçündür, avtomatik intizam qərarı
            deyil.
          </Text>
          <State
            empty={
              !dashboard.data?.flags.length
                ? "Keyfiyyət flagı yoxdur."
                : undefined
            }
          />
          {dashboard.data?.flags.map((flag: any) => (
            <Card key={flag.id}>
              <View style={s.row}>
                <Text style={s.flagCode}>{flag.code}</Text>
                <Text style={flag.severity === "ERROR" ? s.danger : s.warning}>
                  {flag.severity}
                </Text>
              </View>
              <Text>{flag.message}</Text>
              <Text style={s.small}>
                {new Date(flag.created_at).toLocaleString("az-AZ")}
              </Text>
            </Card>
          ))}
        </>
      ) : null}
    </Screen>
  );
}

function Metric({
  value,
  label,
  icon,
  danger,
}: {
  value: string | number;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  danger?: boolean;
}) {
  return (
    <View style={s.metric}>
      <Ionicons
        name={icon}
        size={21}
        color={danger ? colors.red : colors.blue}
      />
      <Text style={[s.num, danger && s.danger]}>{value}</Text>
      <Text style={s.metricLabel}>{label}</Text>
    </View>
  );
}
const s = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "flex-start" },
  logout: {
    marginLeft: "auto",
    padding: 11,
    backgroundColor: "white",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.border,
  },
  nav: {
    flexDirection: "row",
    backgroundColor: "white",
    padding: 5,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  navItem: { flex: 1, alignItems: "center", paddingVertical: 8, gap: 3 },
  navActive: { backgroundColor: colors.softBlue, borderRadius: 12 },
  navText: { fontSize: 10, color: colors.muted },
  navTextActive: { fontSize: 10, color: colors.blue, fontWeight: "900" },
  stats: { flexDirection: "row", flexWrap: "wrap", gap: 9 },
  metric: {
    width: "48%",
    padding: 14,
    borderRadius: 16,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    gap: 4,
  },
  num: { fontSize: 22, fontWeight: "900", color: colors.blue },
  metricLabel: { color: colors.muted, fontSize: 12 },
  section: {
    fontSize: 19,
    fontWeight: "900",
    color: colors.navy,
    marginTop: 5,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 9,
  },
  title: { fontSize: 17, fontWeight: "900", color: colors.navy, flex: 1 },
  muted: { color: colors.muted, lineHeight: 19 },
  meta: { color: colors.blue, fontWeight: "800" },
  priority: { fontWeight: "900", color: colors.red },
  danger: { color: colors.red, fontWeight: "900" },
  warning: { color: "#996000", fontWeight: "900" },
  ok: { color: colors.green, fontWeight: "900" },
  filters: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  filter: {
    padding: 9,
    borderRadius: 9,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
  },
  active: { backgroundColor: colors.softBlue, borderColor: colors.blue },
  activeText: { color: colors.blue, fontWeight: "800" },
  compare: {
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 12,
    backgroundColor: colors.softBlue,
    borderRadius: 12,
  },
  small: { fontSize: 11, color: colors.muted },
  original: { fontWeight: "900", color: colors.navy },
  label: { fontWeight: "800", color: colors.navy },
  conditions: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  condition: { padding: 8, borderRadius: 8, backgroundColor: colors.softBlue },
  conditionText: { fontSize: 10, color: colors.blue, fontWeight: "900" },
  flagCode: { fontWeight: "900", color: colors.navy },
});
