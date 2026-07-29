import {useEffect,useState} from "react";
import {Ionicons} from "@expo/vector-icons";
import {router,useLocalSearchParams} from "expo-router";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {Pressable,ScrollView,StyleSheet,Text,TextInput,View} from "react-native";
import {clearRecentSearches,customerApi,recentSearches,rememberSearch,selectedBranchId} from "../services/api";
import {Card,Chip,PageTitle,RemoteImage,Screen,State} from "../components/ui";
import {colors} from "../constants/theme";
import {useI18n} from "../services/i18n";

function useDebounced(value:string,delay=450){const[result,setResult]=useState(value);useEffect(()=>{const timer=setTimeout(()=>setResult(value.trim()),delay);return()=>clearTimeout(timer)},[value,delay]);return result}

export default function Products(){
  const params=useLocalSearchParams<{q?:string}>(),{t}=useI18n(),client=useQueryClient();
  const[input,setInput]=useState(params.q??""),query=useDebounced(input),[category,setCategory]=useState(""),[sort,setSort]=useState("name"),[saved,setSaved]=useState(false),[recent,setRecent]=useState<string[]>([]);
  useEffect(()=>{recentSearches().then(setRecent)},[]);
  const branch=useQuery({queryKey:["selected-branch"],queryFn:selectedBranchId});
  const products=useQuery({queryKey:["products",query,category,sort,branch.data],queryFn:()=>customerApi.products({q:query,category,sort,branchId:branch.data??undefined}),enabled:branch.isFetched});
  const categories=useQuery({queryKey:["categories"],queryFn:customerApi.categories});
  const favs=useQuery({queryKey:["favourites"],queryFn:customerApi.favourites});
  const ids=new Set(favs.data?.map(x=>x.id));
  const toggle=useMutation({mutationFn:(id:string)=>ids.has(id)?customerApi.unfavourite(id):customerApi.favourite(id),onSuccess:()=>client.invalidateQueries({queryKey:["favourites"]})});
  const rows=saved?favs.data:products.data;
  async function commit(value=input){await rememberSearch(value);setRecent(await recentSearches())}
  async function clear(){await clearRecentSearches();setRecent([])}
  return <Screen refreshing={products.isRefetching} onRefresh={()=>products.refetch()}>
    <PageTitle title={t("productsTitle")} subtitle={t("productsSubtitle")} action={<Pressable style={s.scan} onPress={()=>router.push("/scanner")}><Ionicons name="barcode-outline" size={25} color={colors.blue}/></Pressable>}/>
    <View style={s.search}><Ionicons name="search" size={20} color={colors.muted}/><TextInput style={{flex:1}} placeholder={t("productSearch")} value={input} onChangeText={setInput} returnKeyType="search" onSubmitEditing={()=>commit()}/>{input?<Pressable onPress={()=>setInput("")}><Ionicons name="close-circle" size={20} color={colors.muted}/></Pressable>:null}</View>
    {!input&&recent.length?<View style={s.searchPanel}><View style={s.panelTitle}><Text style={s.filterTitle}>{t("recentSearches")}</Text><Pressable onPress={clear}><Text style={s.clear}>{t("clear")}</Text></Pressable></View><View style={s.wrap}>{recent.map(x=><Chip key={x} label={x} onPress={()=>{setInput(x);commit(x)}}/>)}</View></View>:null}
    {!input&&categories.data?.length?<View><Text style={s.filterTitle}>{t("suggestedSearches")}</Text><View style={s.wrap}>{categories.data.slice(0,6).map(x=><Chip key={x} label={x} onPress={()=>{setInput(x);commit(x)}}/>)}</View></View>:null}
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}><Chip label={t("all")} active={!category&&!saved} onPress={()=>{setCategory("");setSaved(false)}}/>{categories.data?.map(x=><Chip key={x} label={x} active={category===x&&!saved} onPress={()=>{setCategory(x);setSaved(false)}}/>)}<Chip label={t("savedOnly")} active={saved} onPress={()=>setSaved(true)}/></ScrollView>
    <Text style={s.filterTitle}>{t("sort")}</Text><ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}>{[["name",t("sortName")],["price_asc",t("sortPriceAsc")],["price_desc",t("sortPriceDesc")],["discount",t("sortDiscount")]].map(([key,label])=><Chip key={key} label={label} active={sort===key} onPress={()=>setSort(key)}/>)}</ScrollView>
    <State loading={products.isLoading||favs.isLoading} error={products.isError||favs.isError} retry={()=>products.refetch()} empty={!rows?.length?t("productsEmpty"):undefined}/>
    {rows?.map(p=><Card key={p.id} onPress={()=>{commit(p.name);router.push({pathname:"/product-detail" as never,params:{id:p.id}})}}><View style={s.row}><RemoteImage url={p.image_url} height={92}/><View style={s.info}><Text style={s.name}>{p.name}</Text><Text style={s.meta}>{p.brand} · {p.category}</Text><Text style={s.availability}>{p.available===false?t("outOfStock"):t("inStock")}</Text><View style={s.prices}>{p.discount_price?<Text style={s.old}>{p.price.toFixed(2)} {t("currency")}</Text>:null}<Text style={s.price}>{(p.discount_price??p.price).toFixed(2)} {t("currency")}</Text></View></View><Pressable hitSlop={12} onPress={event=>{event.stopPropagation();toggle.mutate(p.id)}}><Ionicons name={ids.has(p.id)?"heart":"heart-outline"} size={27} color={colors.red}/></Pressable></View></Card>)}
  </Screen>
}
const s=StyleSheet.create({scan:{width:46,height:46,borderRadius:15,backgroundColor:colors.softBlue,alignItems:"center",justifyContent:"center"},search:{height:54,backgroundColor:"white",borderWidth:1,borderColor:colors.border,borderRadius:15,paddingHorizontal:14,flexDirection:"row",alignItems:"center",gap:9},searchPanel:{backgroundColor:"white",borderRadius:15,padding:13,borderWidth:1,borderColor:colors.border,gap:9},panelTitle:{flexDirection:"row",justifyContent:"space-between"},clear:{color:colors.blue,fontWeight:"800"},wrap:{flexDirection:"row",flexWrap:"wrap",gap:8},chips:{gap:8,paddingRight:10},filterTitle:{fontWeight:"800",color:colors.navy},row:{flexDirection:"row",gap:12,alignItems:"flex-start"},info:{flex:1},name:{fontWeight:"900",fontSize:16,color:colors.navy},meta:{color:colors.muted,fontSize:12,marginTop:3},availability:{color:colors.green,fontSize:12,fontWeight:"700",marginTop:5},prices:{flexDirection:"row",alignItems:"center",gap:7,marginTop:6},price:{color:colors.blue,fontWeight:"900",fontSize:18},old:{color:colors.muted,textDecorationLine:"line-through",fontSize:12}});
