import { Pressable, StyleSheet, Text } from "react-native";
import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { Card, PageTitle, Screen, State, Status } from "../components/ui";
import { colors } from "../constants/theme";
export default function Reports(){const query=useQuery({queryKey:["reports"],queryFn:api.reports});return <Screen><PageTitle title="Problemlərim" subtitle="Bildirdiyiniz problemlərin statusunu və izləmə nömrəsini burada görün"/><State loading={query.isLoading} error={query.isError} empty={!query.data?.length?"Hələ problem bildirməmisiniz.":undefined}/>{query.data?.map(report=><Pressable key={report.id} onPress={()=>router.push({pathname:"/report-detail",params:{id:report.id}})}><Card><Status value={report.status}/><Text style={s.title}>{report.title}</Text><Text style={s.track}>{report.tracking_number}</Text><Text numberOfLines={2} style={s.description}>{report.description}</Text><Text style={s.date}>{new Date(report.created_at).toLocaleString("az-AZ")}</Text></Card></Pressable>)}</Screen>}
const s=StyleSheet.create({title:{fontSize:17,fontWeight:"900",color:colors.navy},track:{color:colors.blue,fontWeight:"800"},description:{color:colors.muted},date:{fontSize:12,color:colors.muted}});
