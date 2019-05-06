<template>
  <form @submit.prevent="addTarget">
    <div class="form-row">
      <div class="col">
        <div class="d-flex flex-row">
          <div class="mr-auto w-100 pr-3">
            <input
              type="text"
              class="form-control"
              v-model="target"
              :placeholder="$t('home.target-form.ip-address-or-host-name')"
            />
          </div>
          <div>
            <button class="btn w-100 btn-primary">{{ $t('home.target-form.register-target') }}</button>
          </div>
        </div>
        <small class="form-text text-danger">{{ errorMessage }}</small>
      </div>
    </div>
  </form>
</template>

<script>
export default {
  name: 'TargetForm',
  props: {
    audit: {
      type: Object,
      required: true
    },
    auditApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      target: '',
      errorMessage: ''
    };
  },
  methods: {
    addTarget: async function addTarget() {
      try {
        if (this.target.length === 0) {
          this.errorMessage = this.$i18n.t('home.target-form.status.target-is-empty');
          return;
        }
        const res = await this.auditApiClient.post('/scan/', { target: this.target });
        switch (res.status) {
          case 200:
          case 304:
            this.target = '';
            this.errorMessage = '';
            window.eventBus.$emit('SCAN_REGISTERED', res.data.uuid);
            break;
          case 400: {
            const message = JSON.stringify(res.data.message);
            if (message.indexOf('target-is-not-fqdn-or-ipv4') >= 0) {
              this.errorMessage = this.$i18n.t('home.target-form.status.target-is-not-fqdn-or-ipv4');
            } else if (message.indexOf('Audit has been submitted or approved') >= 0) {
              this.errorMessage = this.$i18n.t('home.target-form.status.audit-submitted');
            } else if (message.indexOf('target-is-private-ip') >= 0) {
              this.errorMessage = this.$i18n.t('home.target-form.status.target-is-private-ip');
            } else if (message.indexOf('could-not-resolve-target-fqdn') >= 0) {
              this.errorMessage = this.$i18n.t('home.target-form.status.could-not-resolve-target-fqdn');
            } else {
              this.errorMessage = message;
            }
            break;
          }
          case 401:
            this.errorMessage = this.$i18n.t('home.target-form.status.invalid-token');
            break;
          default:
            this.errorMessage = this.$i18n.t('home.target-form.status.unknown-error');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.target-form.status.unknown-error');
      }
    }
  }
};
</script>
