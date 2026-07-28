import { Ionicons } from "@expo/vector-icons";
import { router, usePathname } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors } from "../constants/theme";

const items=[
  {label:"Əsas",icon:"home-outline" as const,path:"/"},
  {label:"Qiymətlər",icon:"pricetags-outline" as const,path:"/products"},
  {label:"Kartlar",icon:"card-outline" as const,path:"/cards"},
  {label:"Profil",icon:"person-outline" as const,path:"/profile"},
];

export function BottomNav(){
  const inset=useSafeAreaInsets();const pathname=usePathname();
  return <View style={[s.shell,{height:72+inset.bottom,paddingBottom:Math.max(inset.bottom,8)}]}>
    <Nav item={items[0]} active={pathname==="/"}/><Nav item={items[1]} active={pathname.startsWith("/products")}/>
    <View style={s.centerSlot}><Pressable accessibilityRole="button" accessibilityLabel="Problem bildir" onPress={()=>router.push("/report")} style={({pressed})=>[s.centerButton,pressed&&{transform:[{scale:.96}]}]}><Ionicons name="add" size={32} color="white"/></Pressable><Text style={s.centerLabel}>Bildir</Text></View>
    <Nav item={items[2]} active={pathname.startsWith("/cards")}/><Nav item={items[3]} active={pathname.startsWith("/profile")}/>
  </View>;
}
function Nav({item,active}:{item:(typeof items)[number];active:boolean}){return <Pressable style={s.item} onPress={()=>router.push(item.path as any)}><Ionicons name={active?item.icon.replace("-outline","") as any:item.icon} size={22} color={active?colors.blue:colors.muted}/><Text numberOfLines={1} adjustsFontSizeToFit style={[s.label,active&&s.active]}>{item.label}</Text></Pressable>}
const s=StyleSheet.create({shell:{position:"absolute",left:0,right:0,bottom:0,backgroundColor:"#F6F8FC",borderTopWidth:0,flexDirection:"row",alignItems:"flex-start",paddingTop:8,paddingHorizontal:4,shadowColor:"#0B1220",shadowOffset:{width:0,height:-5},shadowOpacity:.06,shadowRadius:12,elevation:12},item:{flex:1,minWidth:0,alignItems:"center",justifyContent:"center",gap:3,height:52,paddingHorizontal:2},label:{fontSize:10.5,lineHeight:13,fontWeight:"700",color:colors.muted,textAlign:"center",maxWidth:"100%"},active:{color:colors.blue,fontWeight:"900"},centerSlot:{flex:1,minWidth:0,alignItems:"center",top:-29},centerButton:{height:62,width:62,borderRadius:31,alignItems:"center",justifyContent:"center",backgroundColor:colors.blue,borderWidth:5,borderColor:"#F6F8FC",shadowColor:colors.blue,shadowOffset:{width:0,height:8},shadowOpacity:.23,shadowRadius:13,elevation:9},centerLabel:{fontSize:10.5,fontWeight:"900",color:colors.blue,marginTop:1}});
