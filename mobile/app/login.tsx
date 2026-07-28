import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { login } from "../services/api";
import { colors } from "../constants/theme";

function Field({ icon, ...props }: { icon: keyof typeof Ionicons.glyphMap } & React.ComponentProps<typeof TextInput>) {
  return <View style={s.field}><Ionicons name={icon} size={20} color={colors.muted}/><TextInput placeholderTextColor={colors.muted} style={s.input} {...props}/></View>;
}

export default function Login() {
  const [email,setEmail]=useState("customer@demo.az");
  const [password,setPassword]=useState("Demo123!");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  return <SafeAreaView style={s.safe}><KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS==="ios"?"padding":undefined}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.page}>
      <View style={s.hero}>
        <View style={s.logo}><Text style={s.logoMark}>M</Text></View>
        <Text style={s.brand}>MARTIQ</Text>
        <Text style={s.title}>Xoş gəlmisiniz</Text>
        <Text style={s.subtitle}>Market məlumatları, məhsul yoxlaması və müraciətləriniz bir tətbiqdə.</Text>
      </View>
      <View style={s.card}>
        <Field icon="mail-outline" autoCapitalize="none" keyboardType="email-address" placeholder="E-poçt ünvanı" value={email} onChangeText={setEmail}/>
        <Field icon="lock-closed-outline" secureTextEntry placeholder="Şifrə" value={password} onChangeText={setPassword}/>
        <Pressable style={s.forgot}><Text style={s.forgotText}>Şifrəni unutmusunuz?</Text></Pressable>
        {error?<View style={s.errorBox}><Ionicons name="alert-circle-outline" size={18} color={colors.red}/><Text style={s.error}>{error}</Text></View>:null}
        <Pressable disabled={busy} style={({pressed})=>[s.primary,(pressed||busy)&&{opacity:.75}]} onPress={async()=>{setError("");setBusy(true);try{const user=await login(email.trim(),password);router.replace(user.role==="STAFF"?"/staff":"/")}catch(e:any){setError(e.message||"Giriş alınmadı")}finally{setBusy(false)}}}>
          <Text style={s.primaryText}>{busy?"Daxil olunur…":"Daxil ol"}</Text><Ionicons name="arrow-forward" size={20} color="white"/>
        </Pressable>
        <Pressable style={s.register} onPress={()=>router.push("/register")}><Text style={s.registerText}>Hesabınız yoxdur? <Text style={s.registerLink}>Qeydiyyatdan keçin</Text></Text></Pressable>
      </View>
      <View style={s.demo}><Ionicons name="information-circle-outline" size={18} color={colors.blue}/><Text style={s.demoText}>Demo hesab məlumatları əvvəlcədən daxil edilib.</Text></View>
    </ScrollView>
  </KeyboardAvoidingView></SafeAreaView>;
}

const shadow={shadowColor:"#0B1220",shadowOffset:{width:0,height:10},shadowOpacity:.08,shadowRadius:18,elevation:4};
const s=StyleSheet.create({safe:{flex:1,backgroundColor:"#F6F8FC"},page:{flexGrow:1,justifyContent:"center",padding:22,paddingBottom:40},hero:{alignItems:"center",marginBottom:26},logo:{width:68,height:68,borderRadius:22,backgroundColor:colors.blue,alignItems:"center",justifyContent:"center",shadowColor:colors.blue,shadowOffset:{width:0,height:10},shadowOpacity:.25,shadowRadius:16,elevation:6},logoMark:{color:"white",fontWeight:"900",fontSize:34},brand:{color:colors.blue,fontWeight:"900",letterSpacing:2,fontSize:14,marginTop:14},title:{fontSize:28,fontWeight:"900",color:colors.navy,marginTop:14},subtitle:{fontSize:14,color:colors.muted,textAlign:"center",lineHeight:21,maxWidth:330,marginTop:8},card:{backgroundColor:"white",borderRadius:22,borderWidth:1,borderColor:colors.border,padding:18,gap:14,...shadow},field:{height:54,borderRadius:16,borderWidth:1,borderColor:colors.border,backgroundColor:"white",flexDirection:"row",alignItems:"center",gap:10,paddingHorizontal:15},input:{flex:1,fontSize:15,color:colors.navy,fontWeight:"600"},forgot:{alignSelf:"flex-end",paddingVertical:2},forgotText:{color:colors.blue,fontSize:13,fontWeight:"800"},primary:{height:54,borderRadius:16,backgroundColor:colors.blue,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8,shadowColor:colors.blue,shadowOffset:{width:0,height:9},shadowOpacity:.22,shadowRadius:14,elevation:5},primaryText:{color:"white",fontSize:15,fontWeight:"900"},register:{paddingVertical:8},registerText:{textAlign:"center",fontSize:13,color:colors.muted,fontWeight:"600"},registerLink:{color:colors.blue,fontWeight:"900"},errorBox:{flexDirection:"row",gap:8,alignItems:"center",backgroundColor:"#FFF0F1",borderRadius:12,padding:11},error:{color:colors.red,fontSize:13,fontWeight:"700",flex:1},demo:{flexDirection:"row",alignItems:"center",justifyContent:"center",gap:7,marginTop:18},demoText:{fontSize:12,color:colors.muted,fontWeight:"600"}});
