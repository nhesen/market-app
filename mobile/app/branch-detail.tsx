import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import {
  Button,
  Card,
  PageTitle,
  RemoteImage,
  Screen,
  State,
} from "../components/ui";
import { colors } from "../constants/theme";
import { customerApi, selectBranch, selectedBranchId } from "../services/api";
import { useI18n } from "../services/i18n";
export default function BranchDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { t } = useI18n(),
    client = useQueryClient();
  const q = useQuery({
    queryKey: ["branch", id],
    queryFn: () => customerApi.branch(id!),
    enabled: Boolean(id),
  });
  const selected = useQuery({
    queryKey: ["selected-branch"],
    queryFn: selectedBranchId,
  });
  const fav = useQuery({
    queryKey: ["branch-favourites"],
    queryFn: customerApi.favouriteBranches,
  });
  const saved = Boolean(fav.data?.some((x) => x.id === id));
  const toggle = useMutation({
    mutationFn: () =>
      saved
        ? customerApi.unfavouriteBranch(id!)
        : customerApi.favouriteBranch(id!),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ["branch-favourites"] }),
  });
  const b = q.data;
  async function choose() {
    await selectBranch(id!);
    await selected.refetch();
    await client.invalidateQueries({ queryKey: ["home"] });
  }
  return (
    <Screen>
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
      />
      {b ? (
        <>
          <View style={s.hero}>
            <RemoteImage
              url={b.image_url ?? "/assets/retail-branch-v2.png"}
              height={210}
            />
            <View style={[s.state, b.is_open ? s.open : s.closed]}>
              <View style={s.dot} />
              <Text style={s.stateText}>
                {b.is_open ? t("open") : t("closed")}
              </Text>
            </View>
          </View>
          <PageTitle title={b.name} subtitle={`${b.distance_km} km`} />
          <Card>
            <Info
              icon="location-outline"
              label={t("address")}
              value={b.address}
            />
            <Info
              icon="time-outline"
              label={t("workingHours")}
              value={b.hours}
            />
          </Card>
          <Card>
            <Text style={s.section}>{t("services")}</Text>
            <View style={s.services}>
              {b.services?.map((x) => (
                <View key={x} style={s.service}>
                  <Ionicons
                    name="checkmark-circle"
                    size={20}
                    color={colors.green}
                  />
                  <Text style={s.serviceText}>{x}</Text>
                </View>
              ))}
            </View>
          </Card>
          <Button
            title={selected.data === id ? t("selected") : t("selectBranch")}
            disabled={selected.data === id}
            onPress={choose}
          />
          <Button
            secondary
            title={saved ? t("unfavourite") : t("favourite")}
            icon={saved ? "heart" : "heart-outline"}
            onPress={() => toggle.mutate()}
          />
        </>
      ) : null}
    </Screen>
  );
}
function Info({
  icon,
  label,
  value,
}: {
  icon: any;
  label: string;
  value: string;
}) {
  return (
    <View style={s.info}>
      <View style={s.infoIcon}>
        <Ionicons name={icon} size={21} color={colors.blue} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={s.label}>{label}</Text>
        <Text style={s.value}>{value}</Text>
      </View>
    </View>
  );
}
const s = StyleSheet.create({
  hero: {
    height: 210,
    borderRadius: 22,
    overflow: "hidden",
    position: "relative",
  },
  state: {
    position: "absolute",
    left: 14,
    bottom: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 99,
  },
  open: { backgroundColor: "rgba(10,89,60,.9)" },
  closed: { backgroundColor: "rgba(150,25,45,.9)" },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: "white" },
  stateText: { color: "white", fontWeight: "900" },
  info: {
    flexDirection: "row",
    gap: 12,
    alignItems: "center",
    paddingVertical: 8,
  },
  infoIcon: {
    width: 44,
    height: 44,
    borderRadius: 15,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  label: { fontSize: 12, color: colors.muted },
  value: { fontWeight: "800", color: colors.navy, marginTop: 3 },
  section: { fontWeight: "900", fontSize: 18, color: colors.navy },
  services: { gap: 9 },
  service: {
    minHeight: 44,
    flexDirection: "row",
    gap: 9,
    alignItems: "center",
    backgroundColor: colors.softGreen,
    borderRadius: 13,
    paddingHorizontal: 12,
  },
  serviceText: { fontWeight: "700", color: colors.navy },
});
