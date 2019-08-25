<template>
  <div class="col pb-5">
    <div class="card">
      <div class="card-body">
        <div class="h5 mb-3">{{ $t('audit.list') }}</div>
        <hr />
        <div class="d-flex flex-row my-4">
          <div class="pl-2 pr-2">
            <input
              type="text"
              class="form-control form-control-sm"
              v-model="keyword"
              :placeholder="$t('audit.search')"
              @blur="loadAuditIndex(1)"
              @keyup.enter="loadAuditIndex(1)"
            />
          </div>
          <div class="pr-2">
            <select class="form-control form-control-sm" v-model="status" @change="loadAuditIndex(1)">
              <option value="">{{ $t('audit.choose-status') }}</option>
              <option value="ONGOING">{{ $t('audit.status-ongoing') }}</option>
              <option value="SUBMITTED">{{ $t('audit.status-submitted') }}</option>
              <option value="APPROVED">{{ $t('audit.status-approved') }}</option>
            </select>
          </div>

          <div class="ml-auto">
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary mr-2"
              :disabled="currentPage == 1"
              @click="loadAuditIndex(currentPage - 1)"
            >
              &laquo; {{ $t('audit.previous') }}
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary mr-2"
              :disabled="loadedCount < displayCount"
              @click="loadAuditIndex(currentPage + 1)"
            >
              {{ $t('audit.next') }} &raquo;
            </button>
          </div>
        </div>

        <table class="table table-sm table-hover mb-0">
          <thead>
            <tr>
              <th scope="col">{{ $t('audit.name') }}</th>
              <th scope="col">{{ $t('audit.description') }}</th>
              <th scope="col">{{ $t('audit.contact') }}</th>
              <th scope="col">{{ $t('audit.created-at') }}</th>
              <th scope="col">{{ $t('audit.updated-at') }}</th>
              <th scope="col">{{ $t('audit.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(audit, index) in audits" :key="index">
              <td class="text-break">
                <a :href="`${origin}/#/${audit.uuid.substr(0, 24)}/`" target="_blank">{{ audit.name }}</a>
              </td>
              <td class="text-break">
                {{ audit.description }}
              </td>
              <td class="text-break">
                <a :href="generateMailURL(audit)">
                  <span v-for="(contact, index) in audit.contacts" :key="index">{{ contact.name }}<br /></span>
                </a>
              </td>
              <td class="text-break">{{ displayDateTime(audit.created_at) }}</td>
              <td class="text-break">{{ displayDateTime(audit.updated_at) }}</td>
              <td>
                <button
                  type="button"
                  class="btn btn-sm btn-secondary float-right ml-2"
                  @click.prevent="deleteAudit(index, audit.uuid)"
                  v-text="$t('audit.delete')"
                />
                <button
                  type="button"
                  class="btn btn-sm btn-secondary float-right ml-2"
                  @click.prevent="rescindAudit(index, audit.uuid)"
                  v-if="audit.approved"
                  v-text="$t('audit.rescind')"
                />
                <button
                  type="button"
                  class="btn btn-sm btn-secondary float-right ml-2"
                  @click.prevent="withdrawAudit(index, audit.uuid)"
                  v-if="audit.submitted && !audit.approved"
                  v-text="$t('audit.withdraw')"
                />
                <button
                  type="button"
                  class="btn btn-sm btn-primary float-right ml-2"
                  @click.prevent="approveAudit(index, audit.uuid)"
                  v-if="audit.submitted && !audit.approved"
                  v-text="$t('audit.approve')"
                />
              </td>
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
  name: 'AuditList',
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
      currentPage: 1,
      origin: process.env.VUE_APP_USER_ORIGIN,
      utcOffset: 0,
      displayCount: 50,
      loadedCount: 0,
      status: '',
      keyword: ''
    };
  },
  watch: {
    keyword() {
      if (this.incrementalSearchTimer) {
        clearTimeout(this.incrementalSearchTimer);
      }
      this.incrementalSearchTimer = setTimeout(() => this.loadAuditIndex(1), 500);
    }
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
    withdrawAudit: async function withdrawAudit(index, auditUUID) {
      if (window.confirm(this.$i18n.t('audit.withdraw-confirmation')) === false) {
        return;
      }
      try {
        const res = await this.auditApiClient.delete(`${auditUUID}/submit/`);
        switch (res.status) {
          case 200: {
            this.errorMessage = '';
            Vue.delete(this.audits, index);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('audit.error-withdraw');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-withdraw');
      }
    },

    deleteAudit: async function deleteAudit(index, auditUUID) {
      if (window.confirm(this.$i18n.t('audit.delete-confirmation')) === false) {
        return;
      }
      try {
        const res = await this.auditApiClient.delete(`${auditUUID}/`);
        switch (res.status) {
          case 200: {
            this.errorMessage = '';
            Vue.delete(this.audits, index);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('audit.error-delete');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-delete');
      }
    },

    approveAudit: async function approveAudit(index, auditUUID) {
      if (window.confirm(this.$i18n.t('audit.approve-confirmation')) === false) {
        return;
      }
      try {
        const res = await this.auditApiClient.post(`${auditUUID}/approve/`);
        switch (res.status) {
          case 200: {
            this.errorMessage = '';
            Vue.delete(this.audits, index);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('audit.error-approve');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-approve');
      }
    },

    rescindAudit: async function rescindAudit(index, auditUUID) {
      if (window.confirm(this.$i18n.t('audit.rescind-confirmation')) === false) {
        return;
      }
      try {
        const res = await this.auditApiClient.delete(`${auditUUID}/approve/`);
        switch (res.status) {
          case 200: {
            this.errorMessage = '';
            Vue.delete(this.audits, index);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('audit.error-rescind');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-rescind');
      }
    },

    loadAuditIndex: async function loadAuditIndex(page) {
      let auditStatus = '';
      switch (this.status) {
        case 'ONGOING': {
          auditStatus = '&submitted=false&approved=false';
          break;
        }
        case 'SUBMITTED': {
          auditStatus = '&submitted=true&approved=false';
          break;
        }
        case 'APPROVED': {
          auditStatus = '&submitted=true&approved=true';
          break;
        }
        default: {
          auditStatus = '';
        }
      }

      try {
        const res = await this.auditApiClient.get(
          `?keyword=${this.keyword}&page=${page}&count=${this.displayCount}${auditStatus}`
        );
        switch (res.status) {
          case 200:
          case 304:
            this.loadedCount = res.data.length;
            this.audits = res.data;
            this.currentPage = page;
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
    this.loadAuditIndex(this.currentPage);
    moment.locale(this.$i18n.locale);
    this.utcOffset = moment().utcOffset();
  }
};
</script>
