import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { customerApi } from "../services/api";
import { Button, Card, PageTitle, Screen, State } from "../components/ui";
import { colors } from "../constants/theme";

export default function Products(){
  const [q,setQ]=useState(""),[tab,setTab]=useState<"products"|"discounts"|"favourites">("products");
  const client=useQueryClient();
  const products=useQuery({queryKey:["products",q],queryFn:()=>customerApi.products(q)});
  const favs=useQuery({queryKey:["favourites"],queryFn:customerApi.favourites});
  const favIds=new Set(favs.data?.map(item=>item.id));
  const toggle=useMutation({mutationFn:(product:any)=>favIds.has(product.id)?customerApi.unfavourite(product.id):customerApi.favourite(product.id),onSuccess:()=>client.invalidateQueries({queryKey:["favourites"]})});
  const rows=tab==="favourites"?favs.data:products.data?.filter(item=>tab==="products"||item.discount_price);
  return <Screen><PageTitle title="Qiymətlər" subtitle="Nova Market məhsulları və filial qiymətləri"/><TextInput style={s.input} placeholder="Məhsul, brend və ya barkod" value={q} onChangeText={setQ}/><View style={s.tabs}>{[["products","Məhsullar"],["discounts","Endirimlər"],["favourites","Seçilmişlər"]].map(item=><Pressable key={item[0]} style={[s.tab,tab===item[0]&&s.active]} onPress={()=>setTab(item[0] as typeof tab)}><Text style={tab===item[0]&&s.activeText}>{item[1]}</Text></Pressable>)}</View><State loading={products.isLoading} error={products.isError} empty={!rows?.length?"Məhsul tapılmadı.":undefined}/>{rows?.map(product=><Card key={product.id}><View style={s.row}><View style={{flex:1}}><Text style={s.name}>{product.name}</Text><Text style={s.meta}>{product.brand} · {product.category}</Text><Text style={s.price}>{(product.discount_price??product.price).toFixed(2)} ₼ {product.discount_price&&<Text style={s.old}>{product.price.toFixed(2)} ₼</Text>}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={favIds.has(product.id)?"Seçilmişlərdən sil":"Seçilmişlərə əlavə et"} onPress={()=>toggle.mutate(product)}><Text style={s.heart}>{favIds.has(product.id)?"♥":"♡"}</Text></Pressable></View><Button secondary title="Qiymət uyğunsuzluğu bildir" onPress={()=>router.push({pathname:"/report",params:{category:"PRICE",title:`${product.name} qiymət uyğunsuzluğu`,description:`${product.name} məhsulunun rəf və ya kassa qiyməti tətbiqdə göstərilən qiymətlə uyğun deyil.`,barcode:product.barcode}})}/></Card>)}</Screen>;
}
const s=StyleSheet.create({input:{backgroundColor:"white",borderWidth:1,borderColor:colors.border,borderRadius:13,padding:14},tabs:{flexDirection:"row",backgroundColor:"white",borderRadius:13,padding:4},tab:{flex:1,padding:10,alignItems:"center",borderRadius:10},active:{backgroundColor:colors.softBlue},activeText:{color:colors.blue,fontWeight:"800"},row:{flexDirection:"row"},name:{fontWeight:"900",fontSize:17},meta:{color:colors.muted,marginTop:4},price:{color:colors.blue,fontWeight:"900",fontSize:19,marginTop:10},old:{color:colors.muted,textDecorationLine:"line-through",fontSize:13},heart:{fontSize:30,color:colors.red}});
