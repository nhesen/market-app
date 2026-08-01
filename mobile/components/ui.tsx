import { ReactNode, useEffect, useState } from "react";
import {
  Image,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { usePathname } from "expo-router";
import { storage as SecureStore } from "../services/storage";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, radius, shadow, spacing, type } from "../constants/theme";
import { mediaUrl } from "../services/api";
import { useI18n } from "../services/i18n";
import { BottomNav } from "./BottomNav";
export function Screen({
  children,
  refreshing = false,
  onRefresh,
}: {
  children: ReactNode;
  refreshing?: boolean;
  onRefresh?: () => void;
}) {
  const path = usePathname(),
    tab = ["/products", "/cards", "/profile"].includes(path);
  return (
    <SafeAreaView style={s.safe} edges={["top", "left", "right"]}>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={s.screen}
        refreshControl={
          onRefresh ? (
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.teal}
            />
          ) : undefined
        }
      >
        {children}
      </ScrollView>
      {tab ? <BottomNav /> : null}
    </SafeAreaView>
  );
}
export function PageTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <View style={s.titleRow}>
      <View style={{ flex: 1 }}>
        <Text accessibilityRole="header" style={s.title}>
          {title}
        </Text>
        {subtitle ? <Text style={s.muted}>{subtitle}</Text> : null}
      </View>
      {action}
    </View>
  );
}
export function Card({
  children,
  onPress,
}: {
  children: ReactNode;
  onPress?: () => void;
}) {
  return onPress ? (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [s.card, pressed && s.pressed]}
    >
      {children}
    </Pressable>
  ) : (
    <View style={s.card}>{children}</View>
  );
}
export function Button({
  title,
  onPress,
  disabled = false,
  secondary = false,
  icon,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  secondary?: boolean;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.button,
        secondary && s.secondary,
        (disabled || pressed) && s.dim,
      ]}
    >
      {icon ? (
        <Ionicons
          name={icon}
          size={19}
          color={secondary ? colors.blue : colors.white}
        />
      ) : null}
      <Text style={[s.buttonText, secondary && s.secondaryText]}>{title}</Text>
    </Pressable>
  );
}
export function State({
  loading,
  error,
  empty,
  retry,
}: {
  loading?: boolean;
  error?: boolean;
  empty?: string;
  retry?: () => void;
}) {
  const { t } = useI18n();
  if (loading)
    return (
      <View accessibilityLabel={t("loading" as any)} style={s.state}>
        <Skeleton />
        <Skeleton />
        <Skeleton />
      </View>
    );
  if (error)
    return (
      <View style={s.state}>
        <View style={s.stateIcon}>
          <Ionicons
            name="cloud-offline-outline"
            size={30}
            color={colors.blue}
          />
        </View>
        <Text style={s.stateTitle}>{t("loadError")}</Text>
        {retry ? <Button secondary title={t("retry")} onPress={retry} /> : null}
      </View>
    );
  if (empty)
    return (
      <View style={s.state}>
        <View style={s.stateIcon}>
          <Ionicons name="basket-outline" size={30} color={colors.teal} />
        </View>
        <Text style={s.stateTitle}>{empty}</Text>
      </View>
    );
  return null;
}
export function Skeleton() {
  return (
    <View style={s.skeleton}>
      <View style={s.skeletonImage} />
      <View style={s.skeletonCopy}>
        <View style={s.skeletonLine} />
        <View style={[s.skeletonLine, { width: "62%" }]} />
      </View>
    </View>
  );
}
export function Status({ value }: { value: string }) {
  const { t } = useI18n();
  const key: Record<string, Parameters<typeof t>[0]> = {
    SUBMITTED: "statusSubmitted",
    RECEIVED: "statusSubmitted",
    NEW: "statusSubmitted",
    PRECHECK: "statusReview",
    UNDER_REVIEW: "statusReview",
    CONFIRMED: "statusReview",
    PLANNED: "statusPlanned",
    IMPLEMENTED: "statusImplemented",
    REJECTED: "statusRejected",
    VERIFICATION_REQUIRED: "statusVerification",
    VERIFIED: "statusReview",
    ASSIGNED: "statusReview",
    REOPENED: "statusReview",
    IN_PROGRESS: "statusProgress",
    RESOLUTION_CANDIDATE: "statusProgress",
    RESOLVED: "statusResolved",
    MANUALLY_RESOLVED: "statusResolved",
    AUTO_RESOLVED: "statusResolved",
  };
  return (
    <Text
      style={[
        s.badge,
        value.includes("RESOLVED") && s.badgeSuccess,
        value === "REJECTED" && s.badgeDanger,
      ]}
    >
      {key[value] ? t(key[value]) : value.replaceAll("_", " ")}
    </Text>
  );
}
export function RemoteImage({
  url,
  height = 150,
}: {
  url?: string;
  height?: number;
}) {
  const [failed, setFailed] = useState(false),
    [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    SecureStore.getItemAsync("token").then(setToken);
  }, []);
  const uri = mediaUrl(failed || !url ? "/assets/retail-products-v2.png" : url),
    source = uri?.includes("/api/v1/media/")
      ? { uri, headers: { Authorization: `Bearer ${token ?? ""}` } }
      : { uri },
    size = height === 92 ? { width: 92 } : { width: "100%" as const };
  return (
    <Image
      accessibilityLabel={url ? "Baxish retail media" : "Baxish placeholder"}
      accessibilityIgnoresInvertColors
      source={source}
      onError={() => setFailed(true)}
      resizeMode="cover"
      style={[s.image, { height }, size]}
    />
  );
}
export function Chip({
  label,
  active = false,
  onPress,
}: {
  label: string;
  active?: boolean;
  onPress?: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active, disabled: !onPress }}
      disabled={!onPress}
      onPress={onPress}
      style={({ pressed }) => [
        s.chip,
        active && s.chipActive,
        pressed && s.dim,
      ]}
    >
      <Text style={[s.chipText, active && s.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  screen: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: 112,
    gap: spacing.md,
    backgroundColor: colors.background,
    minHeight: "100%",
  },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  title: {
    fontSize: type.title,
    fontWeight: "900",
    letterSpacing: -0.5,
    color: colors.navy,
  },
  muted: { color: colors.muted, lineHeight: 20 },
  card: {
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    gap: 9,
    overflow: "hidden",
    ...shadow.card,
  },
  pressed: { opacity: 0.88, transform: [{ scale: 0.992 }] },
  button: {
    minHeight: 50,
    paddingHorizontal: 16,
    borderRadius: radius.md,
    backgroundColor: colors.blue,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 8,
    ...shadow.primary,
  },
  secondary: {
    backgroundColor: colors.softBlue,
    shadowOpacity: 0,
    elevation: 0,
  },
  secondaryText: { color: colors.blue },
  buttonText: { fontWeight: "800", color: colors.white, textAlign: "center" },
  dim: { opacity: 0.58 },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: colors.softAmber,
    color: "#885600",
    fontSize: 11,
    fontWeight: "800",
    paddingVertical: 7,
    paddingHorizontal: 10,
    borderRadius: radius.pill,
    overflow: "hidden",
  },
  badgeSuccess: { backgroundColor: colors.softGreen, color: colors.green },
  badgeDanger: { backgroundColor: "#FFE9ED", color: colors.red },
  state: { paddingVertical: 32, alignItems: "center", gap: 13 },
  stateIcon: {
    width: 58,
    height: 58,
    borderRadius: 20,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  stateTitle: { color: colors.muted, fontWeight: "700", textAlign: "center" },
  skeleton: {
    height: 96,
    width: "100%",
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    flexDirection: "row",
    padding: 12,
    gap: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  skeletonImage: { width: 72, borderRadius: 13, backgroundColor: "#E4EBF4" },
  skeletonCopy: { flex: 1, gap: 10, justifyContent: "center" },
  skeletonLine: {
    height: 12,
    width: "88%",
    borderRadius: 8,
    backgroundColor: "#E4EBF4",
  },
  image: {
    width: "100%",
    borderRadius: radius.md,
    backgroundColor: colors.softBlue,
  },
  chip: {
    minHeight: 44,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    justifyContent: "center",
  },
  chipActive: { backgroundColor: colors.navy, borderColor: colors.navy },
  chipText: { color: colors.muted, fontWeight: "700", fontSize: 12 },
  chipTextActive: { color: colors.white },
});
