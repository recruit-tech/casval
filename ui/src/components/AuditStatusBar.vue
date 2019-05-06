<template>
  <div class="container-fluid fixed-bottom pb-5" v-if="auditStatus !== 'ongoing'">
    <div class="row">
      <div class="col"></div>

      <div
        class="col10 text-center border border-success shadow-sm p-3 bg-white rounded"
        v-if="auditStatus === 'approved'"
      >
        <b class="text-success pr-2">
          <font-awesome-icon icon="check-circle" class="mr-1"></font-awesome-icon>
          {{ $t('home.audit-status-bar.submit-approved') }}
        </b>
      </div>

      <div
        class="col10 text-center border border-primary shadow-sm p-3 bg-white rounded"
        v-if="auditStatus === 'submit-ready'"
      >
        <b class="text-primary pr-2">
          <font-awesome-icon icon="exclamation-circle" class="mr-1"></font-awesome-icon>
          {{ $t('home.audit-status-bar.submit-ready') }}
        </b>
        <button class="btn btn-primary" @click="submit">
          <b>{{ $t('home.audit-status-bar.submit') }}</b>
        </button>
      </div>
      <div
        class="col10 text-center border border-sedoncary shadow-sm p-3 bg-white rounded"
        v-if="auditStatus === 'submitted'"
      >
        <b class="text-secondary pr-2">{{ $t('home.audit-status-bar.submit-completed') }}</b>
        <button class="btn btn-secondary disabled" @click="cancel">
          <b>{{ $t('home.audit-status-bar.withdraw') }}</b>
        </button>
      </div>
      <div class="col10 text-center border border-danger shadow-sm p-3 bg-white rounded" v-if="auditStatus === 'fatal'">
        <span class="text-danger">
          <font-awesome-icon icon="exclamation-circle" class="mr-1"></font-awesome-icon
          >{{ $t('home.audit-status-bar.critical-vulnerability-found') }}
        </span>
      </div>
      <div class="col"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuditStatusBar',
  props: {
    audit: {
      type: Object,
      required: true
    },
    auditApiClient: {
      type: Function,
      required: true
    },
    auditStatus: {
      type: String,
      required: true
    }
  },
  methods: {
    submit: async function submit() {
      try {
        const res = await this.auditApiClient.post('/submit/');
        switch (res.status) {
          case 200:
            this.errorMessage = '';
            window.eventBus.$emit('RELOAD_REQUESTED');
            break;
          default:
            this.errorMessage = this.$i18n.t('home.audit-status-bar.submit-failure');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.audit-status-bar.submit-failure');
      }
    },
    cancel: async function cancel() {
      try {
        if (window.confirm(this.$i18n.t('home.audit-status-bar.withdraw-confirmation'))) {
          const res = await this.auditApiClient.delete('/submit/');
          switch (res.status) {
            case 200:
              this.errorMessage = '';
              window.eventBus.$emit('RELOAD_REQUESTED');
              break;
            default:
              this.errorMessage = this.$i18n.t('home.audit-status-bar.withdraw-failure');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.audit-status-bar.withdraw-failure');
      }
    }
  }
};
</script>
