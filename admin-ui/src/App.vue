<template>
  <div id="app">
    <nav class="navbar navbar-expand navbar-dark bg-dark">
      <img src="./assets/logo-white.svg" class="logo mr-3" />
      <div class="collapse navbar-collapse" id="navbarNavDropdown">
        <ul class="navbar-nav">
          <li class="nav-item" :class="{ active: currentTab === 'audit' }">
            <a class="nav-link" href="#" @click="changeTab('audit')">{{ $t('audit-management') }}</a>
          </li>
          <li class="nav-item" :class="{ active: currentTab === 'vulnerability' }">
            <a class="nav-link" href="#" @click="changeTab('vulnerability')">{{ $t('vulnerability-management') }}</a>
          </li>
        </ul>
      </div>
    </nav>
    <modal-authentication></modal-authentication>
    <audit-management v-if="currentTab === 'audit'" :audit-api-client="auditApiClient"></audit-management>
    <vulnerability-management
      v-else-if="currentTab === 'vulnerability'"
      :vulnerability-api-client="vulnerabilityApiClient"
    ></vulnerability-management>
  </div>
</template>

<script>
import axios from 'axios';
import $ from 'jquery';
import AuditManagement from './components/AuditManagement.vue';
import ModalAuthentication from './components/ModalAuthentication.vue';
import VulnerabilityManagement from './components/VulnerabilityManagement.vue';

export default {
  name: 'app',
  data() {
    return {
      currentTab: 'audit',
      token: window.localStorage.getItem('token'),
      auditApiClient: null,
      vulnerabilityApiClient: null
    };
  },
  components: {
    AuditManagement,
    ModalAuthentication,
    VulnerabilityManagement
  },
  methods: {
    changeTab: function changeTab(tab) {
      this.currentTab = tab;
    },
    forgotToken: function forgotToken() {
      if (window.localStorage.getItem('token').length > 0) {
        window.localStorage.removeItem('token');
        window.location.reload(true);
      }
    }
  },
  created: function created() {
    this.auditApiClient = axios.create({
      baseURL: `${process.env.VUE_APP_API_ENDPOINT}/audit`,
      timeout: process.env.VUE_APP_API_TIMEOUT,
      headers: { Authorization: `Bearer ${this.token}` },
      validateStatus: status => status !== 401
    });
    this.auditApiClient.interceptors.response.use(
      response => response,
      error => {
        this.forgotToken();
        return Promise.reject(error);
      }
    );
    this.vulnerabilityApiClient = axios.create({
      baseURL: `${process.env.VUE_APP_API_ENDPOINT}/vuln`,
      timeout: process.env.VUE_APP_API_TIMEOUT,
      headers: { Authorization: `Bearer ${this.token}` },
      validateStatus: status => status !== 401
    });
    this.vulnerabilityApiClient.interceptors.response.use(
      response => response,
      error => {
        this.forgotToken();
        return Promise.reject(error);
      }
    );
  },
  mounted: function mounted() {
    if (this.token === null) {
      $('#modal-authenticate')
        .modal({ keyboard: false, backdrop: 'static' })
        .modal('show');
    }
  }
};
</script>

<style>
html {
  height: 100%;
}
body {
  height: 100%;
  background-color: #f0f0f0;
}
</style>

<style scoped>
img.logo {
  height: 1rem;
}
</style>
