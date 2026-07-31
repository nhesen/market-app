import { useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import {
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
export default function SuggestionDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { t, language } = useI18n();
  const q = useQuery({
    queryKey: ["suggestion", id],
    queryFn: () => customerApi.suggestion(id!),
    enabled: Boolean(id),
    refetchInterval: 10000,
  });
  const x = q.data;
  return (
    <Screen>
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
      />
      {x ? (
        <>
          <Status value={x.status} />
          <PageTitle
            title={x.title}
            subtitle={`${t("trackingNumber")}: ${x.tracking_number}`}
          />
          <Card>
            <Text style={s.category}>
              {t(`suggestion_${x.category}` as any)}
            </Text>
            <Text style={s.body}>{x.description}</Text>
          </Card>
          {x.media?.map((item: any) => (
            <RemoteImage key={item.id} url={item.url} height={220} />
          ))}
          {x.admin_note ? (
            <Card>
              <Text style={s.noteTitle}>{t("managementNote")}</Text>
              <Text>{x.admin_note}</Text>
            </Card>
          ) : null}
          <Text style={s.section}>{t("timeline")}</Text>
          {x.history?.map((item: any, index: number) => (
            <View style={s.event} key={`${item.created_at}-${index}`}>
              <View style={s.rail}>
                <View style={s.dot} />
                {index < x.history.length - 1 ? <View style={s.line} /> : null}
              </View>
              <View style={s.eventBody}>
                <Status value={item.status} />
                <Text style={s.note}>{item.note}</Text>
                <Text style={s.date}>
                  {new Date(item.created_at).toLocaleString(
                    language === "az" ? "az-AZ" : "en-GB",
                  )}
                </Text>
              </View>
            </View>
          ))}
        </>
      ) : null}
    </Screen>
  );
}
const s = StyleSheet.create({
  body: { fontSize: 15, lineHeight: 23 },
  category: { color: colors.green, fontWeight: "900" },
  noteTitle: { fontWeight: "900", color: colors.blue },
  section: { fontSize: 19, fontWeight: "900", color: colors.navy },
  event: { flexDirection: "row", gap: 12, minHeight: 86 },
  rail: { width: 18, alignItems: "center" },
  dot: {
    width: 13,
    height: 13,
    borderRadius: 7,
    backgroundColor: colors.blue,
    marginTop: 6,
  },
  line: { width: 2, flex: 1, backgroundColor: colors.border },
  eventBody: { flex: 1, gap: 6, paddingBottom: 16 },
  note: { color: colors.navy },
  date: { fontSize: 12, color: colors.muted },
});
