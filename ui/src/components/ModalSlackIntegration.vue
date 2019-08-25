<template>
  <div id="modal-slack-integration" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('home.modal.slack-integration.title') }}</h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p>
            <span v-html="$t('home.modal.slack-integration.message')"></span><br />
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="py-1">
            <div class="row">
              <div class="col">{{ $t('home.modal.slack-integration.incoming-webhooks') }}</div>
              <div class="col-7">
                <div class="input-group mb-3">
                  <div class="input-group-prepend">
                    <div class="input-group-text">
                      <input type="checkbox" v-model="isSlackIntegrated" v-on:change="initializeUrlForm" />
                    </div>
                  </div>
                  <input
                    type="text"
                    class="form-control form-control-sm"
                    v-model="slackWebhookUrl"
                    v-on:focus="removeDummyUrl"
                    :placeholder="$t('home.modal.slack-integration.incoming-webhooks-url')"
                    :disabled="!isSlackIntegrated"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.slack-integration.cancel') }}
          </button>
          <button type="button" class="btn btn-primary" @click="changeSlackIntegration">
            {{ $t('home.modal.slack-integration.ok') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from 'jquery';
import 'bootstrap';

export default {
  name: 'ModalSlackIntegration',
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
      isSlackIntegrated: this.audit.slack_integration,
      slackWebhookUrl: '',
      dummyWebhookUrl: '****************',
      errorMessage: ''
    };
  },
  methods: {
    isValidSlackUrl: function isValidSlackUrl(url) {
      const parser = document.createElement('a');
      parser.href = url;
      return parser.protocol.startsWith('https') && parser.hostname.endsWith('slack.com');
    },
    initializeUrlForm: function initializeUrlForm() {
      if (!this.isSlackIntegrated) {
        this.slackWebhookUrl = '';
      }
    },
    removeDummyUrl: function removeDummyUrl() {
      if (!this.isValidSlackUrl(this.slackWebhookUrl)) {
        this.slackWebhookUrl = '';
      }
    },
    changeSlackIntegration: async function changeSlackIntegration() {
      this.errorMessage = '';

      if (this.isSlackIntegrated && !this.isValidSlackUrl(this.slackWebhookUrl)) {
        this.errorMessage = this.$i18n.t('home.modal.slack-integration.error-invalid-url');
        return;
      }
      try {
        const request = {
          slack_default_webhook_url: this.isSlackIntegrated ? this.slackWebhookUrl : ''
        };
        const res = await this.auditApiClient.patch('/', request);
        switch (res.status) {
          case 200:
            $('#modal-slack-integration').modal('hide');
            break;
          default:
            this.errorMessage = this.$i18n.t('home.modal.slack-integration.error-general');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.modal.slack-integration.error-general');
      }
    }
  },
  created: function created() {
    this.slackWebhookUrl = this.audit.slack_integration ? this.dummyWebhookUrl : '';
  }
};
</script>
