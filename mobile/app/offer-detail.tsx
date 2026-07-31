import { useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text } from "react-native";
import { Card, PageTitle, RemoteImage, Screen, State } from "../components/ui";
import { customerApi } from "../services/api";
import { useI18n } from "../services/i18n";
import { colors } from "../constants/theme";
export default function OfferDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { t, language } = useI18n();
  const q = useQuery({
      queryKey: ["offer", id],
      queryFn: () => customerApi.offer(id!),
      enabled: Boolean(id),
    }),
    x = q.data;
  return (
    <Screen>
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
      />
      {x ? (
        <>
          <RemoteImage url={x.image_url} height={230} />
          <PageTitle
            title={language === "en" ? x.title_en : x.title_az}
            subtitle={`${x.points_cost} ${t("bonus")}`}
          />
          <Card>
            <Text style={s.body}>
              {language === "en" ? x.description_en : x.description_az}
            </Text>
            <Text style={s.valid}>
              {t("validUntil")}:{" "}
              {new Date(x.valid_until).toLocaleDateString(
                language === "az" ? "az-AZ" : "en-GB",
              )}
            </Text>
            <Text style={s.demo}>{t("simulated")}</Text>
          </Card>
        </>
      ) : null}
    </Screen>
  );
}
const s = StyleSheet.create({
  body: { fontSize: 16, lineHeight: 24, color: colors.navy },
  valid: { color: colors.green, fontWeight: "800" },
  demo: { color: colors.muted, fontSize: 12 },
});
