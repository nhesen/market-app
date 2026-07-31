import { useEffect } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, logout, restoreSession } from "../services/api";
import { useI18n } from "../services/i18n";
import { Card, PageTitle, Screen, State, Status } from "../components/ui";
import { colors, radius, spacing } from "../constants/theme";

const adminRoles = ["BRANCH_ADMIN", "HEAD_OFFICE_ADMIN", "PLATFORM_ADMIN"];

export default function AdminMobile({
  expectedRole,
}: { expectedRole?: string } = {}) {
  const { t } = useI18n(),
    client = useQueryClient();
  const me = useQuery({
    queryKey: ["admin-mobile-me"],
    queryFn: restoreSession,
  });
  const role = me.data?.role,
    isTenant = role === "BRANCH_ADMIN" || role === "HEAD_OFFICE_ADMIN",
    isHead = role === "HEAD_OFFICE_ADMIN",
    isPlatform = role === "PLATFORM_ADMIN";
  useEffect(() => {
    if (!me.data) return;
    if (!adminRoles.includes(me.data.role)) {
      router.replace(me.data.role === "STAFF" ? "/staff" : "/");
      return;
    }
    if (expectedRole && me.data.role !== expectedRole) {
      const target =
        me.data.role === "BRANCH_ADMIN"
          ? "/branch-admin"
          : me.data.role === "HEAD_OFFICE_ADMIN"
            ? "/head-admin"
            : "/platform-admin";
      router.replace(target as never);
    }
  }, [me.data, expectedRole]);
  const dashboard = useQuery({
    queryKey: ["admin-mobile-dashboard"],
    queryFn: adminApi.dashboard,
    enabled: Boolean(role),
  });
  const incidents = useQuery({
    queryKey: ["admin-mobile-incidents"],
    queryFn: adminApi.incidents,
    enabled: Boolean(role),
  });
  const reports = useQuery({
    queryKey: ["admin-mobile-reports"],
    queryFn: adminApi.reports,
    enabled: isTenant,
  });
  const audits = useQuery({
    queryKey: ["admin-mobile-audits"],
    queryFn: adminApi.audits,
    enabled: isTenant,
  });
  const network = useQuery({
    queryKey: ["admin-mobile-network"],
    queryFn: adminApi.network,
    enabled: isHead,
  });
  const analytics = useQuery({
    queryKey: ["admin-mobile-analytics"],
    queryFn: adminApi.analytics,
    enabled: isTenant,
  });
  const health = useQuery({
    queryKey: ["admin-mobile-health"],
    queryFn: adminApi.platformHealth,
    enabled: isPlatform,
  });
  const organisations = useQuery({
    queryKey: ["admin-mobile-organisations"],
    queryFn: adminApi.organisations,
    enabled: isPlatform,
  });
  const usage = useQuery({
    queryKey: ["admin-mobile-usage"],
    queryFn: adminApi.tenantUsage,
    enabled: isPlatform,
  });
  const queries = [
      dashboard,
      incidents,
      reports,
      audits,
      network,
      analytics,
      health,
      organisations,
      usage,
    ],
    active = queries.filter(
      (q) => q.fetchStatus !== "idle" || q.data !== undefined,
    );
  const loading = me.isLoading || active.some((q) => q.isLoading),
    error = me.isError || active.some((q) => q.isError),
    refreshing = active.some((q) => q.isRefetching);
  function refresh() {
    me.refetch();
    active.forEach((q) => q.refetch());
  }
  function signOut() {
    Alert.alert(t("logout"), t("adminLogoutConfirm"), [
      { text: t("cancel"), style: "cancel" },
      {
        text: t("yesLogout"),
        style: "destructive",
        onPress: async () => {
          await logout();
          client.clear();
          router.replace("/login");
        },
      },
    ]);
  }
  const roleTitle =
    role === "BRANCH_ADMIN"
      ? t("branchAdmin")
      : role === "HEAD_OFFICE_ADMIN"
        ? t("headAdmin")
        : t("platformAdmin");
  return (
    <Screen refreshing={refreshing} onRefresh={refresh}>
      <View style={s.top}>
        <View style={s.logo}>
          <Ionicons name="shield-checkmark" size={25} color="white" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.brand}>MARTIQ</Text>
          <Text style={s.role}>{roleTitle}</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("logout")}
          style={s.logout}
          onPress={signOut}
        >
          <Ionicons name="log-out-outline" size={23} color={colors.red} />
        </Pressable>
      </View>
      <PageTitle
        title={t("adminMobile")}
        subtitle={`${me.data?.full_name ?? ""} · ${t("adminWelcome")}`}
      />
      <State loading={loading && !me.data} error={error} retry={refresh} />
      {dashboard.data ? (
        <View style={s.metrics}>
          <Metric
            icon="alert-circle"
            label={t("openIncidents")}
            value={dashboard.data.open_incidents}
          />
          <Metric
            icon="warning"
            label={t("highRisk")}
            value={dashboard.data.high_risk}
          />
          <Metric
            icon="checkmark-circle"
            label={t("resolved")}
            value={dashboard.data.resolved}
          />
          <Metric
            icon="analytics"
            label={t("storeScore")}
            value={dashboard.data.smart_store_score}
          />
        </View>
      ) : null}
      {isTenant && analytics.data ? (
        <Card>
          <Text style={s.section}>{t("totalRecords")}</Text>
          <View style={s.inline}>
            <Small
              label={t("incidents")}
              value={analytics.data.summary.total}
            />
            <Small
              label={t("overdue")}
              value={analytics.data.summary.overdue}
            />
            <Small
              label={t("resolved")}
              value={analytics.data.summary.resolved}
            />
          </View>
        </Card>
      ) : null}
      {isHead ? (
        <>
          <Text style={s.section}>{t("networkBranches")}</Text>
          {network.data?.map((x: any) => (
            <Card key={x.branch_id}>
              <View style={s.row}>
                <View style={{ flex: 1 }}>
                  <Text style={s.itemTitle}>{x.branch}</Text>
                  <Text style={s.meta}>
                    {t("openIncidents")}: {x.open_incidents} · {t("highRisk")}:{" "}
                    {x.high_risk}
                  </Text>
                </View>
                <Text style={s.score}>{x.score}</Text>
              </View>
            </Card>
          ))}
        </>
      ) : null}
      {isPlatform ? (
        <>
          <Text style={s.section}>{t("systemHealth")}</Text>
          {health.data ? (
            <Card>
              <Health
                label={t("systemHealth")}
                value={health.data.system.status}
              />
              <Health
                label={t("databaseHealth")}
                value={health.data.database.status}
              />
              <Health
                label={t("visionHealth")}
                value={health.data.vision.status}
              />
            </Card>
          ) : null}
          <Text style={s.section}>{t("tenantUsage")}</Text>
          {usage.data?.map((x: any) => (
            <Card key={x.organisation_id}>
              <Text style={s.itemTitle}>{x.organisation}</Text>
              <Text style={s.meta}>
                {x.branches} filial · {x.users} user · {x.incidents} incident
              </Text>
            </Card>
          ))}
        </>
      ) : null}
      <Text style={s.section}>{t("incidents")}</Text>
      {incidents.data?.length ? (
        incidents.data.slice(0, 12).map((x: any) => (
          <Card key={x.id}>
            <View style={s.row}>
              <View style={{ flex: 1 }}>
                <Text style={s.itemTitle}>{x.title}</Text>
                <Text style={s.meta}>
                  {x.source?.replaceAll("_", " ")} · {x.priority}
                </Text>
              </View>
              <Status value={x.status} />
            </View>
          </Card>
        ))
      ) : !loading ? (
        <Text style={s.empty}>{t("noData")}</Text>
      ) : null}
      {isTenant ? (
        <Card>
          <View style={s.inline}>
            <Small
              label={t("customerReports")}
              value={reports.data?.length ?? 0}
            />
            <Small label={t("staffAudits")} value={audits.data?.length ?? 0} />
          </View>
        </Card>
      ) : null}
      {isPlatform ? (
        <Card>
          <View style={s.inline}>
            <Small
              label={t("organisations")}
              value={organisations.data?.length ?? 0}
            />
            <Small label={t("tenantUsage")} value={usage.data?.length ?? 0} />
          </View>
        </Card>
      ) : null}
    </Screen>
  );
}
function Metric({
  icon,
  label,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: number;
}) {
  return (
    <View style={s.metric}>
      <Ionicons name={icon} size={22} color={colors.blue} />
      <Text style={s.metricValue}>{value ?? 0}</Text>
      <Text style={s.metricLabel}>{label}</Text>
    </View>
  );
}
function Small({ label, value }: { label: string; value: number }) {
  return (
    <View style={s.small}>
      <Text style={s.smallValue}>{value}</Text>
      <Text style={s.metricLabel}>{label}</Text>
    </View>
  );
}
function Health({ label, value }: { label: string; value: string }) {
  const ok = value === "ok";
  return (
    <View style={s.health}>
      <Ionicons
        name={ok ? "checkmark-circle" : "warning"}
        size={20}
        color={ok ? colors.green : colors.amber}
      />
      <Text style={s.healthLabel}>{label}</Text>
      <Text style={s.healthValue}>{value.toUpperCase()}</Text>
    </View>
  );
}
const s = StyleSheet.create({
  top: { minHeight: 62, flexDirection: "row", alignItems: "center", gap: 12 },
  logo: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: colors.navy,
    alignItems: "center",
    justifyContent: "center",
  },
  brand: {
    fontWeight: "900",
    fontSize: 17,
    color: colors.navy,
    letterSpacing: 1.2,
  },
  role: { fontSize: 12, color: colors.muted, fontWeight: "700" },
  logout: {
    width: 46,
    height: 46,
    borderRadius: 15,
    backgroundColor: "#FFE9ED",
    alignItems: "center",
    justifyContent: "center",
  },
  metrics: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  metric: {
    width: "48%",
    minHeight: 125,
    padding: 15,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 5,
  },
  metricValue: { fontSize: 26, fontWeight: "900", color: colors.navy },
  metricLabel: { fontSize: 12, color: colors.muted, fontWeight: "700" },
  section: { fontSize: 18, fontWeight: "900", color: colors.navy },
  inline: { flexDirection: "row", gap: 8 },
  small: {
    flex: 1,
    padding: 10,
    borderRadius: radius.md,
    backgroundColor: colors.softBlue,
    alignItems: "center",
  },
  smallValue: { fontSize: 20, fontWeight: "900", color: colors.blue },
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  itemTitle: { fontSize: 15, fontWeight: "900", color: colors.navy },
  meta: { fontSize: 12, color: colors.muted, marginTop: 4 },
  score: { fontSize: 24, fontWeight: "900", color: colors.teal },
  health: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 8 },
  healthLabel: { flex: 1, fontWeight: "700", color: colors.text },
  healthValue: { fontSize: 11, fontWeight: "900", color: colors.green },
  empty: { textAlign: "center", color: colors.muted, padding: 20 },
});
