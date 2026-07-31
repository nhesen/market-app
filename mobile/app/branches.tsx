import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Button, Card, Chip, PageTitle, Screen, State } from "../components/ui";
import { colors } from "../constants/theme";
import {
  api,
  customerApi,
  selectBranch,
  selectedBranchId,
  selectMarket,
} from "../services/api";
import { useI18n } from "../services/i18n";
const marketQueries = [
  "home",
  "branches",
  "products",
  "categories",
  "discounts",
  "favourites",
  "branch-favourites",
  "campaign-favourites",
  "cards",
  "offers",
  "news",
  "notifications",
];
export default function Branches() {
  const { t } = useI18n(),
    client = useQueryClient();
  const q = useQuery({ queryKey: ["branches"], queryFn: api.branches });
  const orgs = useQuery({
    queryKey: ["organisations"],
    queryFn: api.organisations,
  });
  const market = useQuery({
    queryKey: ["market"],
    queryFn: customerApi.market,
  });
  const selected = useQuery({
    queryKey: ["selected-branch"],
    queryFn: selectedBranchId,
  });
  const fav = useQuery({
    queryKey: ["branch-favourites"],
    queryFn: customerApi.favouriteBranches,
  });
  const ids = new Set(fav.data?.map((x) => x.id));
  const switchMarket = useMutation({
    mutationFn: selectMarket,
    onSuccess: async () => {
      marketQueries.forEach((key) => client.removeQueries({ queryKey: [key] }));
      await Promise.all([
        market.refetch(),
        q.refetch(),
        selected.refetch(),
        fav.refetch(),
      ]);
    },
  });
  const toggle = useMutation({
    mutationFn: (id: string) =>
      ids.has(id)
        ? customerApi.unfavouriteBranch(id)
        : customerApi.favouriteBranch(id),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ["branch-favourites"] }),
  });
  async function choose(id: string) {
    await selectBranch(id);
    await Promise.all([
      selected.refetch(),
      client.invalidateQueries({ queryKey: ["home"] }),
      client.invalidateQueries({ queryKey: ["products"] }),
    ]);
  }
  return (
    <Screen
      refreshing={q.isRefetching || switchMarket.isPending}
      onRefresh={() => q.refetch()}
    >
      <PageTitle title={t("branchesTitle")} subtitle={t("branchesSubtitle")} />
      <Text style={s.label}>{t("market")}</Text>
      <View style={s.chips}>
        {orgs.data?.map((x: any) => (
          <Chip
            key={x.id}
            label={x.name}
            active={market.data?.id === x.id}
            onPress={() =>
              market.data?.id !== x.id && switchMarket.mutate(x.id)
            }
          />
        ))}
      </View>
      {switchMarket.isPending ? (
        <Text style={s.switching}>{t("switchingMarket")}</Text>
      ) : null}
      <State
        loading={
          q.isLoading || market.isLoading || selected.isLoading || fav.isLoading
        }
        error={q.isError || market.isError || fav.isError}
        retry={() => q.refetch()}
        empty={!q.data?.length ? t("noBranches") : undefined}
      />
      {q.data?.map((b) => (
        <Card key={b.id}>
          <View style={s.row}>
            <View style={s.icon}>
              <Ionicons
                name="storefront-outline"
                size={25}
                color={colors.blue}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.title}>{b.name}</Text>
              <Text style={s.meta}>{b.address}</Text>
              <Text style={b.is_open ? s.open : s.closed}>
                {b.is_open ? t("open") : t("closed")} · {b.hours} ·{" "}
                {b.distance_km} km
              </Text>
            </View>
            <Pressable onPress={() => toggle.mutate(b.id)}>
              <Ionicons
                name={ids.has(b.id) ? "heart" : "heart-outline"}
                size={27}
                color={colors.red}
              />
            </Pressable>
          </View>
          {selected.data === b.id ? (
            <View style={s.preferred}>
              <Ionicons
                name="checkmark-circle"
                size={18}
                color={colors.green}
              />
              <Text style={s.preferredText}>{t("preferredBranch")}</Text>
            </View>
          ) : (
            <Button title={t("selectBranch")} onPress={() => choose(b.id)} />
          )}
          <Button
            secondary
            title={t("details")}
            onPress={() =>
              router.push({
                pathname: "/branch-detail" as never,
                params: { id: b.id },
              })
            }
          />
        </Card>
      ))}
    </Screen>
  );
}
const s = StyleSheet.create({
  label: { fontWeight: "900", color: colors.navy },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  switching: { color: colors.blue, fontWeight: "800" },
  row: { flexDirection: "row", gap: 11, alignItems: "flex-start" },
  icon: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  title: { fontSize: 17, fontWeight: "900", color: colors.navy },
  meta: { color: colors.muted, marginTop: 3 },
  open: { color: colors.green, fontWeight: "800", marginTop: 5 },
  closed: { color: colors.red, fontWeight: "800", marginTop: 5 },
  preferred: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    backgroundColor: colors.softGreen,
    padding: 11,
    borderRadius: 12,
  },
  preferredText: { color: colors.green, fontWeight: "800" },
});
