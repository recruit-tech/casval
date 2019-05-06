import Vue from 'vue';
import VueI18n from 'vue-i18n';

import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import fontawesome from '@fortawesome/fontawesome';
import faArrowLeft from '@fortawesome/fontawesome-free-solid/faArrowLeft';
import faBars from '@fortawesome/fontawesome-free-solid/faBars';
import faCalendar from '@fortawesome/fontawesome-free-solid/faCalendar';
import faCalendarTimes from '@fortawesome/fontawesome-free-solid/faCalendarTimes';
import faCheckCircle from '@fortawesome/fontawesome-free-solid/faCheckCircle';
import faChevronCircleRight from '@fortawesome/fontawesome-free-solid/faChevronCircleRight';
import faClock from '@fortawesome/fontawesome-free-solid/faClock';
import faDownload from '@fortawesome/fontawesome-free-solid/faDownload';
import faExclamationCircle from '@fortawesome/fontawesome-free-solid/faExclamationCircle';
import faPencilAlt from '@fortawesome/fontawesome-free-solid/faPencilAlt';
import faSpinner from '@fortawesome/fontawesome-free-solid/faSpinner';

import App from './App.vue';

const en = require('./i18n/en.json');
const ja = require('./i18n/ja.json');

Vue.use(VueI18n);
const i18n = new VueI18n({
  locale: (navigator.browserLanguage || navigator.language || navigator.userLanguage).substr(0, 2),
  fallbackLocale: 'en',
  messages: {
    en,
    ja
  }
});

Vue.config.productionTip = false;

Vue.component('font-awesome-icon', FontAwesomeIcon);
fontawesome.library.add(
  faArrowLeft,
  faBars,
  faCalendar,
  faCalendarTimes,
  faCheckCircle,
  faChevronCircleRight,
  faClock,
  faDownload,
  faExclamationCircle,
  faPencilAlt,
  faSpinner
);

window.eventBus = new Vue();

new Vue({
  i18n,
  render: h => h(App)
}).$mount('#app');
