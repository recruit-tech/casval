<template>
  <div :id="modalId" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            {{ $t('home.modal.scan-from-api.title') }}
          </h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          {{ $t('home.modal.scan-from-api.message1') }}
          <span v-html="$t('home.modal.scan-from-api.message2')"></span><br />
          <pre class="rounded bg-dark text-light text-wrap my-2 p-2 select-all">{{ curlCommand }}</pre>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.scan-from-api.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModalScanFromApi',
  props: {
    modalId: {
      type: String,
      required: true
    },
    scan: {
      type: Object,
      required: true
    },
    restrictedToken: {
      type: String,
      required: true
    },
    startAt: {
      type: Object,
      required: true
    },
    endAt: {
      type: Object,
      required: true
    }
  },
  methods: {
    selectAll: function selectAll() {
      this.select();
    }
  },
  computed: {
    curlCommand: function curlCommand() {
      const startAt = this.startAt.format('YYYY-MM-DDTHH:mm:ss');
      const endAt = this.endAt.format('YYYY-MM-DDTHH:mm:ss');

      return `curl '${process.env.VUE_APP_API_ENDPOINT}/scan/${this.scan.uuid}/schedule/' -X PATCH -H 'Authorization: Bearer ${this.restrictedToken}' -H 'Content-Type: application/json' -d '{"target": "${this.scan.target}", "start_at":"${startAt}", "end_at":"${endAt}", "slack_webhook_url":""}'`;
    }
  }
};
</script>
<style scoped>
.select-all {
  user-select: all;
  -webkit-user-select: all;
  -moz-user-select: all;
  -ms-user-select: element;
}
</style>
