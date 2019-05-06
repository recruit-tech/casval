<template>
  <div id="app" class="h-100">
    <entrance :status="status" v-if="status !== 'loaded'"></entrance>
    <home :audit="audit" :audit-api-client="auditApiClient" :scan-api-client="scanApiClient" v-else></home>
  </div>
</template>

<script>
import axios from 'axios';
import Entrance from './components/Entrance.vue';
import Home from './components/Home.vue';

export default {
  name: 'app',
  data() {
    return {
      audit: null,
      auditUUID: '',
      status: 'loading',
      token: null
    };
  },
  components: {
    Entrance,
    Home
  },
  computed: {
    auditApiClient: function createAuditApiClient() {
      return axios.create({
        baseURL: `${process.env.VUE_APP_API_ENDPOINT}/audit/${this.auditUUID}`,
        timeout: process.env.VUE_APP_API_TIMEOUT,
        headers: { Authorization: `Bearer ${this.token}` },
        validateStatus: () => true
      });
    },
    scanApiClient: function createScanApiClient() {
      return axios.create({
        baseURL: `${process.env.VUE_APP_API_ENDPOINT}/scan`,
        timeout: process.env.API_REQUEST_TIMEOUT,
        headers: { Authorization: `Bearer ${this.token}` },
        validateStatus: () => true
      });
    }
  },
  methods: {
    generateToken: async function generateToken(password) {
      this.status = 'loading';
      try {
        const res = await this.auditApiClient.post('/tokens/', { password });
        switch (res.status) {
          case 200:
            this.token = res.data.token;
            this.getAudit();
            break;
          case 401:
            this.status = 'restricted-by-password';
            break;
          case 403:
            this.status = 'restricted-by-ip';
            break;
          case 404:
            this.status = 'audit-not-found';
            break;
          default:
            this.status = 'unknown-error';
        }
      } catch (e) {
        this.status = 'unknown-error';
      }
    },
    getAudit: async function getAudit() {
      try {
        const res = await this.auditApiClient.get('/');
        switch (res.status) {
          case 200:
          case 304:
            this.audit = res.data;
            this.status = 'loaded';
            window.document.title = `${process.env.VUE_APP_TITLE} - ${this.audit.name}`;
            break;
          case 401:
            this.status = 'invalid-token';
            break;
          case 404:
            this.status = 'audit-not-found';
            break;
          default:
            this.status = 'unknown-error';
        }
      } catch (e) {
        this.status = 'unknown-error';
      }
    }
  },
  created: function created() {
    this.auditUUID = window.location.hash.substring(2).replace('/', '') || '';
    this.auditUUID += '00000000';

    window.eventBus.$on('TOKEN_REQUESTED', password => {
      this.generateToken(password);
    });
    window.eventBus.$on('RELOAD_REQUESTED', () => {
      this.getAudit();
    });
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
