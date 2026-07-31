import { useRef, useState } from "react";
import {
  Alert,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { CameraView, useCameraPermissions } from "expo-camera";
import { Ionicons } from "@expo/vector-icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { staffApi, uploadAsset, uploadImage } from "../services/api";
import {
  Button,
  Card,
  PageTitle,
  Screen,
  State,
  Status,
} from "../components/ui";
import { colors } from "../constants/theme";

type Mode = "detail" | "barcode" | "date" | "itemReview" | "completion";
const conditions = [
  "NORMAL",
  "EXPIRING_SOON",
  "EXPIRED",
  "DAMAGED",
  "INVALID_PRODUCT",
  "UNREADABLE",
];

export default function Audit() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    client = useQueryClient(),
    camera = useRef<CameraView>(null);
  const task = useQuery({
    queryKey: ["audit", id],
    queryFn: () => staffApi.audit(id!),
    enabled: Boolean(id),
  });
  const [mode, setMode] = useState<Mode>("detail"),
    [barcode, setBarcode] = useState(""),
    [product, setProduct] = useState<any>();
  const [date, setDate] = useState(""),
    [confirmed, setConfirmed] = useState(false),
    [condition, setCondition] = useState("NORMAL"),
    [note, setNote] = useState("");
  const [photo, setPhoto] = useState(""),
    [photoKey, setPhotoKey] = useState(""),
    [candidates, setCandidates] = useState<string[]>([]),
    [ocrEngine, setOcrEngine] = useState(""),
    [ocrOriginal, setOcrOriginal] = useState(""),
    [corrections, setCorrections] = useState(0),
    [processing, setProcessing] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const refresh = () => {
    client.invalidateQueries({ queryKey: ["audit", id] });
    client.invalidateQueries({ queryKey: ["audits"] });
    client.invalidateQueries({ queryKey: ["staff-dashboard"] });
  };
  const start = useMutation({
    mutationFn: () => staffApi.start(id!),
    onSuccess: () => {
      refresh();
      setMode("detail");
    },
  });
  const add = useMutation({
    mutationFn: () =>
      staffApi.addItem(id!, {
        barcode,
        confirmed_date: date,
        date_confirmed: confirmed,
        ocr_corrected: Boolean(ocrOriginal && date !== ocrOriginal),
        ocr_engine: ocrEngine,
        ocr_candidates: candidates,
        correction_count: corrections,
        condition,
        note,
        photo_key: photoKey,
      }),
    onSuccess: () => {
      resetItem();
      refresh();
      setMode("detail");
    },
    onError: (error) => Alert.alert("Məhsul saxlanmadı", error.message),
  });
  const complete = useMutation({
    mutationFn: () => staffApi.complete(id!),
    onSuccess: () => {
      refresh();
      Alert.alert(
        "Audit tamamlandı",
        "Başlama və tamamlanma vaxtı, nəticələr və keyfiyyət yoxlamaları saxlanıldı.",
        [{ text: "Panelə qayıt", onPress: () => router.replace("/staff") }],
      );
    },
    onError: (error) => Alert.alert("Audit tamamlanmadı", error.message),
  });
  function resetItem() {
    setBarcode("");
    setProduct(undefined);
    setDate("");
    setConfirmed(false);
    setCondition("NORMAL");
    setNote("");
    setPhoto("");
    setPhotoKey("");
    setCandidates([]);
    setOcrEngine("");
    setOcrOriginal("");
    setCorrections(0);
  }
  async function allow(next: "barcode" | "date") {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) {
        Alert.alert(
          "Kamera icazəsi lazımdır",
          "Barkod və tarix sübutu yalnız kamera ilə toplanır.",
        );
        return;
      }
    }
    setMode(next);
  }
  async function acceptBarcode(value: string) {
    if (
      task.data?.unique_products &&
      task.data.items.some((item: any) => item.barcode === value)
    ) {
      Alert.alert(
        "Təkrar barkod",
        "Bu audit unikal məhsullar tələb edir və barkod artıq istifadə olunub.",
      );
      setMode("detail");
      return;
    }
    setProcessing(true);
    try {
      const found = await staffApi.productByBarcode(value);
      setBarcode(value);
      setProduct(found);
      setMode("detail");
    } catch (error) {
      Alert.alert(
        "Məhsul tapılmadı",
        error instanceof Error ? error.message : "Bu marketdə məhsul yoxdur.",
      );
      setMode("detail");
    } finally {
      setProcessing(false);
    }
  }
  async function captureDate() {
    const picture = await camera.current?.takePictureAsync({ quality: 0.85 });
    if (!picture) return;
    setProcessing(true);
    try {
      const [ocr, asset] = await Promise.all([
        uploadImage(picture.uri),
        uploadAsset(picture.uri, "image/jpeg"),
      ]);
      setPhoto(picture.uri);
      setPhotoKey(asset.id);
      setCandidates(ocr.candidates ?? []);
      setOcrEngine(ocr.engine);
      const first = ocr.candidates?.[0] ?? "";
      setDate(first);
      setOcrOriginal(first);
      setConfirmed(false);
      setMode("detail");
    } catch (error) {
      Alert.alert(
        "Şəkil işlənmədi",
        error instanceof Error ? error.message : "Yenidən çəkin.",
      );
      setMode("detail");
    } finally {
      setProcessing(false);
    }
  }
  if (mode === "barcode")
    return (
      <View style={s.cameraPage}>
        <CameraView
          style={StyleSheet.absoluteFill}
          barcodeScannerSettings={{
            barcodeTypes: ["ean13", "ean8", "upc_a", "code128"],
          }}
          onBarcodeScanned={({ data }) => acceptBarcode(data)}
        />
        <View style={s.overlay}>
          <Text style={s.cameraText}>
            Barkodu çərçivənin daxilində saxlayın
          </Text>
          <View style={s.barcodeFrame} />
          {processing ? (
            <Text style={s.cameraText}>Məhsul yoxlanılır…</Text>
          ) : null}
          <Button secondary title="Ləğv et" onPress={() => setMode("detail")} />
        </View>
      </View>
    );
  if (mode === "date")
    return (
      <View style={s.cameraPage}>
        <CameraView
          ref={camera}
          style={StyleSheet.absoluteFill}
          facing="back"
        />
        <View style={s.overlay}>
          <Text style={s.cameraText}>
            Tarixi yaxınlaşdırın · parıltını azaldın · yazını aydın saxlayın
          </Text>
          <View style={s.dateFrame} />
          <Pressable
            disabled={processing}
            style={s.shutter}
            onPress={captureDate}
          >
            <View style={s.shutterInner} />
          </Pressable>
          <Button secondary title="Ləğv et" onPress={() => setMode("detail")} />
        </View>
      </View>
    );
  if (task.isLoading || task.isError)
    return (
      <Screen>
        <State
          loading={task.isLoading}
          error={task.isError}
          retry={() => task.refetch()}
        />
      </Screen>
    );
  const data = task.data,
    canComplete = data.item_count >= data.required_count;
  if (mode === "completion")
    return (
      <Screen>
        <PageTitle
          title="Audit nəticəsini yoxlayın"
          subtitle="Göndərdikdən sonra tapıntılar branch admin üçün görünəcək."
        />
        <Text style={s.count}>
          {data.item_count}/{data.required_count} məhsul
        </Text>
        {data.items.map((item: any) => (
          <Card key={item.id}>
            <View style={s.row}>
              <Text style={s.product}>{item.product}</Text>
              <Status value={item.condition} />
            </View>
            <Text style={s.meta}>
              {item.barcode} · {item.confirmed_date}
            </Text>
            <Text style={s.meta}>
              Şəkil: ✓ · Tarix təsdiqi: {item.date_confirmed ? "✓" : "—"}
            </Text>
            {item.note ? <Text>{item.note}</Text> : null}
          </Card>
        ))}
        {!canComplete ? (
          <Text style={s.error}>Tələb olunan məhsul sayı tamamlanmayıb.</Text>
        ) : null}
        <Button
          disabled={!canComplete || complete.isPending}
          title={complete.isPending ? "Tamamlanır…" : "Auditi yekunlaşdır"}
          onPress={() => complete.mutate()}
        />
        <Button
          secondary
          title="Auditə qayıt"
          onPress={() => setMode("detail")}
        />
      </Screen>
    );
  if (mode === "itemReview")
    return (
      <Screen>
        <PageTitle
          title="Məhsul nəticəsini təsdiqləyin"
          subtitle="OCR avtomatik qərar deyil. Son qərar sizindir."
        />
        <Card>
          <Text style={s.product}>{product?.name}</Text>
          <Text>
            {product?.brand} · {barcode}
          </Text>
          {photo ? <Image source={{ uri: photo }} style={s.preview} /> : null}
          <Text>
            Tarix: <Text style={s.bold}>{date}</Text>
          </Text>
          <Text>
            Vəziyyət: <Text style={s.bold}>{condition}</Text>
          </Text>
          <Text>
            OCR düzəlişi:{" "}
            {ocrOriginal && date !== ocrOriginal ? "Bəli" : "Xeyr"}
          </Text>
          <Text>
            Təsdiq:{" "}
            {confirmed
              ? "Əməkdaş tərəfindən açıq təsdiqlənib"
              : "Təsdiqlənməyib"}
          </Text>
        </Card>
        <Button
          disabled={!confirmed || add.isPending}
          title={add.isPending ? "Saxlanılır…" : "Məhsulu auditə əlavə et"}
          onPress={() => add.mutate()}
        />
        <Button
          secondary
          title="Düzəliş et"
          onPress={() => setMode("detail")}
        />
      </Screen>
    );
  return (
    <Screen>
      <PageTitle title={data.title} subtitle={data.instructions} />
      <Card>
        <View style={s.row}>
          <Status value={data.status} />
          <Text style={s.priority}>{data.priority}</Text>
        </View>
        <Text style={s.meta}>
          Son vaxt: {new Date(data.due_at).toLocaleString("az-AZ")}
        </Text>
        <Text style={s.count}>
          {data.item_count}/{data.required_count} məhsul · {data.progress}%
        </Text>
        <View style={s.track}>
          <View
            style={[s.fill, { width: `${Math.min(data.progress, 100)}%` }]}
          />
        </View>
        <Text style={s.meta}>
          {data.unique_products
            ? "Hər məhsul unikal olmalıdır"
            : "Eyni məhsul təkrar yoxlana bilər"}
        </Text>
        {data.status === "ASSIGNED" || data.status === "OVERDUE" ? (
          <Button title="Auditi başlat" onPress={() => start.mutate()} />
        ) : null}
      </Card>
      {data.status === "IN_PROGRESS" ? (
        <>
          <Card>
            <Text style={s.step}>1 · Məhsul barkodu</Text>
            <Button
              secondary
              icon="barcode-outline"
              title={
                product ? `✓ ${product.name}` : "Kamera ilə barkod skan et"
              }
              onPress={() => allow("barcode")}
            />
            {product ? (
              <Text style={s.meta}>
                {product.brand} · {product.category} · {barcode}
              </Text>
            ) : null}
            <Text style={s.step}>2 · Son istifadə tarixi sübutu</Text>
            <Button
              secondary
              icon="camera-outline"
              title={
                photo
                  ? "✓ Şəkil və OCR hazırdır"
                  : "Tarix sahəsinin şəklini çək"
              }
              onPress={() => allow("date")}
            />
            {photo ? <Image source={{ uri: photo }} style={s.preview} /> : null}
            <Text style={s.ocr}>
              OCR: {ocrEngine || "gözləyir"}. Namizədlər ayrıca təsdiq
              edilməlidir.
            </Text>
            {candidates.length ? (
              <View style={s.chips}>
                {candidates.map((value) => (
                  <Pressable
                    key={value}
                    onPress={() => {
                      setDate(value);
                      setConfirmed(false);
                    }}
                  >
                    <Text style={[s.chip, date === value && s.selected]}>
                      {value}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : photo ? (
              <Text style={s.warning}>
                OCR tarix oxumadı. Şəkli yenidən çəkə və ya tarixi manual
                düzəldə bilərsiniz; bu hal keyfiyyət flagı yaradacaq.
              </Text>
            ) : null}
            <TextInput
              style={s.input}
              placeholder="DD.MM.YYYY"
              value={date}
              onChangeText={(value) => {
                setDate(value);
                setConfirmed(false);
                setCorrections((x) => x + 1);
              }}
            />
            <Pressable
              style={[s.confirm, confirmed && s.confirmed]}
              onPress={() => setConfirmed(!confirmed)}
            >
              <Ionicons
                name={confirmed ? "checkbox" : "square-outline"}
                size={24}
                color={confirmed ? colors.green : colors.muted}
              />
              <Text style={s.confirmText}>
                Tarixi şəkillə müqayisə etdim və şəxsən təsdiqləyirəm
              </Text>
            </Pressable>
            <Text style={s.step}>3 · Məhsulun vəziyyəti</Text>
            <View style={s.chips}>
              {conditions.map((value) => (
                <Pressable key={value} onPress={() => setCondition(value)}>
                  <Text style={[s.chip, condition === value && s.selected]}>
                    {value}
                  </Text>
                </Pressable>
              ))}
            </View>
            <TextInput
              style={[s.input, s.note]}
              multiline
              placeholder="Tapıntı barədə qeyd"
              value={note}
              onChangeText={setNote}
            />
            <Button
              disabled={!product || !photoKey || !date || !confirmed}
              title="Məhsulu review et"
              onPress={() => setMode("itemReview")}
            />
          </Card>
          {data.items.length ? (
            <>
              <Text style={s.step}>Saxlanmış məhsullar</Text>
              {data.items.map((item: any) => (
                <Card key={item.id}>
                  <View style={s.row}>
                    <Text style={s.product}>{item.product}</Text>
                    <Status value={item.condition} />
                  </View>
                  <Text style={s.meta}>
                    {item.barcode} · {item.confirmed_date}
                  </Text>
                </Card>
              ))}
            </>
          ) : null}
          <Button
            title="Tamamlama review-u"
            onPress={() => setMode("completion")}
          />
        </>
      ) : null}
      {data.status === "COMPLETED" ? (
        <>
          <Text style={s.ok}>Audit tamamlanıb</Text>
          <Button
            title="Panelə qayıt"
            onPress={() => router.replace("/staff")}
          />
        </>
      ) : null}
    </Screen>
  );
}

const s = StyleSheet.create({
  cameraPage: { flex: 1, backgroundColor: "black" },
  overlay: {
    position: "absolute",
    inset: 0,
    alignItems: "center",
    justifyContent: "space-around",
    padding: 28,
  },
  cameraText: {
    color: "white",
    fontWeight: "900",
    backgroundColor: "#0009",
    padding: 10,
    borderRadius: 10,
    textAlign: "center",
  },
  barcodeFrame: {
    width: "90%",
    height: 170,
    borderWidth: 3,
    borderColor: "white",
    borderRadius: 20,
  },
  dateFrame: {
    width: "90%",
    height: 110,
    borderWidth: 3,
    borderColor: "white",
    borderRadius: 16,
  },
  shutter: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 4,
    borderColor: "white",
    alignItems: "center",
    justifyContent: "center",
  },
  shutterInner: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: "white",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 8,
  },
  priority: { fontWeight: "900", color: colors.red },
  meta: { color: colors.muted, lineHeight: 19 },
  count: { fontSize: 17, fontWeight: "900", color: colors.navy },
  track: {
    height: 9,
    borderRadius: 9,
    backgroundColor: colors.border,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: colors.green },
  step: { fontWeight: "900", color: colors.navy, fontSize: 16, marginTop: 5 },
  product: { fontWeight: "900", color: colors.navy, fontSize: 17, flex: 1 },
  preview: { height: 180, width: "100%", borderRadius: 13 },
  ocr: { fontSize: 12, color: colors.muted },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  chip: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: colors.softBlue,
    color: colors.blue,
    fontSize: 11,
    fontWeight: "800",
  },
  selected: { backgroundColor: colors.blue, color: "white" },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 13,
    backgroundColor: "white",
  },
  note: { height: 80, textAlignVertical: "top" },
  confirm: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  confirmed: { backgroundColor: "#EAF8F2", borderColor: colors.green },
  confirmText: { flex: 1, fontWeight: "700", color: colors.navy },
  warning: {
    color: "#8A5700",
    backgroundColor: colors.softAmber,
    padding: 10,
    borderRadius: 10,
  },
  error: { color: colors.red, fontWeight: "800" },
  ok: {
    color: colors.green,
    fontWeight: "900",
    textAlign: "center",
    fontSize: 18,
  },
  bold: { fontWeight: "900" },
});
