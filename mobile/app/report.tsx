import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, selectedBranchId, uploadAsset } from "../services/api";
import { Button, Card, Chip, PageTitle, Screen, State } from "../components/ui";
import { colors } from "../constants/theme";
import { useI18n } from "../services/i18n";
const subcategoryValues: Record<string, string[]> = {
  PRODUCT: [
    "EXPIRED",
    "DAMAGED_PACKAGING",
    "OPENED_PACKAGE",
    "SPOILED",
    "UNREADABLE_DATE",
    "STORAGE_TEMPERATURE",
    "MISSING_INFORMATION",
  ],
  SHELF_AND_PRICE: [
    "EMPTY_SHELF",
    "MISSING_PRICE_LABEL",
    "SHELF_CHECKOUT_MISMATCH",
    "PROMOTION_NOT_APPLIED",
    "DISORGANISED_SHELF",
    "WRONG_LOCATION",
  ],
  CLEANLINESS_AND_SAFETY: [
    "SPILL",
    "BROKEN_GLASS",
    "DIRTY_AREA",
    "BLOCKED_AISLE",
    "BLOCKED_EXIT",
    "DAMAGED_CART",
    "REFRIGERATOR_LEAK",
  ],
  SERVICE: [
    "LONG_QUEUE",
    "TOO_FEW_CHECKOUTS",
    "PAYMENT_TERMINAL_FAILURE",
    "NO_CARTS",
    "PRICE_CHECKER_FAILURE",
    "ASSISTANCE_REQUIRED",
  ],
  OTHER: ["OTHER"],
};
export default function Report() {
  const { t } = useI18n(),
    params = useLocalSearchParams<{
      category?: string;
      title?: string;
      description?: string;
      barcode?: string;
      productId?: string;
      subcategory?: string;
      attachmentId?: string;
      mediaUri?: string;
    }>();
  const [title, setTitle] = useState(params.title ?? ""),
    [description, setDescription] = useState(params.description ?? ""),
    [category, setCategory] = useState(params.category ?? ""),
    [subcategory, setSubcategory] = useState(params.subcategory ?? ""),
    [branchId, setBranchId] = useState(""),
    [step, setStep] = useState(1),
    [mediaUri, setMediaUri] = useState(params.mediaUri ?? ""),
    [mediaType, setMediaType] = useState("image/jpeg"),
    [attachmentId, setAttachmentId] = useState(params.attachmentId ?? ""),
    [cameraOpen, setCameraOpen] = useState(false),
    [progress, setProgress] = useState(0),
    [uploadError, setUploadError] = useState(""),
    [aiResult, setAiResult] = useState<any>();
  const [p, setPermission] = useCameraPermissions(),
    camera = useRef<CameraView>(null);
  const branches = useQuery({ queryKey: ["branches"], queryFn: api.branches });
  useEffect(() => {
    selectedBranchId().then((id) =>
      setBranchId(id || branches.data?.[0]?.id || ""),
    );
  }, [branches.data]);
  useEffect(() => {
    setSubcategory((current) =>
      (subcategoryValues[category] ?? []).includes(current) ? current : "",
    );
  }, [category]);
  const categories = [
    ["PRODUCT", t("categoryProduct")],
    ["SHELF_AND_PRICE", t("categoryShelf")],
    ["CLEANLINESS_AND_SAFETY", t("categorySafety")],
    ["SERVICE", t("categoryService")],
    ["OTHER", t("categoryOther")],
  ];
  const review = useMutation({
    mutationFn: () => api.reviewReport({ title, description, category }),
    onSuccess: (value) => {
      setAiResult(value);
      setStep(3);
    },
  });
  const submit = useMutation({
    mutationFn: () =>
      api.createReport({
        branch_id: branchId,
        category: aiResult?.suggested_category ?? category,
        subcategory,
        product_id: params.productId || null,
        barcode: params.barcode || null,
        title,
        description,
        attachment_ids: attachmentId ? [attachmentId] : [],
      }),
    onSuccess: (r) => {
      Alert.alert(
        t("reportSent"),
        `${t("trackingNumber")}: ${r.tracking_number}`,
      );
      router.replace({ pathname: "/report-detail", params: { id: r.id } });
    },
  });
  async function send(uri: string, type: string) {
    setMediaUri(uri);
    setMediaType(type);
    setUploadError("");
    setAttachmentId("");
    setProgress(0);
    try {
      const asset = await uploadAsset(uri, type, setProgress);
      setAttachmentId(asset.id);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : t("loadError"));
    }
  }
  async function openCamera() {
    if (!p?.granted) {
      const result = await setPermission();
      if (!result.granted) return;
    }
    setCameraOpen(true);
  }
  async function capture() {
    const image = await camera.current?.takePictureAsync({ quality: 0.75 });
    if (image) {
      setCameraOpen(false);
      await send(image.uri, "image/jpeg");
    }
  }
  async function pick(kind: "images" | "videos") {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: [kind],
      quality: 0.75,
      videoMaxDuration: 15,
    });
    if (!result.canceled) {
      const asset = result.assets[0];
      await send(
        asset.uri,
        asset.mimeType ?? (kind === "videos" ? "video/mp4" : "image/jpeg"),
      );
    }
  }
  if (cameraOpen)
    return (
      <View style={s.camera}>
        <CameraView
          ref={camera}
          style={StyleSheet.absoluteFill}
          facing="back"
        />
        <View style={s.overlay}>
          <Pressable style={s.shutter} onPress={capture}>
            <View style={s.inner} />
          </Pressable>
          <Button
            secondary
            title={t("cancel")}
            onPress={() => setCameraOpen(false)}
          />
        </View>
      </View>
    );
  const chosen = branches.data?.find((x) => x.id === branchId),
    subcategories = subcategoryValues[category] ?? [];
  return (
    <Screen>
      <Text style={s.progressLabel}>
        {t("step")} {step}/3
      </Text>
      <View style={s.progressTrack}>
        <View style={[s.progressFill, { width: `${(step / 3) * 100}%` }]} />
      </View>
      <PageTitle title={t("reportWizard")} subtitle={t("humanReview")} />
      <State
        loading={branches.isLoading}
        error={branches.isError}
        retry={() => branches.refetch()}
      />
      {step === 1 ? (
        <>
          <Text style={s.label}>{t("chooseCategory")}</Text>
          <View style={s.chips}>
            {categories.map(([value, label]) => (
              <Chip
                key={value}
                label={label}
                active={category === value}
                onPress={() => setCategory(value)}
              />
            ))}
          </View>
          {category ? (
            <>
              <Text style={s.label}>{t("subcategory")}</Text>
              <View style={s.chips}>
                {subcategories.map((value) => (
                  <Chip
                    key={value}
                    label={t(`sub_${value}` as any)}
                    active={subcategory === value}
                    onPress={() => setSubcategory(value)}
                  />
                ))}
              </View>
            </>
          ) : null}
          <Text style={s.label}>{t("chooseBranch")}</Text>
          {branches.data?.map((b) => (
            <Card key={b.id} onPress={() => setBranchId(b.id)}>
              <View style={s.row}>
                <View style={[s.radio, branchId === b.id && s.radioActive]} />
                <View>
                  <Text style={s.branch}>{b.name}</Text>
                  <Text style={s.meta}>{b.address}</Text>
                </View>
              </View>
            </Card>
          ))}
          <Button
            disabled={!category || !subcategory || !branchId}
            title={t("continue")}
            onPress={() => setStep(2)}
          />
        </>
      ) : null}
      {step === 2 ? (
        <>
          <Text style={s.label}>{t("reportTitle")}</Text>
          <TextInput
            style={s.input}
            placeholder={t("reportTitleHint")}
            value={title}
            onChangeText={setTitle}
          />
          <Text style={s.label}>{t("description")}</Text>
          <TextInput
            style={[s.input, s.multi]}
            multiline
            placeholder={t("descriptionHint")}
            value={description}
            onChangeText={setDescription}
          />
          {params.barcode ? (
            <Card>
              <Text style={s.prefill}>{t("linkedProduct")}</Text>
              <Text>
                {t("barcode")}: {params.barcode}
              </Text>
            </Card>
          ) : null}
          <Text style={s.label}>{t("media")}</Text>
          {mediaUri ? (
            <Card>
              {mediaType.startsWith("image/") ? (
                <Image source={{ uri: mediaUri }} style={s.preview} />
              ) : (
                <View style={s.video}>
                  <Ionicons name="videocam" size={42} color={colors.blue} />
                  <Text style={s.videoText}>{t("shortVideo")}</Text>
                </View>
              )}
              {progress < 1 && !uploadError ? (
                <>
                  <Text style={s.meta}>
                    {t("uploading")} {Math.round(progress * 100)}%
                  </Text>
                  <View style={s.uploadTrack}>
                    <View
                      style={[s.uploadFill, { width: `${progress * 100}%` }]}
                    />
                  </View>
                </>
              ) : null}
              {uploadError ? (
                <>
                  <Text style={s.error}>{uploadError}</Text>
                  <Button
                    secondary
                    title={t("uploadRetry")}
                    onPress={() => send(mediaUri, mediaType)}
                  />
                </>
              ) : null}
            </Card>
          ) : (
            <View style={s.mediaActions}>
              <Button
                secondary
                icon="camera-outline"
                title={t("takePhoto")}
                onPress={openCamera}
              />
              <Button
                secondary
                icon="images-outline"
                title={t("choosePhoto")}
                onPress={() => pick("images")}
              />
              <Button
                secondary
                icon="videocam-outline"
                title={t("chooseVideo")}
                onPress={() => pick("videos")}
              />
            </View>
          )}
          <Button
            disabled={
              title.trim().length < 4 ||
              description.trim().length < 10 ||
              Boolean(mediaUri && !attachmentId) ||
              review.isPending
            }
            title={t("aiReview")}
            onPress={() => review.mutate()}
          />
          <Button secondary title={t("back")} onPress={() => setStep(1)} />
        </>
      ) : null}
      {step === 3 ? (
        <>
          <Card>
            <Text style={s.ai}>MARTIQ Assist</Text>
            <Text>{aiResult?.summary}</Text>
            {aiResult?.warnings?.map((x: string) => (
              <Text style={s.warning} key={x}>
                {x}
              </Text>
            ))}
          </Card>
          <Card>
            <Text style={s.title}>{title}</Text>
            <Text>{description}</Text>
            <Text style={s.meta}>
              {chosen?.name} · {t(`sub_${subcategory}` as any)}
            </Text>
            {mediaUri && mediaType.startsWith("image/") ? (
              <Image source={{ uri: mediaUri }} style={s.preview} />
            ) : null}
          </Card>
          {submit.error ? (
            <Text style={s.error}>{submit.error.message}</Text>
          ) : null}
          <Button
            disabled={submit.isPending}
            title={submit.isPending ? t("submitting") : t("submit")}
            onPress={() => submit.mutate()}
          />
          <Button secondary title={t("edit")} onPress={() => setStep(2)} />
        </>
      ) : null}
    </Screen>
  );
}
const s = StyleSheet.create({
  progressLabel: { color: colors.blue, fontWeight: "900" },
  progressTrack: { height: 5, borderRadius: 3, backgroundColor: colors.border },
  progressFill: { height: 5, borderRadius: 3, backgroundColor: colors.blue },
  label: { fontWeight: "900", color: colors.navy },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  input: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    padding: 14,
  },
  multi: { height: 130, textAlignVertical: "top" },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  radio: {
    width: 21,
    height: 21,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: colors.border,
  },
  radioActive: { borderWidth: 6, borderColor: colors.blue },
  branch: { fontWeight: "900", color: colors.navy },
  meta: { color: colors.muted },
  prefill: { color: colors.blue, fontWeight: "800" },
  mediaActions: { gap: 9 },
  preview: { width: "100%", height: 200, borderRadius: 14 },
  video: {
    height: 150,
    borderRadius: 14,
    backgroundColor: colors.softBlue,
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  videoText: { color: colors.blue, fontWeight: "800" },
  uploadTrack: { height: 7, backgroundColor: colors.border, borderRadius: 4 },
  uploadFill: { height: 7, backgroundColor: colors.green, borderRadius: 4 },
  error: { color: colors.red },
  ai: { fontSize: 18, fontWeight: "900", color: colors.blue },
  warning: {
    color: "#8A5700",
    backgroundColor: colors.softAmber,
    padding: 9,
    borderRadius: 9,
  },
  title: { fontSize: 19, fontWeight: "900", color: colors.navy },
  camera: { flex: 1, backgroundColor: "black" },
  overlay: {
    position: "absolute",
    left: 25,
    right: 25,
    bottom: 35,
    alignItems: "center",
    gap: 15,
  },
  shutter: {
    width: 78,
    height: 78,
    borderRadius: 39,
    borderWidth: 4,
    borderColor: "white",
    alignItems: "center",
    justifyContent: "center",
  },
  inner: { width: 58, height: 58, borderRadius: 29, backgroundColor: "white" },
});
