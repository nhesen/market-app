import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { staffApi } from "../services/api";
import { Card, PageTitle, Screen, State, Status } from "../components/ui";
import { colors } from "../constants/theme";

const auditConditions=["NORMAL","EXPIRING_SOON","EXPIRED","DAMAGED","UNREADABLE","OTHER"];
export default function Staff(){
  const [filter,setFilter]=useState("ALL");const client=useQueryClient();
  const tasks=useQuery({queryKey:["audits"],queryFn:staffApi.audits});
  const quality=useQuery({queryKey:["staff-quality"],queryFn:staffApi.quality});
  const reAuditQuery=useQuery({queryKey:["re-audits"],queryFn:staffApi.reAudits});
  const completeReAudit=useMutation({mutationFn:({id,condition}:{id:string;condition:string})=>staffApi.completeReAudit(id,condition),onSuccess:()=>client.invalidateQueries({queryKey:["re-audits"]})});
  const rows=(tasks.data??[]).filter(item=>filter==="ALL"||item.status===filter),reAudits=reAuditQuery.data??[];
  return <Screen><PageTitle title="Audit iş paneli" subtitle="Bugünkü tapşırıqlar, təkrar audit və keyfiyyət göstəriciləri"/>
    <View style={s.stats}><Metric value={(tasks.data??[]).filter(x=>x.status==="ASSIGNED").length} label="Təyin edilib"/><Metric value={(tasks.data??[]).filter(x=>new Date(x.due_at)<new Date()&&x.status!=="COMPLETED").length} label="Gecikib"/><Metric value={(tasks.data??[]).filter(x=>x.status==="COMPLETED").length} label="Tamamlanıb"/><Metric value={`${quality.data?.score??0}/100`} label="Keyfiyyət"/></View>
    <Card><Text style={s.section}>Keyfiyyət xülasəsi</Text><Text>Tamamlanma: {quality.data?.completion_rate??0}% · Orta müddət: {quality.data?.average_duration_minutes??0} dəq.</Text><Text style={s.explain}>{quality.data?.explanation}</Text>{quality.data?.quality_flags?.map((flag:any)=><View key={flag.id} style={s.flag}><Text style={s.flagTitle}>{flag.code}</Text><Text style={s.explain}>{flag.message}</Text></View>)}</Card>
    {reAudits.length>0&&<><Text style={s.section}>Təkrar auditlər</Text>{reAudits.map((item:any)=><Card key={item.id}><Status value={item.status}/><Text>İlkin nəticə: {item.original_condition}</Text>{item.status==="ASSIGNED"&&<View style={s.conditions}>{auditConditions.map(condition=><Pressable key={condition} onPress={()=>completeReAudit.mutate({id:item.id,condition})}><Text style={s.condition}>{condition}</Text></Pressable>)}</View>}{item.status==="COMPLETED"&&<Text style={item.consistent?s.ok:s.bad}>{item.consistent?"Nəticə uyğundur":"Uyğunsuzluq keyfiyyət yoxlamasına göndərildi"}</Text>}</Card>)}</>}
    <Text style={s.section}>Audit tapşırıqları</Text><View style={s.filters}>{["ALL","ASSIGNED","IN_PROGRESS","COMPLETED"].map(value=><Pressable key={value} onPress={()=>setFilter(value)} style={[s.filter,filter===value&&s.active]}><Text style={filter===value&&s.activeText}>{value}</Text></Pressable>)}</View><State loading={tasks.isLoading} error={tasks.isError} empty={!rows.length?"Bu bölmədə audit tapşırığı yoxdur.":undefined}/>{rows.map(task=><Pressable key={task.id} onPress={()=>router.push({pathname:"/audit",params:{id:task.id}})}><Card><View style={s.row}><Status value={task.status}/><Text style={s.priority}>{task.priority}</Text></View><Text style={s.title}>{task.title}</Text><Text style={s.explain}>{task.item_count}/{task.required_count} məhsul · Son vaxt {new Date(task.due_at).toLocaleString("az-AZ")}</Text></Card></Pressable>)}
  </Screen>;
}
function Metric({value,label}:{value:string|number;label:string}){return <View style={s.metric}><Text style={s.num}>{value}</Text><Text style={s.metricLabel}>{label}</Text></View>}
const s=StyleSheet.create({stats:{flexDirection:"row",flexWrap:"wrap",gap:9},metric:{width:"48%",padding:15,borderRadius:16,backgroundColor:"white",borderWidth:1,borderColor:colors.border},num:{fontSize:24,fontWeight:"900",color:colors.blue},metricLabel:{color:colors.muted,fontSize:12},section:{fontSize:18,fontWeight:"900",color:colors.navy},explain:{color:colors.muted,lineHeight:19},flag:{padding:10,borderRadius:10,backgroundColor:colors.softAmber},flagTitle:{fontWeight:"900",color:"#996000"},conditions:{flexDirection:"row",flexWrap:"wrap",gap:6},condition:{fontSize:11,padding:7,borderRadius:8,backgroundColor:colors.softBlue,color:colors.blue,fontWeight:"800"},ok:{color:colors.green,fontWeight:"800"},bad:{color:colors.red,fontWeight:"800"},filters:{flexDirection:"row",flexWrap:"wrap",gap:6},filter:{padding:9,borderRadius:9,backgroundColor:"white",borderWidth:1,borderColor:colors.border},active:{backgroundColor:colors.softBlue,borderColor:colors.blue},activeText:{color:colors.blue,fontWeight:"800"},row:{flexDirection:"row",justifyContent:"space-between"},priority:{fontWeight:"900",color:colors.red},title:{fontSize:17,fontWeight:"900"}});
