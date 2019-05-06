import Vue from 'vue';
import VueI18n from 'vue-i18n';
import VTooltip from 'v-tooltip';

import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

import App from './App.vue';

const en = require('./i18n/en.json');
const ja = require('./i18n/ja.json');

Vue.config.productionTip = false;

window.eventBus = new Vue();

Vue.use(VueI18n);
const i18n = new VueI18n({
  locale: (navigator.browserLanguage || navigator.language || navigator.userLanguage).substr(0, 2),
  fallbackLocale: 'en',
  messages: {
    en,
    ja
  }
});

const tooltipOptions = {
  defaultHtml: false
};

Vue.use(VTooltip, tooltipOptions);

new Vue({
  i18n,
  render: h => h(App)
}).$mount('#app');
