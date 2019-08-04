<template>
  <div class="col pb-5" v-if="audits.length > 0">
    <div class="card border-danger text-danger">
      <div class="card-body">
        <div class="h5 mb-3">{{ $t('audit.urgent-list') }}</div>
        <table class="table table-sm table-hover mb-0">
          <thead>
            <tr>
              <th scope="col">{{ $t('audit.name') }}</th>
              <th scope="col">{{ $t('audit.description') }}</th>
              <th scope="col">{{ $t('audit.contact') }}</th>
              <th scope="col">{{ $t('audit.updated-at') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(audit, index) in audits" :key="index">
              <td>
                <a :href="`${origin}/#/${audit.uuid.substr(0, 24)}/`" target="_blank">{{ audit.name }}</a>
              </td>
              <td>
                {{ audit.description }}
              </td>
              <td>
                <a :href="generateMailURL(audit)">
                  <span v-for="(contact, index) in audit.contacts" :key="index">{{ contact.name }}<br /></span>
                </a>
              </td>
              <td>{{ displayDateTime(audit.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue';
import moment from 'moment';

export default {
  name: 'AuditUrgentList',
  props: {
    auditApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      audits: [],
      errorMessage: '',
      origin: process.env.VUE_APP_USER_ORIGIN,
      utcOffset: 0
    };
  },
  methods: {
    generateMailURL: function generateMailURL(audit) {
      let url = 'mailto:';
      audit.contacts.forEach(contact => {
        url = `${url}${contact.email};`;
      });
      return url;
    },
    displayDateTime: function displayDateTime(datetime) {
      if (datetime.length === 0) {
        return '';
      }
      const m = moment(datetime, 'YYYY-MM-DD hh:mm:ss').add(this.utcOffset, 'minutes');
      return m.format(this.$i18n.t('audit.datetime-format'));
    },

    loadAuditIndex: async function loadAuditIndex() {
      try {
        const res = await this.auditApiClient.get('?unsafe_only=true');
        switch (res.status) {
          case 200:
          case 304:
            this.audits = res.data;
            break;
          default:
            this.errorMessage = this.$i18n.t('audit.error-loading');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-loading');
      }
    }
  },
  mounted: function mounted() {
    this.loadAuditIndex();
    moment.locale(this.$i18n.locale);
    this.utcOffset = moment().utcOffset();
  }
};
</script>
