import {createContext,useContext,useEffect,useMemo,useState} from "react";
import * as SecureStore from "expo-secure-store";
import az from "../locales/az";
import en from "../locales/en";
type Language="az"|"en";type Key=keyof typeof az;
const Context=createContext({language:"az" as Language,setLanguage:async(_value:Language)=>{},t:(key:Key)=>az[key] as string});
export function I18nProvider({children}:{children:React.ReactNode}){const[language,setValue]=useState<Language>("az");useEffect(()=>{SecureStore.getItemAsync("language").then(value=>{if(value==="az"||value==="en")setValue(value)})},[]);const value=useMemo(()=>({language,setLanguage:async(next:Language)=>{setValue(next);await SecureStore.setItemAsync("language",next)},t:(key:Key)=>(language==="az"?az[key]:en[key]) as string}),[language]);return <Context.Provider value={value}>{children}</Context.Provider>}
export const useI18n=()=>useContext(Context);
