<template>
  <form @submit.prevent="addTarget">
    <div class="form-row">
      <div class="col">
        <div class="d-flex justify-content-end">
          <div class="mr-auto flex-fill pr-3">
            <div class="input-group">
              <input
                type="text"
                class="form-control"
                v-model="target"
                :placeholder="$t('home.target-form.ip-address-or-host-name')"
              />
              <div class="input-group-append div-multi-host-registration">
                <span class="input-group-text" data-toggle="modal" data-target="#modal-multi-host-registration">
                  <font-awesome-icon icon="file-upload"></font-awesome-icon>
                </span>
              </div>
            </div>
          </div>
          <div>
            <button class="btn btn-primary">{{ $t('home.target-form.register-target') }}</button>
          </div>
        </div>
        <small class="form-text text-danger">{{ errorMessage }}</small>
      </div>
    </div>
    <modal-multi-host-registration :add-target-api="addTargetApi"></modal-multi-host-registration>
  </form>
</template>

<script>
import ModalMultiHostRegistration from './ModalMultiHostRegistration.vue';

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
  components: {
    ModalMultiHostRegistration
  },
  data() {
    return {
      target: '',
      errorMessage: ''
    };
  },
  methods: {
    addTargetApi: async function addTargetApi(target) {
      const res = await this.auditApiClient.post('/scan/', { target });
      switch (res.status) {
        case 200:
        case 304:
          return res.data.uuid;
        case 400: {
          const message = JSON.stringify(res.data.message);
          if (message.indexOf('target-is-not-fqdn-or-ipv4') >= 0) {
            throw new Error(this.$i18n.t('home.target-form.status.target-is-not-fqdn-or-ipv4'));
          } else if (message.indexOf('Audit has been submitted or approved') >= 0) {
            throw new Error(this.$i18n.t('home.target-form.status.audit-submitted'));
          } else if (message.indexOf('target-is-private-ip') >= 0) {
            throw new Error(this.$i18n.t('home.target-form.status.target-is-private-ip'));
          } else if (message.indexOf('could-not-resolve-target-fqdn') >= 0) {
            throw new Error(this.$i18n.t('home.target-form.status.could-not-resolve-target-fqdn'));
          } else {
            throw new Error(message);
          }
        }
        case 401:
          throw new Error(this.$i18n.t('home.target-form.status.invalid-token'));
        default:
          throw new Error(this.$i18n.t('home.target-form.status.unknown-error'));
      }
    },
    addTarget: async function addTarget() {
      if (this.target.length === 0) {
        this.errorMessage = this.$i18n.t('home.target-form.status.target-is-empty');
        return;
      }
      try {
        const uuid = await this.addTargetApi(this.target);
        window.eventBus.$emit('SCAN_REGISTERED', uuid);
        this.target = '';
        this.errorMessage = '';
      } catch (e) {
        this.errorMessage = e.message;
      }
    }
  }
};
</script>
<style scoped>
.input-group > .div-multi-host-registration {
  margin-left: -2.5rem;
  z-index: 2;
  border: 0px solid rgba(0, 0, 0, 0) !important;
}
.input-group > .div-multi-host-registration > .input-group-text {
  border-width: 0;
  background-color: rgba(255, 255, 255, 0);
  opacity: 0.5;
  transition: 0.5s;
}
.input-group > .div-multi-host-registration > .input-group-text:hover {
  cursor: pointer;
  opacity: 1;
  transition: 0.5s;
}
.input-group > .custom-select:not(:last-child),
.input-group > .form-control:not(:last-child) {
  border-top-right-radius: 0.25rem;
  border-bottom-right-radius: 0.25rem;
}
</style>
