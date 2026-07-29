import { useEffect } from "react";
import { router, Stack, usePathname } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nProvider } from "../services/i18n";
import { sessionRole } from "../services/api";

const client = new QueryClient({defaultOptions:{queries:{staleTime:30000,retry:1}}});

function RoleGate() {
  const path = usePathname();
  useEffect(() => { if (path === "/") sessionRole().then(role => { if (role === "STAFF") router.replace("/staff"); }); }, [path]);
  return <Stack screenOptions={{headerShown:false,animation:"slide_from_right"}}/>;
}

export default function Layout() {
  return <I18nProvider><QueryClientProvider client={client}><RoleGate/></QueryClientProvider></I18nProvider>;
}
