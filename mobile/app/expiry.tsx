import { useRef, useState } from "react";
import { Image, StyleSheet, Text, TextInput, View } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { router, useLocalSearchParams } from "expo-router";
import { Button, Card, PageTitle, Screen } from "../components/ui";
import { uploadAsset, uploadImage } from "../services/api";
import { colors } from "../constants/theme";
import { useI18n } from "../services/i18n";

export default function Expiry() {
  const { name, barcode, productId } = useLocalSearchParams<{
    name: string;
    barcode: string;
    productId: string;
  }>();
  const { t } = useI18n();
  const [permission, requestPermission] = useCameraPermissions();
  const camera = useRef<CameraView>(null);
  const [uri, setUri] = useState("");
  const [candidates, setCandidates] = useState<string[]>([]);
  const [date, setDate] = useState("");
  const [engine, setEngine] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [reporting, setReporting] = useState(false);

  if (!permission?.granted)
    return (
      <View style={s.center}>
        <Text>{t("expiryPermission")}</Text>
        <Button title={t("allowCamera")} onPress={requestPermission} />
      </View>
    );
  if (!uri)
    return (
      <View style={{ flex: 1 }}>
        <CameraView ref={camera} style={{ flex: 1 }} facing="back">
          <View style={s.cameraGuide}>
            <Text style={s.white}>{t("expiryGuide")}</Text>
            <View style={s.dateFrame} />
            <Text style={s.white}>{t("holdSteady")}</Text>
            <Button
              title={t("takePhoto")}
              onPress={async () => {
                const picture = await camera.current?.takePictureAsync({
                  quality: 0.75,
                });
                if (picture) setUri(picture.uri);
              }}
            />
          </View>
        </CameraView>
      </View>
    );

  async function createReport() {
    setReporting(true);
    try {
      const asset = await uploadAsset(uri);
      router.push({
        pathname: "/report",
        params: {
          category: "PRODUCT",
          subcategory: "EXPIRED",
          productId,
          barcode,
          title: t("expiredReportTitle").replace("{product}", name || ""),
          description: t("expiredReportDescription").replace("{date}", date),
          attachmentId: asset.id,
          mediaUri: uri,
        },
      });
    } finally {
      setReporting(false);
    }
  }

  function confirmDate() {
    const parts = date.split(/[./-]/).map(Number);
    const parsed = date.startsWith("20")
      ? new Date(date)
      : new Date(
          parts[2] < 100 ? 2000 + parts[2] : parts[2],
          parts[1] - 1,
          parts[0],
        );
    const days = (parsed.getTime() - Date.now()) / 86400000;
    setResult(
      Number.isNaN(days)
        ? "UNREADABLE"
        : days < 0
          ? "EXPIRED"
          : days <= 7
            ? "EXPIRING_SOON"
            : "VALID",
    );
  }

  return (
    <Screen>
      <PageTitle
        title={t("confirmExpiry")}
        subtitle={`${name ?? ""} · ${barcode ?? ""}`}
      />
      <Image source={{ uri }} style={s.preview} />
      <Button
        secondary
        title={t("retake")}
        onPress={() => {
          setUri("");
          setCandidates([]);
          setDate("");
          setResult("");
        }}
      />
      <Button
        title={loading ? t("ocrScanning") : t("findDateCandidates")}
        disabled={loading}
        onPress={async () => {
          setLoading(true);
          try {
            const value = await uploadImage(uri);
            setCandidates(value.candidates);
            setEngine(value.engine);
          } finally {
            setLoading(false);
          }
        }}
      />
      <Card>
        <Text style={s.label}>{t("ocrCandidates")}</Text>
        {candidates.length ? (
          candidates.map((value) => (
            <Text
              key={value}
              style={s.candidate}
              onPress={() => setDate(value)}
            >
              {value}
            </Text>
          ))
        ) : engine ? (
          <Text style={s.help}>
            {t("noDateFound")} · {engine}
          </Text>
        ) : null}
        <TextInput
          accessibilityLabel={t("manualDate")}
          style={s.input}
          placeholder="DD.MM.YYYY"
          value={date}
          onChangeText={setDate}
        />
        <Button
          disabled={!date}
          title={t("confirmDateExplicitly")}
          onPress={confirmDate}
        />
        {result ? (
          <>
            <Text
              style={[s.result, result === "EXPIRED" && { color: colors.red }]}
            >
              {t(`expiryResult_${result}` as any)}
            </Text>
            {result === "EXPIRED" ? (
              <Button
                disabled={reporting}
                title={reporting ? t("uploading") : t("reportToBranch")}
                onPress={createReport}
              />
            ) : null}
          </>
        ) : null}
      </Card>
    </Screen>
  );
}

const s = StyleSheet.create({
  center: { flex: 1, padding: 24, justifyContent: "center", gap: 15 },
  cameraGuide: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
    padding: 20,
  },
  white: {
    color: "white",
    fontWeight: "800",
    textAlign: "center",
    backgroundColor: "#0008",
    padding: 10,
    borderRadius: 8,
  },
  dateFrame: {
    width: "90%",
    height: 150,
    borderWidth: 3,
    borderColor: colors.blue,
    borderRadius: 18,
  },
  preview: { width: "100%", height: 230, borderRadius: 16 },
  label: { fontWeight: "900" },
  candidate: {
    padding: 12,
    backgroundColor: colors.softBlue,
    borderRadius: 10,
    color: colors.blue,
    fontWeight: "800",
  },
  help: { color: colors.muted },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 13,
  },
  result: {
    fontWeight: "900",
    fontSize: 18,
    color: colors.green,
    textAlign: "center",
  },
});
