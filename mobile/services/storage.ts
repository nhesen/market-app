import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const webStorage = {
  async getItemAsync(key: string) {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(key);
  },
  async setItemAsync(key: string, value: string) {
    if (typeof window !== "undefined") window.localStorage.setItem(key, value);
  },
  async deleteItemAsync(key: string) {
    if (typeof window !== "undefined") window.localStorage.removeItem(key);
  },
};

export const storage = Platform.OS === "web" ? webStorage : SecureStore;
