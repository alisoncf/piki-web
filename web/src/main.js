import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Dialog, Notify, Quasar } from 'quasar'
import quasarLang from 'quasar/lang/pt-BR'
import '@fontsource-variable/inter'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'

import App from './App.vue'
import { criarRoteador } from './router'
import './css/app.css'

const app = createApp(App)
app.use(createPinia())
app.use(criarRoteador())
app.use(Quasar, { plugins: { Notify, Dialog }, lang: quasarLang })
app.mount('#app')
