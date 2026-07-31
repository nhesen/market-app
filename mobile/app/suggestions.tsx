import { useState } from "react";
import { Image, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  Chip,
  PageTitle,
  Screen,
  State,
  Status,
} from "../components/ui";
import { api, customerApi, uploadAsset } from "../services/api";
import { useI18n } from "../services/i18n";
import { colors } from "../constants/theme";
const values = [
  "CUSTOMER_EXPERIENCE",
  "PRODUCT_REQUEST",
  "SELF_CHECKOUT",
  "PARKING",
  "ACCESSIBILITY",
  "NEW_BRANCH_LOCATION",
  "STORE_LAYOUT",
  "RECYCLING",
  "DELIVERY",
  "CHECKOUT_PROCESS",
  "CUSTOMER_SERVICE",
  "OTHER",
];
export default function Suggestions() {
  const { t } = useI18n(),
    client = useQueryClient();
  const [title, setTitle] = useState(""),
    [description, setDescription] = useState(""),
    [category, setCategory] = useState("CUSTOMER_EXPERIENCE"),
    [anonymous, setAnonymous] = useState(false),
    [branchId, setBranchId] = useState<string>(),
    [image, setImage] = useState(""),
    [attachmentId, setAttachmentId] = useState(""),
    [progress, setProgress] = useState(0);
  const list = useQuery({
    queryKey: ["suggestions"],
    queryFn: customerApi.suggestions,
  });
  const branches = useQuery({ queryKey: ["branches"], queryFn: api.branches });
  const create = useMutation({
    mutationFn: () =>
      customerApi.createSuggestion({
        branch_id: branchId || null,
        category,
        title,
        description,
        anonymous,
        attachment_ids: attachmentId ? [attachmentId] : [],
      }),
    onSuccess: () => {
      setTitle("");
      setDescription("");
      setImage("");
      setAttachmentId("");
      setBranchId(undefined);
      client.invalidateQueries({ queryKey: ["suggestions"] });
    },
  });
  async function pick() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.75,
    });
    if (!result.canceled) {
      const uri = result.assets[0].uri;
      setImage(uri);
      setProgress(0);
      const asset = await uploadAsset(
        uri,
        result.assets[0].mimeType ?? "image/jpeg",
        setProgress,
      );
      setAttachmentId(asset.id);
    }
  }
  return (
    <Screen refreshing={list.isRefetching} onRefresh={() => list.refetch()}>
      <PageTitle
        title={t("suggestionsTitle")}
        subtitle={t("suggestionsSubtitle")}
      />
      <Card>
        <Text style={s.label}>{t("category")}</Text>
        <View style={s.chips}>
          {values.map((value) => (
            <Chip
              key={value}
              label={t(`suggestion_${value}` as any)}
              active={category === value}
              onPress={() => setCategory(value)}
            />
          ))}
        </View>
        <Text style={s.label}>{t("suggestionTitle")}</Text>
        <TextInput style={s.input} value={title} onChangeText={setTitle} />
        <Text style={s.label}>{t("description")}</Text>
        <TextInput
          style={[s.input, s.multi]}
          multiline
          value={description}
          onChangeText={setDescription}
        />
        <Text style={s.label}>{t("optionalBranch")}</Text>
        <View style={s.chips}>
          <Chip
            label={t("allBranches")}
            active={!branchId}
            onPress={() => setBranchId(undefined)}
          />
          {branches.data?.map((b) => (
            <Chip
              key={b.id}
              label={b.name}
              active={branchId === b.id}
              onPress={() => setBranchId(b.id)}
            />
          ))}
        </View>
        <Text style={s.label}>{t("optionalImage")}</Text>
        {image ? (
          <Card>
            <Image source={{ uri: image }} style={s.preview} />
            {progress < 1 ? (
              <Text style={s.progress}>
                {t("uploading")} {Math.round(progress * 100)}%
              </Text>
            ) : null}
          </Card>
        ) : (
          <Button
            secondary
            icon="images-outline"
            title={t("choosePhoto")}
            onPress={pick}
          />
        )}
        <View style={s.row}>
          <Text style={{ flex: 1 }}>{t("anonymous")}</Text>
          <Switch
            value={anonymous}
            onValueChange={setAnonymous}
            trackColor={{ true: colors.blue }}
          />
        </View>
        <Button
          disabled={
            create.isPending ||
            title.length < 4 ||
            description.length < 10 ||
            Boolean(image && !attachmentId)
          }
          title={create.isPending ? t("submitting") : t("submit")}
          onPress={() => create.mutate()}
        />
        {create.error ? (
          <Text style={s.error}>{create.error.message}</Text>
        ) : null}
      </Card>
      <Text style={s.section}>{t("mySuggestions")}</Text>
      <State
        loading={list.isLoading}
        error={list.isError}
        retry={() => list.refetch()}
        empty={!list.data?.length ? t("noSuggestions") : undefined}
      />
      {list.data?.map((x) => (
        <Card
          key={x.id}
          onPress={() =>
            router.push({
              pathname: "/suggestion-detail" as never,
              params: { id: x.id },
            })
          }
        >
          <Status value={x.status} />
          <Text style={s.title}>{x.title}</Text>
          <Text style={s.track}>{x.tracking_number}</Text>
          <Text style={s.category}>{t(`suggestion_${x.category}` as any)}</Text>
          <Text numberOfLines={2} style={s.meta}>
            {x.description}
          </Text>
        </Card>
      ))}
    </Screen>
  );
}
const s = StyleSheet.create({
  label: { fontWeight: "900", color: colors.navy },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 13,
    padding: 13,
  },
  multi: { height: 105, textAlignVertical: "top" },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  row: { flexDirection: "row", alignItems: "center" },
  preview: { width: "100%", height: 170, borderRadius: 13 },
  progress: { color: colors.blue, fontWeight: "800" },
  section: { fontSize: 19, fontWeight: "900", color: colors.navy },
  title: { fontSize: 17, fontWeight: "900", color: colors.navy },
  track: { color: colors.blue, fontWeight: "800" },
  category: { color: colors.green, fontWeight: "800", fontSize: 12 },
  meta: { color: colors.muted },
  error: { color: colors.red },
});
