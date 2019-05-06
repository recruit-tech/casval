<template>
  <div id="modal-restriction" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('home.modal.access-restriction.title') }}</h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('home.modal.access-restriction.message') }}<br />
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="container mt-4">
            <div class="row">
              <div class="col">{{ $t('home.modal.access-restriction.ip-restriction') }}</div>
              <div class="col-7">
                <select class="form-control form-control-sm" v-model="isIpRestricted">
                  <option value="true">{{ $t('home.modal.access-restriction.enable') }}</option>
                  <option value="false">{{ $t('home.modal.access-restriction.disable') }}</option>
                </select>
              </div>
            </div>
          </div>
          <div class="container mt-4 mb-0">
            <div class="row">
              <div class="col">{{ $t('home.modal.access-restriction.password-restriction') }}</div>
              <div class="col-7">
                <div class="input-group mb-3">
                  <div class="input-group-prepend">
                    <div class="input-group-text">
                      <input type="checkbox" v-model="isPasswordRestricted" />
                    </div>
                  </div>
                  <input
                    type="password"
                    class="form-control form-control-sm"
                    v-model="password"
                    :placeholder="$t('home.modal.access-restriction.password')"
                    :disabled="!isPasswordRestricted"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.access-restriction.cancel') }}
          </button>
          <button type="button" class="btn btn-primary" @click="applyRestriction">
            {{ $t('home.modal.access-restriction.ok') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModalAccessRestriction',
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
      password: '',
      errorMessage: '',
      isIpRestricted: this.audit.ip_restriction,
      isPasswordRestricted: this.audit.password_protection
    };
  },
  methods: {
    applyRestriction: async function applyRestriction() {
      if (this.isPasswordRestricted && this.password.length < process.env.VUE_APP_MIN_PASSWORD_LENGTH) {
        this.errorMessage = this.$i18n.t('home.modal.access-restriction.error-invalid-password', {
          minLength: process.env.VUE_APP_MIN_PASSWORD_LENGTH
        });
        return;
      }
      try {
        const request = {
          ip_restriction: this.isIpRestricted,
          password_protection: this.isPasswordRestricted
        };
        if (this.isPasswordRestricted) {
          request.password = this.password;
        }
        const res = await this.auditApiClient.patch('/', request);
        switch (res.status) {
          case 200:
            window.location.reload(true);
            break;
          default:
            this.errorMessage = this.$i18n.t('home.modal.access-restriction.error-general');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.modal.access-restriction.error-general');
      }
    }
  }
};
</script>
