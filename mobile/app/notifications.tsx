import { Pressable, StyleSheet, Text, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Button, Card, PageTitle, Screen, State } from "../components/ui";
import { colors } from "../constants/theme";
import { customerApi } from "../services/api";
import { useI18n } from "../services/i18n";
export default function Notifications() {
  const { t, language } = useI18n(),
    client = useQueryClient();
  const q = useQuery({
    queryKey: ["notifications"],
    queryFn: customerApi.notifications,
  });
  const refresh = () =>
    client.invalidateQueries({ queryKey: ["notifications"] });
  const read = useMutation({
      mutationFn: customerApi.readNotification,
      onSuccess: refresh,
    }),
    all = useMutation({
      mutationFn: customerApi.readAllNotifications,
      onSuccess: refresh,
    });
  const unread = q.data?.filter((x) => !x.is_read).length ?? 0;
  function open(item: any) {
    if (!item.is_read) read.mutate(item.id);
    const id = item.related_entity_id;
    if (item.kind === "REPORT_STATUS" && id)
      router.push({ pathname: "/report-detail", params: { id } });
    else if (item.kind === "SUGGESTION_STATUS" && id)
      router.push({ pathname: "/suggestion-detail", params: { id } });
    else if (
      (item.kind === "NEWS" || item.kind === "BRANCH_ANNOUNCEMENT") &&
      id
    )
      router.push({ pathname: "/news-detail", params: { id } });
    else if (item.kind === "DISCOUNT" && id)
      router.push({ pathname: "/discount-detail", params: { id } });
    else if (item.kind === "EXPIRING_POINTS") router.push("/cards");
  }
  return (
    <Screen refreshing={q.isRefetching} onRefresh={() => q.refetch()}>
      <PageTitle
        title={t("notifications")}
        subtitle={`${unread} ${t("unread")}`}
      />
      {unread ? (
        <Button
          secondary
          title={t("markAllRead")}
          onPress={() => all.mutate()}
        />
      ) : null}
      <State
        loading={q.isLoading}
        error={q.isError}
        retry={() => q.refetch()}
        empty={!q.data?.length ? t("noNotifications") : undefined}
      />
      {q.data?.map((x) => (
        <Pressable key={x.id} onPress={() => open(x)}>
          <Card>
            <View style={s.row}>
              <View style={[s.icon, x.is_read && s.read]}>
                <Ionicons
                  name="notifications-outline"
                  size={21}
                  color={x.is_read ? colors.muted : colors.blue}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.title}>{x.title}</Text>
                <Text style={s.body}>{x.body}</Text>
                <Text style={s.date}>
                  {new Date(x.created_at).toLocaleString(
                    language === "az" ? "az-AZ" : "en-GB",
                  )}
                </Text>
              </View>
              {!x.is_read ? <View style={s.dot} /> : null}
            </View>
          </Card>
        </Pressable>
      ))}
    </Screen>
  );
}
const s = StyleSheet.create({
  row: { flexDirection: "row", gap: 11, alignItems: "flex-start" },
  icon: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  read: { backgroundColor: "#F2F4F7" },
  title: { fontWeight: "900", color: colors.navy },
  body: { color: colors.muted, lineHeight: 19, marginTop: 3 },
  date: { fontSize: 11, color: colors.muted, marginTop: 6 },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: colors.blue },
});
