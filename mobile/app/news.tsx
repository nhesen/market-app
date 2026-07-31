import { useState } from "react";
import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import {
  Card,
  Chip,
  PageTitle,
  RemoteImage,
  Screen,
  State,
  Status,
} from "../components/ui";
import { customerApi } from "../services/api";
import { useI18n } from "../services/i18n";
import { colors } from "../constants/theme";
export default function News() {
  const { t, language } = useI18n(),
    [filter, setFilter] = useState("ALL");
  const q = useQuery({ queryKey: ["news"], queryFn: () => customerApi.news() });
  const groups = [
    "ALL",
    "NEWS",
    "ANNOUNCEMENT",
    "BRANCH_UPDATE",
    "NEW_SERVICE",
    "CAMPAIGN",
  ];
  const rows =
    filter === "ALL"
      ? q.data
      : q.data?.filter((n) => n.content_type === filter);
  return (
    <Screen refreshing={q.isRefetching} onRefresh={() => q.refetch()}>
      <PageTitle title={t("newsTitle")} />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={s.chips}
      >
        {groups.map((value) => (
          <Chip
            key={value}
            active={filter === value}
            label={t(`newsType_${value}` as any)}
            onPress={() => setFilter(value)}
          />
        ))}
      </ScrollView>
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
        empty={!rows?.length ? t("newsEmpty") : undefined}
      />
      {rows?.map((n) => (
        <Card
          key={n.id}
          onPress={() =>
            router.push({
              pathname: "/news-detail" as never,
              params: { id: n.id },
            })
          }
        >
          <RemoteImage url={n.image_url} height={170} />
          <View style={s.meta}>
            <Status value={t(`newsType_${n.content_type}` as any)} />
            <Text style={s.date}>
              {new Date(n.published_at).toLocaleDateString(
                language === "az" ? "az-AZ" : "en-GB",
              )}
            </Text>
          </View>
          <Text style={s.title}>
            {language === "en" ? n.title_en : n.title_az}
          </Text>
          <Text numberOfLines={3} style={s.body}>
            {language === "en" ? n.summary_en : n.summary_az}
          </Text>
          <Text style={s.scope}>
            {n.branch_id ? t("branchScope") : t("marketScope")}
          </Text>
        </Card>
      ))}
    </Screen>
  );
}
const s = StyleSheet.create({
  chips: { gap: 8, paddingRight: 12 },
  meta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontSize: 19, fontWeight: "900", color: colors.navy },
  body: { color: colors.muted, lineHeight: 20 },
  date: { fontSize: 12, color: colors.muted },
  scope: { fontSize: 12, color: colors.blue, fontWeight: "800" },
});
