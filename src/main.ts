import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import router from "./router";
import { useAppStore } from "./core/stores/appStore";
import { createPinia } from "pinia";

createApp(App).use(router).use(createPinia()).mount("#app");

useAppStore(); // Initialize the AppStore
