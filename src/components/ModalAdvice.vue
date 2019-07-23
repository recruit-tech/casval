<template>
  <div :id="modalId" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('vulnerability.modal.advice.title') }}</h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('vulnerability.modal.advice.message') }}<br />
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="pb-1">
            <textarea
              class="form-control form-control-sm bg-none"
              rows="5"
              :placeholder="$t('vulnerability.modal.advice.placeholder')"
              v-model="newAdvice"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('vulnerability.modal.advice.cancel') }}
          </button>
          <button type="button" class="btn btn-primary" @click="updateAdvice">
            {{ $t('vulnerability.modal.advice.ok') }}
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
  name: 'ModalAdvice',
  props: {
    index: {
      type: Number,
      required: true
    },
    oid: {
      type: String,
      required: true
    },
    modalId: {
      type: String,
      required: true
    },
    advice: {
      type: String,
      required: true
    },
    vulnerabilityApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      newAdvice: this.advice,
      errorMessage: ''
    };
  },
  watch: {
    advice() {
      this.newAdvice = this.advice;
    }
  },
  methods: {
    updateAdvice: async function updateAdvice() {
      try {
        const res = await this.vulnerabilityApiClient.patch(`/${this.oid}/`, { advice: this.newAdvice });
        switch (res.status) {
          case 200: {
            this.$emit('adviceUpdated', this.index, this.newAdvice);
            $(`#${this.modalId}`).modal('hide');
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('vulnerability.error-update');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('vulnerability.error-update');
      }
    }
  }
};
</script>
<style scoped>
.bg-none {
  background-image: none;
}
</style>
