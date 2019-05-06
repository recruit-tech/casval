<template>
  <div id="modal-authenticate" class="modal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('authentication.title') }}</h5>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('authentication.message') }}
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="container mt-4">
            <div class="row">
              <div class="col"></div>
              <div class="col-7">
                <input
                  type="password"
                  class="form-control"
                  :placeholder="$t('authentication.password')"
                  v-model="password"
                  @keyup.enter="authenticate"
                />
              </div>
              <div class="col"></div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" @click="authenticate">{{ $t('authentication.ok') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ModalAuthenticate',
  data() {
    return {
      password: '',
      errorMessage: ''
    };
  },
  computed: {
    authApiClient: function createAuditApiClient() {
      return axios.create({
        baseURL: `${process.env.VUE_APP_API_ENDPOINT}/auth`,
        timeout: process.env.VUE_APP_API_TIMEOUT,
        validateStatus: () => true
      });
    }
  },
  methods: {
    authenticate: async function applyRestriction() {
      try {
        const res = await this.authApiClient.post('/', {
          password: this.password
        });
        switch (res.status) {
          case 200:
            window.localStorage.setItem('token', res.data.token);
            window.location.reload(true);
            break;
          default:
            this.errorMessage = this.$i18n.t('authentication.error-general');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('authentication.error-general');
      }
    }
  }
};
</script>
