import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/index.css'
import './style.css'

createApp(App).use(createPinia()).use(router).use(ElementPlus).mount('#app')
