import { createApp } from "vue";
import "@fontsource/plus-jakarta-sans/400.css";
import "@fontsource/plus-jakarta-sans/500.css";
import "@fontsource/plus-jakarta-sans/600.css";
import "@fontsource/plus-jakarta-sans/700.css";
import "./style.css";
import App from "./App.vue";
import router from "./router";
import { useAppStore } from "./core/stores/appStore";
import { createPinia } from "pinia";

createApp(App).use(router).use(createPinia()).mount("#app");

useAppStore(); // Initialize the AppStore
