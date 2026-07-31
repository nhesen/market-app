import { router, useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text } from "react-native";
import {
  Button,
  Card,
  PageTitle,
  RemoteImage,
  Screen,
  State,
  Status,
} from "../components/ui";
import { customerApi } from "../services/api";
import { useI18n } from "../services/i18n";
import { colors } from "../constants/theme";
export default function NewsDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { t, language } = useI18n();
  const q = useQuery({
    queryKey: ["news", id],
    queryFn: () => customerApi.newsDetail(id!),
    enabled: Boolean(id),
  });
  const n = q.data,
    body = language === "en" ? n?.body_en : n?.body_az,
    cta =
      n?.content_type === "CAMPAIGN"
        ? { label: t("viewDiscounts"), path: "/discounts" }
        : n?.branch_id
          ? { label: t("viewBranch"), path: `/branch-detail?id=${n.branch_id}` }
          : null;
  return (
    <Screen>
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
      />
      {n ? (
        <>
          <RemoteImage url={n.image_url} height={240} />
          <Status value={t(`newsType_${n.content_type}` as any)} />
          <PageTitle
            title={language === "en" ? n.title_en : n.title_az}
            subtitle={`${t("published")}: ${new Date(n.published_at).toLocaleDateString(language === "az" ? "az-AZ" : "en-GB")}`}
          />
          <Card>
            <Text style={s.summary}>
              {language === "en" ? n.summary_en : n.summary_az}
            </Text>
            <Text style={s.body}>
              {body || (language === "en" ? n.summary_en : n.summary_az)}
            </Text>
            <Text style={s.scope}>
              {n.branch_id ? t("branchScope") : t("allBranches")}
            </Text>
          </Card>
          {cta ? (
            <Button
              title={cta.label}
              onPress={() => router.push(cta.path as never)}
            />
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}
const s = StyleSheet.create({
  summary: {
    fontSize: 17,
    fontWeight: "800",
    lineHeight: 25,
    color: colors.navy,
  },
  body: { fontSize: 15, lineHeight: 25, color: colors.navy },
  scope: { color: colors.blue, fontWeight: "800" },
});
