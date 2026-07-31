import { useEffect, useState } from "react";
import { router, Stack, usePathname } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as SecureStore from "expo-secure-store";
import { I18nProvider } from "../services/i18n";
import { restoreSession } from "../services/api";

const client = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000, retry: 1 } },
});

function RoleGate() {
  const path = usePathname();
  const [ready, setReady] = useState(path !== "/");
  useEffect(() => {
    if (path !== "/") {
      setReady(true);
      return;
    }
    let active = true;
    (async () => {
      const seen = await SecureStore.getItemAsync("onboarding_seen");
      if (!seen) {
        if (active) setReady(true);
        return;
      }
      const user = await restoreSession();
      if (!active) return;
      if (!user) {
        router.replace("/login");
        return;
      }
      if (user.role === "STAFF") {
        router.replace("/staff");
        return;
      }
      if (user.role === "BRANCH_ADMIN") {
        router.replace("/branch-admin" as never);
        return;
      }
      if (user.role === "HEAD_OFFICE_ADMIN") {
        router.replace("/head-admin" as never);
        return;
      }
      if (user.role === "PLATFORM_ADMIN") {
        router.replace("/platform-admin" as never);
        return;
      }
      setReady(true);
    })().catch(() => {
      if (active) router.replace("/login");
    });
    return () => {
      active = false;
    };
  }, [path]);
  if (!ready) return null;
  return (
    <Stack
      screenOptions={{ headerShown: false, animation: "slide_from_right" }}
    />
  );
}

export default function Layout() {
  return (
    <I18nProvider>
      <QueryClientProvider client={client}>
        <RoleGate />
      </QueryClientProvider>
    </I18nProvider>
  );
}
