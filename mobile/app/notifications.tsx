import { Pressable, StyleSheet, Text, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { customerApi } from "../services/api";
import { Button, Card, PageTitle, Screen, State } from "../components/ui";
import { colors } from "../constants/theme";

export default function Notifications(){
  const client=useQueryClient();
  const query=useQuery({queryKey:["notifications"],queryFn:customerApi.notifications});
  const refresh=()=>client.invalidateQueries({queryKey:["notifications"]});
  const read=useMutation({mutationFn:customerApi.readNotification,onSuccess:refresh});
  const readAll=useMutation({mutationFn:customerApi.readAllNotifications,onSuccess:refresh});
  const unread=query.data?.filter(item=>!item.is_read).length??0;
  return <Screen><PageTitle title="Bildirişlər" subtitle={`${unread} oxunmamış bildiriş`}/>{unread>0&&<Button secondary disabled={readAll.isPending} title={readAll.isPending?"Yenilənir…":"Hamısını oxunmuş et"} onPress={()=>readAll.mutate()}/>}<State loading={query.isLoading} error={query.isError} empty={!query.data?.length?"Yeni bildiriş yoxdur.":undefined}/>{query.data?.map(item=><Pressable accessibilityRole="button" accessibilityLabel={`${item.title}. ${item.is_read?"Oxunub":"Oxunmayıb"}`} key={item.id} onPress={()=>!item.is_read&&read.mutate(item.id)}><Card><View style={s.row}><Text style={s.title}>{item.title}</Text>{!item.is_read&&<View style={s.dot}/>}</View><Text style={s.body}>{item.body}</Text><Text style={s.date}>{new Date(item.created_at).toLocaleString("az-AZ")}</Text></Card></Pressable>)}</Screen>;
}
const s=StyleSheet.create({row:{flexDirection:"row",justifyContent:"space-between"},title:{fontWeight:"900"},dot:{width:9,height:9,borderRadius:5,backgroundColor:colors.blue},body:{color:colors.muted},date:{fontSize:11,color:colors.muted}});
