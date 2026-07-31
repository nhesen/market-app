import { useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { router } from "expo-router";
import { Button } from "../components/ui";
import { colors } from "../constants/theme";
import { customerApi } from "../services/api";
import { useI18n } from "../services/i18n";
export default function Scanner() {
  const { t } = useI18n();
  const [permission, request] = useCameraPermissions(),
    [locked, setLocked] = useState(false),
    [error, setError] = useState("");
  const last = useRef("");
  if (!permission)
    return (
      <View style={s.center}>
        <Text>{t("loading")}</Text>
      </View>
    );
  if (!permission.granted)
    return (
      <View style={s.center}>
        <Text style={s.title}>{t("scanProduct")}</Text>
        <Text style={s.help}>{t("media")}</Text>
        <Button title={t("continue")} onPress={request} />
        <Button
          secondary
          title={t("search")}
          onPress={() => router.replace("/products")}
        />
      </View>
    );
  return (
    <View style={s.page}>
      <CameraView
        style={StyleSheet.absoluteFill}
        barcodeScannerSettings={{
          barcodeTypes: ["ean13", "ean8", "upc_a", "code128"],
        }}
        onBarcodeScanned={
          locked
            ? undefined
            : async ({ data }) => {
                if (data === last.current) return;
                last.current = data;
                setLocked(true);
                try {
                  const product = await customerApi.barcode(data);
                  router.replace({
                    pathname: "/product-detail" as never,
                    params: { id: product.id },
                  });
                } catch {
                  setError(t("productsEmpty"));
                }
              }
        }
      />
      <View style={s.overlay}>
        <Text style={s.guide}>{t("barcode")}</Text>
        <View style={s.frame} />
        {error ? <Text style={s.error}>{error}</Text> : null}
        <Button
          title={t("retry")}
          onPress={() => {
            setLocked(false);
            setError("");
            last.current = "";
          }}
        />
      </View>
    </View>
  );
}
const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#000" },
  center: {
    flex: 1,
    padding: 25,
    justifyContent: "center",
    gap: 16,
    backgroundColor: colors.background,
  },
  title: { fontSize: 23, fontWeight: "900" },
  help: { color: colors.muted },
  overlay: { flex: 1, alignItems: "center", justifyContent: "center", gap: 18 },
  guide: {
    color: "white",
    fontSize: 17,
    fontWeight: "800",
    backgroundColor: "#0008",
    padding: 9,
    borderRadius: 9,
  },
  frame: {
    width: "82%",
    height: 210,
    borderWidth: 3,
    borderColor: colors.blue,
    borderRadius: 22,
  },
  error: {
    color: "white",
    backgroundColor: colors.red,
    padding: 12,
    borderRadius: 10,
  },
});
