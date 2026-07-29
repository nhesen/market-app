import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { login } from "../services/api";
import { colors } from "../constants/theme";
import { useI18n } from "../services/i18n";

function Field({ icon, ...props }: { icon: keyof typeof Ionicons.glyphMap } & React.ComponentProps<typeof TextInput>) {
  return <View style={s.field}><Ionicons name={icon} size={20} color={colors.muted}/><TextInput placeholderTextColor={colors.muted} style={s.input} {...props}/></View>;
}

export default function Login() {
  const { t } = useI18n();
  const [email, setEmail] = useState("customer@demo.az"), [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);
  async function submit() {
    setError(""); setBusy(true);
    try {
      const user = await login(email.trim(), password);
      if (user.role === "STAFF") router.replace("/staff");
      else if (user.role === "CUSTOMER") router.replace("/");
      else throw new Error(t("customerRequired"));
    } catch (value) { setError(value instanceof Error ? value.message : t("loadError")); }
    finally { setBusy(false); }
  }
  return <SafeAreaView style={s.safe}><KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS === "ios" ? "padding" : undefined}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.page}>
    <View style={s.hero}><View style={s.logo}><Ionicons name="storefront" size={34} color="white"/></View><Text style={s.brand}>{t("appName")}</Text><Text style={s.title}>{t("welcome")}</Text><Text style={s.subtitle}>{t("loginSubtitle")}</Text></View>
    <View style={s.card}><Field icon="mail-outline" autoCapitalize="none" keyboardType="email-address" placeholder={t("email")} value={email} onChangeText={setEmail}/><Field icon="lock-closed-outline" secureTextEntry placeholder={t("password")} value={password} onChangeText={setPassword}/><Pressable style={s.forgot} onPress={()=>router.push("/forgot-password" as never)}><Text style={s.link}>{t("forgot")}</Text></Pressable>
      {error ? <View style={s.errorBox}><Ionicons name="alert-circle-outline" size={18} color={colors.red}/><Text style={s.error}>{error}</Text></View> : null}
      <Pressable disabled={busy} style={[s.primary,busy&&{opacity:.6}]} onPress={submit}><Text style={s.primaryText}>{busy?t("loggingIn"):t("login")}</Text><Ionicons name="arrow-forward" size={20} color="white"/></Pressable><Pressable onPress={()=>router.push("/register")}><Text style={s.register}>{t("noAccount")} <Text style={s.link}>{t("register")}</Text></Text></Pressable>
    </View></ScrollView></KeyboardAvoidingView></SafeAreaView>;
}

const s=StyleSheet.create({safe:{flex:1,backgroundColor:colors.background},page:{flexGrow:1,justifyContent:"center",padding:22},hero:{alignItems:"center",marginBottom:25},logo:{width:70,height:70,borderRadius:23,backgroundColor:colors.blue,alignItems:"center",justifyContent:"center"},brand:{color:colors.blue,fontWeight:"900",letterSpacing:2,fontSize:13,marginTop:13},title:{fontSize:29,fontWeight:"900",color:colors.navy,marginTop:12},subtitle:{color:colors.muted,textAlign:"center",lineHeight:21,marginTop:7,maxWidth:330},card:{backgroundColor:"white",borderRadius:24,borderWidth:1,borderColor:colors.border,padding:18,gap:14},field:{height:55,borderRadius:15,borderWidth:1,borderColor:colors.border,flexDirection:"row",alignItems:"center",gap:10,paddingHorizontal:15},input:{flex:1,color:colors.navy,fontWeight:"600"},forgot:{alignSelf:"flex-end"},link:{color:colors.blue,fontWeight:"900"},primary:{height:54,borderRadius:15,backgroundColor:colors.blue,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8},primaryText:{color:"white",fontWeight:"900"},register:{textAlign:"center",color:colors.muted,padding:8},errorBox:{flexDirection:"row",gap:8,backgroundColor:"#FFF0F1",padding:11,borderRadius:12},error:{color:colors.red,flex:1}});
