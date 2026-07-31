import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import {
  Button,
  Card,
  PageTitle,
  Screen,
  State,
  Status,
} from "../components/ui";
import { api } from "../services/api";
import { useI18n } from "../services/i18n";
import { colors } from "../constants/theme";

export default function Reports() {
  const { t, language } = useI18n(),
    q = useQuery({ queryKey: ["reports"], queryFn: api.reports });
  return (
    <Screen refreshing={q.isRefetching} onRefresh={() => q.refetch()}>
      <PageTitle
        title={t("reportsTitle")}
        subtitle={t("reportsSubtitle")}
        action={
          <Button
            title={t("newReport")}
            onPress={() => router.push("/report")}
          />
        }
      />
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
        empty={!q.data?.length ? t("noReports") : undefined}
      />
      {q.data?.map((r) => (
        <Card
          key={r.id}
          onPress={() =>
            router.push({ pathname: "/report-detail", params: { id: r.id } })
          }
        >
          <View style={s.row}>
            <Status value={r.customer_status ?? r.status} />
            <Text style={s.date}>
              {new Date(r.created_at).toLocaleDateString(
                language === "az" ? "az-AZ" : "en-GB",
              )}
            </Text>
          </View>
          <Text style={s.title}>{r.title}</Text>
          <Text style={s.track}>{r.tracking_number}</Text>
          <Text numberOfLines={2} style={s.description}>
            {r.description}
          </Text>
        </Card>
      ))}
    </Screen>
  );
}
const s = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  date: { fontSize: 12, color: colors.muted },
  title: { fontSize: 17, fontWeight: "900", color: colors.navy },
  track: { color: colors.blue, fontWeight: "800" },
  description: { color: colors.muted, lineHeight: 20 },
});
