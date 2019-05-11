<template>
  <div :id="modalId" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <font-awesome-icon icon="exclamation-circle"></font-awesome-icon> {{ $t('home.modal.scan-warning.title') }}
          </h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p v-html="$t('home.modal.scan-warning.message', { sourceIp: sourceIp })" />
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.scan-warning.cancel') }}
          </button>
          <button type="button" class="btn btn-danger" @click="setSchedule">
            <font-awesome-icon icon="clock"></font-awesome-icon> {{ $t('home.modal.scan-warning.schedule') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from 'jquery';

export default {
  name: 'ModalScanWarning',
  props: {
    modalId: {
      type: String,
      required: true
    },
    sourceIp: {
      type: String,
      required: true
    }
  },
  methods: {
    setSchedule() {
      this.$emit('set-schedule');
      window.sessionStorage.setItem('scan-warning-agreed', 'true');
      $(`#${this.modalId}`).modal('hide');
    }
  }
};
</script>
