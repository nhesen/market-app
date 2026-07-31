import { useEffect, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import {
  Pressable,
  RefreshControl,
  ScrollView as NativeScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import * as SecureStore from "expo-secure-store";
import { SafeAreaView } from "react-native-safe-area-context";
import { api, hasSession } from "../services/api";
import { colors } from "../constants/theme";
import { BottomNav } from "../components/BottomNav";
import { Card, RemoteImage, State, Status } from "../components/ui";
import { useI18n } from "../services/i18n";
function ScrollView({
  refreshing,
  onRefresh,
  ...props
}: React.ComponentProps<typeof NativeScrollView> & {
  refreshing?: boolean;
  onRefresh?: () => void;
}) {
  return (
    <NativeScrollView
      {...props}
      refreshControl={
        onRefresh ? (
          <RefreshControl
            refreshing={Boolean(refreshing)}
            onRefresh={onRefresh}
            tintColor={colors.blue}
          />
        ) : undefined
      }
    />
  );
}
export default function Home() {
  const { t, language } = useI18n();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    Promise.all([
      SecureStore.getItemAsync("onboarding_seen"),
      hasSession(),
    ]).then(([seen, session]) => {
      if (!seen) router.replace("/onboarding" as never);
      else if (!session) router.replace("/login");
      else setReady(true);
    });
  }, []);
  const q = useQuery({ queryKey: ["home"], queryFn: api.home, enabled: ready });
  if (!ready)
    return (
      <View style={s.center}>
        <Ionicons name="storefront" size={42} color={colors.blue} />
      </View>
    );
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={s.safe}>
      <ScrollView
        contentContainerStyle={s.page}
        showsVerticalScrollIndicator={false}
        refreshing={q.isRefetching}
        onRefresh={() => q.refetch()}
      >
        <State
          loading={q.isLoading}
          error={q.isError}
          retry={() => q.refetch()}
        />
        {q.data ? (
          <>
            <View style={s.header}>
              <View style={{ flex: 1 }}>
                <Text style={s.hello}>
                  {t("hello")}, {q.data.user.full_name.split(" ")[0]}
                </Text>
                <Text style={s.marketName}>{q.data.organisation?.name}</Text>
                <Pressable
                  style={s.branch}
                  onPress={() => router.push("/branches")}
                >
                  <Ionicons name="location" size={16} color={colors.blue} />
                  <View style={{ flex: 1 }}>
                    <Text style={s.branchName}>
                      {q.data.selected_branch?.name}
                    </Text>
                    <Text
                      style={
                        q.data.selected_branch?.is_open ? s.open : s.closed
                      }
                    >
                      {q.data.selected_branch?.is_open
                        ? t("open")
                        : t("closed")}{" "}
                      · {q.data.selected_branch?.hours}
                    </Text>
                  </View>
                  <Text style={s.change}>{t("change")}</Text>
                </Pressable>
              </View>
              <Pressable
                style={s.bell}
                onPress={() => router.push("/notifications")}
              >
                <Ionicons
                  name="notifications-outline"
                  size={24}
                  color={colors.navy}
                />
                {q.data.unread_notifications ? (
                  <View style={s.badge}>
                    <Text style={s.badgeText}>
                      {Math.min(q.data.unread_notifications, 99)}
                    </Text>
                  </View>
                ) : null}
              </Pressable>
              <Pressable
                accessibilityLabel={t("profile")}
                style={s.avatar}
                onPress={() => router.push("/profile")}
              >
                <Text style={s.avatarText}>
                  {q.data.user.full_name.slice(0, 1).toUpperCase()}
                </Text>
              </Pressable>
            </View>
            <View style={s.search}>
              <Ionicons name="search" size={20} color={colors.muted} />
              <TextInput
                style={{ flex: 1 }}
                placeholder={t("productSearch")}
                placeholderTextColor={colors.muted}
                onSubmitEditing={(e) =>
                  router.push({
                    pathname: "/products",
                    params: { q: e.nativeEvent.text },
                  })
                }
              />
              <Pressable onPress={() => router.push("/scanner")}>
                <Ionicons
                  name="barcode-outline"
                  size={26}
                  color={colors.blue}
                />
              </Pressable>
            </View>
            <Section
              title={t("news")}
              action={t("seeAll")}
              onPress={() => router.push("/news" as never)}
            />
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {q.data.news.slice(0, 5).map((n) => (
                <Pressable
                  key={n.id}
                  style={s.news}
                  onPress={() =>
                    router.push({
                      pathname: "/news-detail" as never,
                      params: { id: n.id },
                    })
                  }
                >
                  <RemoteImage url={n.image_url} height={105} />
                  <Text numberOfLines={2} style={s.cardTitle}>
                    {language === "en" ? n.title_en : n.title_az}
                  </Text>
                  <Text numberOfLines={2} style={s.muted}>
                    {language === "en" ? n.summary_en : n.summary_az}
                  </Text>
                </Pressable>
              ))}
            </ScrollView>
            <Section title={t("quickActions")} />
            <View style={s.quick}>
              {[
                ["pricetag-outline", t("checkPrice"), "/products"],
                ["gift-outline", t("discounts"), "/discounts"],
                ["alert-circle-outline", t("reportProblem"), "/report"],
                ["bulb-outline", t("sendSuggestion"), "/suggestions"],
                ["navigate-outline", t("findBranch"), "/branches"],
                ["barcode-outline", t("scanProduct"), "/scanner"],
              ].map(([icon, label, path]) => (
                <Pressable
                  key={path}
                  style={s.quickItem}
                  onPress={() => router.push(path as never)}
                >
                  <View style={s.iconBox}>
                    <Ionicons
                      name={icon as any}
                      size={23}
                      color={colors.blue}
                    />
                  </View>
                  <Text style={s.quickText}>{label}</Text>
                </Pressable>
              ))}
            </View>
            <Pressable style={s.loyalty} onPress={() => router.push("/cards")}>
              <View>
                <Text style={s.loyaltyLabel}>{t("loyalty").toUpperCase()}</Text>
                <Text style={s.balance}>
                  {q.data.loyalty?.balance ?? 0} {t("bonus")}
                </Text>
                <Text style={s.loyaltyMeta}>
                  +{q.data.loyalty?.monthly_earned ?? 0} {t("monthlyEarned")} ·{" "}
                  {q.data.loyalty?.expiring ?? 0} {t("expiring")}
                </Text>
              </View>
              <Ionicons name="qr-code" size={52} color="white" />
            </Pressable>
            <Section
              title={t("featuredDiscounts")}
              action={t("seeAll")}
              onPress={() => router.push("/discounts")}
            />
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {q.data.discounts.slice(0, 8).map((p) => (
                <Pressable
                  key={p.id}
                  style={s.product}
                  onPress={() =>
                    router.push({
                      pathname: "/product-detail" as never,
                      params: { id: p.id },
                    })
                  }
                >
                  <RemoteImage url={p.image_url} height={90} />
                  <Text numberOfLines={2} style={s.cardTitle}>
                    {p.name}
                  </Text>
                  <Text style={s.old}>
                    {p.price.toFixed(2)} {t("currency")}
                  </Text>
                  <Text style={s.price}>
                    {p.discount_price?.toFixed(2)} {t("currency")}
                  </Text>
                </Pressable>
              ))}
            </ScrollView>
            <Section
              title={t("activeReports")}
              action={t("seeAll")}
              onPress={() => router.push("/reports")}
            />
            {q.data.reports.length ? (
              q.data.reports.map((r) => (
                <Card
                  key={r.id}
                  onPress={() =>
                    router.push({
                      pathname: "/report-detail",
                      params: { id: r.id },
                    })
                  }
                >
                  <View style={s.row}>
                    <View style={{ flex: 1 }}>
                      <Text style={s.cardTitle}>{r.title}</Text>
                      <Text style={s.muted}>{r.tracking_number}</Text>
                    </View>
                    <Status value={r.status} />
                  </View>
                </Card>
              ))
            ) : (
              <Text style={s.muted}>{t("noActiveReports")}</Text>
            )}
            <Section
              title={t("nearbyBranches")}
              action={t("seeAll")}
              onPress={() => router.push("/branches")}
            />
            {q.data.branches.slice(0, 3).map((b) => (
              <Card
                key={b.id}
                onPress={() =>
                  router.push({
                    pathname: "/branch-detail" as never,
                    params: { id: b.id },
                  })
                }
              >
                <View style={s.row}>
                  <View style={s.storeIcon}>
                    <Ionicons
                      name="storefront-outline"
                      size={22}
                      color={colors.blue}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.cardTitle}>{b.name}</Text>
                    <Text style={s.muted}>
                      {b.address} · {b.distance_km} km
                    </Text>
                  </View>
                  <Text style={b.is_open ? s.open : s.closed}>
                    {b.is_open ? t("open") : t("closed")}
                  </Text>
                </View>
              </Card>
            ))}
          </>
        ) : null}
      </ScrollView>
      <BottomNav />
    </SafeAreaView>
  );
}
function Section({
  title,
  action,
  onPress,
}: {
  title: string;
  action?: string;
  onPress?: () => void;
}) {
  return (
    <View style={s.section}>
      <Text style={s.sectionTitle}>{title}</Text>
      {action ? (
        <Pressable onPress={onPress}>
          <Text style={s.change}>{action}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  page: { padding: 18, paddingBottom: 110, gap: 13 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: { flexDirection: "row", gap: 12 },
  hello: { fontSize: 25, fontWeight: "900", color: colors.navy },
  branch: { flexDirection: "row", gap: 7, alignItems: "center", marginTop: 7 },
  branchName: { fontWeight: "800", color: colors.navy },
  open: { color: colors.green, fontWeight: "800", fontSize: 12 },
  closed: { color: colors.red, fontWeight: "800", fontSize: 12 },
  change: { color: colors.blue, fontWeight: "800", fontSize: 12 },
  bell: {
    width: 46,
    height: 46,
    borderRadius: 16,
    backgroundColor: "white",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  marketName: { color: colors.blue, fontWeight: "900", marginTop: 3 },
  badge: {
    position: "absolute",
    right: -3,
    top: -4,
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.red,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  badgeText: { color: "white", fontSize: 10, fontWeight: "900" },
  avatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: colors.navy,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: { color: "white", fontSize: 18, fontWeight: "900" },
  search: {
    height: 56,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    paddingHorizontal: 15,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  section: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 8,
  },
  sectionTitle: { fontSize: 19, fontWeight: "900", color: colors.navy },
  news: {
    width: 260,
    backgroundColor: "white",
    borderRadius: 17,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 11,
    marginRight: 11,
    gap: 7,
  },
  cardTitle: { fontWeight: "900", color: colors.navy },
  muted: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  quick: { flexDirection: "row", flexWrap: "wrap", gap: 9 },
  quickItem: {
    width: "31.5%",
    minHeight: 100,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 10,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 13,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  quickText: {
    fontSize: 12,
    fontWeight: "800",
    marginTop: 8,
    color: colors.navy,
  },
  loyalty: {
    backgroundColor: colors.deepNavy,
    borderRadius: 21,
    padding: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  loyaltyLabel: { color: "#9FC1FF", fontSize: 11, fontWeight: "900" },
  balance: {
    fontSize: 28,
    color: "white",
    fontWeight: "900",
    marginVertical: 5,
  },
  loyaltyMeta: { color: "#D8E6FF", fontSize: 12 },
  product: {
    width: 155,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 10,
    marginRight: 10,
    gap: 4,
  },
  old: {
    textDecorationLine: "line-through",
    color: colors.muted,
    fontSize: 12,
  },
  price: { fontSize: 19, fontWeight: "900", color: colors.blue },
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  storeIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
});
