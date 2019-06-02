import Vue from 'vue';
import VueI18n from 'vue-i18n';

import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

import { library, dom } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { faArrowLeft } from '@fortawesome/free-solid-svg-icons/faArrowLeft';
import { faBars } from '@fortawesome/free-solid-svg-icons/faBars';
import { faCalendar } from '@fortawesome/free-solid-svg-icons/faCalendar';
import { faCalendarTimes } from '@fortawesome/free-solid-svg-icons/faCalendarTimes';
import { faCheckCircle } from '@fortawesome/free-solid-svg-icons/faCheckCircle';
import { faChevronCircleRight } from '@fortawesome/free-solid-svg-icons/faChevronCircleRight';
import { faClock } from '@fortawesome/free-solid-svg-icons/faClock';
import { faDownload } from '@fortawesome/free-solid-svg-icons/faDownload';
import { faExclamationCircle } from '@fortawesome/free-solid-svg-icons/faExclamationCircle';
import { faPencilAlt } from '@fortawesome/free-solid-svg-icons/faPencilAlt';
import { faSpinner } from '@fortawesome/free-solid-svg-icons/faSpinner';
import { faFileUpload } from '@fortawesome/free-solid-svg-icons/faFileUpload';

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
library.add(
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
  faSpinner,
  faFileUpload
);

dom.watch();

window.eventBus = new Vue();

new Vue({
  i18n,
  render: h => h(App)
}).$mount('#app');
