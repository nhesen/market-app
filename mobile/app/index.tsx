import { useEffect } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { SafeAreaView } from "react-native-safe-area-context";
import { api } from "../services/api";
import { colors } from "../constants/theme";
import { BottomNav } from "../components/BottomNav";
const status: any = {
  VERIFICATION_REQUIRED: "Yoxlanılır",
  VERIFIED: "Təsdiqləndi",
  IN_PROGRESS: "İcradadır",
  RESOLVED: "Həll edildi",
  AUTO_RESOLVED: "Avtomatik həll",
};
export default function Home() {
  const q = useQuery({ queryKey: ["home"], queryFn: api.home, retry: false });
  useEffect(() => {
    if (q.isError) router.replace("/login");
  }, [q.isError]);
  if (q.isLoading)
    return (
      <View style={s.center}>
        <ActivityIndicator color={colors.blue} />
        <Text>MARTIQ hazırlanır…</Text>
      </View>
    );
  if (!q.data)
    return (
      <View style={s.center}>
        <Text>Serverə qoşulmaq mümkün olmadı.</Text>
        <Pressable style={s.button} onPress={() => q.refetch()}>
          <Text style={s.buttonText}>Yenidən yoxla</Text>
        </Pressable>
      </View>
    );
  const d = q.data,
    b = d.branches[0];
  return (
    <SafeAreaView edges={["top","left","right"]} style={{ flex: 1, backgroundColor: colors.background }}>
      <ScrollView contentContainerStyle={s.page}>
        <View style={s.header}>
          <View>
            <Text style={s.hello}>Salam, {d.user.full_name} 👋</Text>
            <Text style={s.muted}>Nova Market · {b?.name}</Text>
            <Text style={s.open}>● Açıq · {b?.hours}</Text>
          </View>
          <Pressable style={s.avatar} onPress={() => router.push("/notifications")}>
            <Text>🔔</Text>
          </Pressable>
        </View>
        <View style={s.search}>
          <TextInput placeholder="Məhsul və ya barkod axtarın" onSubmitEditing={(e)=>router.push({pathname:"/products",params:{q:e.nativeEvent.text}})} />
          <Text onPress={()=>router.push("/scanner")}>▣</Text>
        </View>
        <Title text="Xəbərlər" />
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {d.news.map((n) => (
            <View style={s.news} key={n.id}>
              <View style={s.newsImage}>
                <Text style={{ fontSize: 34 }}>🛒</Text>
              </View>
              <Text style={s.cardTitle}>{n.title_az}</Text>
              <Text style={s.muted}>{n.summary_az}</Text>
            </View>
          ))}
        </ScrollView>
        <Title text="Sürətli keçidlər" />
        <View style={s.quick}>
          {[
            ["⌕", "Qiyməti yoxla"],
            ["％", "Endirimlər"],
            ["!", "Problem bildir"],
            ["✦", "Təklif göndər"],
            ["⌖", "Filial tap"],
            ["▣", "Məhsul skan et"],
          ].map((x, i) => (
            <Pressable
              key={x[1]}
              style={s.quickItem}
              onPress={() => router.push(["/products","/products","/report","/suggestions","/branches","/scanner"][i] as any)}
            >
              <Text style={s.quickIcon}>{x[0]}</Text>
              <Text style={s.quickText}>{x[1]}</Text>
            </Pressable>
          ))}
        </View>
        <View style={s.loyalty}>
          <Text style={s.loyaltyLabel}>DEMO BONUS BALANSI</Text>
          <Text style={s.balance}>{d.loyalty?.balance ?? 0} bonus</Text>
          <Text style={{ color: "white" }}>
            Bu ay +{d.loyalty?.monthly_earned} · {d.loyalty?.expiring} bonusun
            müddəti bitir
          </Text>
        </View>
        <Title text="Seçilmiş endirimlər" />
        <ScrollView horizontal>
          {d.discounts.map((p) => (
            <View style={s.product} key={p.id}>
              <Text style={{ fontSize: 40 }}>🥛</Text>
              <Text style={s.cardTitle}>{p.name}</Text>
              <Text style={s.old}>{p.price.toFixed(2)} ₼</Text>
              <Text style={s.price}>{p.discount_price.toFixed(2)} ₼</Text>
            </View>
          ))}
        </ScrollView>
        <View style={s.sectionRow}><Title text="Problemlərim"/><Pressable onPress={()=>router.push('/reports' as any)}><Text style={s.seeAll}>Hamısına bax</Text></Pressable></View>
        {d.reports.map((r) => (
          <Pressable
            key={r.id}
            style={s.report}
            onPress={() =>
              router.push({ pathname: "/report-detail", params: { id: r.id } })
            }
          >
            <View>
              <Text style={s.cardTitle}>{r.title}</Text>
              <Text style={s.muted}>{r.tracking_number}</Text>
            </View>
            <Text style={s.badge}>{status[r.status] ?? r.status}</Text>
          </Pressable>
        ))}
        <Title text="Yaxın filiallar" />
        {d.branches.map((x) => (
          <View style={s.report} key={x.id}>
            <View>
              <Text style={s.cardTitle}>{x.name}</Text>
              <Text style={s.muted}>
                {x.address} · {x.distance_km} km
              </Text>
            </View>
            <Text style={s.open}>Açıq</Text>
          </View>
        ))}
      </ScrollView>
      <BottomNav />
    </SafeAreaView>
  );
}
function Title({ text }: { text: string }) {
  return <Text style={s.title}>{text}</Text>;
}
const s = StyleSheet.create({
  page: { padding: 20, paddingBottom: 110, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 15 },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  hello: { fontSize: 24, fontWeight: "800", color: colors.navy },
  muted: { color: colors.muted, fontSize: 13 },
  open: { color: colors.green, fontWeight: "700", marginTop: 4 },
  avatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  search: {
    height: 56,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 15,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontSize: 19, fontWeight: "800", marginTop: 14, color: colors.navy },
  news: {
    width: 280,
    backgroundColor: "white",
    borderRadius: 17,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 13,
    marginRight: 12,
    gap: 7,
  },
  newsImage: {
    height: 95,
    borderRadius: 12,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: { fontWeight: "800", color: colors.navy },
  quick: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  quickItem: {
    width: "31%",
    minHeight: 88,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    padding: 11,
  },
  quickIcon: { fontSize: 22, color: colors.blue, fontWeight: "800" },
  quickText: { fontSize: 12, fontWeight: "700", marginTop: 7 },
  loyalty: {
    backgroundColor: colors.deepNavy,
    borderRadius: 18,
    padding: 20,
    gap: 6,
  },
  loyaltyLabel: { color: "#a9c7ff", fontSize: 11, fontWeight: "800" },
  balance: { fontSize: 28, color: "white", fontWeight: "900" },
  product: {
    width: 150,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 15,
    padding: 14,
    marginRight: 10,
  },
  old: {
    textDecorationLine: "line-through",
    color: colors.muted,
    marginTop: 8,
  },
  price: { fontSize: 19, fontWeight: "900", color: colors.blue },
  report: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    padding: 15,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  badge: {
    backgroundColor: colors.softAmber,
    color: "#9a6200",
    padding: 7,
    borderRadius: 20,
    fontSize: 11,
    fontWeight: "700",
  },
  sectionRow:{flexDirection:"row",alignItems:"center",justifyContent:"space-between"},
  seeAll:{color:colors.blue,fontWeight:"800",marginTop:14},
  button: { backgroundColor: colors.blue, padding: 14, borderRadius: 12 },
  buttonText: { color: "white", fontWeight: "800" },
  nav: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: 82,
    backgroundColor: "white",
    borderTopWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
  },
  reportNav: {
    width: 56,
    height: 56,
    borderRadius: 18,
    backgroundColor: colors.blue,
    alignItems: "center",
    justifyContent: "center",
    marginTop: -28,
  },
});
