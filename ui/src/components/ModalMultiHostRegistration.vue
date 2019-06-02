<template>
  <div id="modal-multi-host-registration" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('home.modal.multi-host-registration.title') }}</h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('home.modal.multi-host-registration.message') }}<br />
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="pb-1">
            <textarea
              v-on:keyup="removeError"
              class="form-control form-control-sm bg-none"
              :class="{ 'is-invalid': this.errorMessage != '', 'text-danger': this.errorMessage != '' }"
              rows="5"
              :placeholder="$t('home.modal.multi-host-registration.placeholder')"
              v-model="targetList"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.multi-host-registration.cancel') }}
          </button>
          <button type="button" class="btn btn-primary" @click="addTargets(targetList)">
            {{ $t('home.modal.multi-host-registration.ok') }}
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
  name: 'ModalMultiHostRegistration',
  props: {
    addTargetApi: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      targetList: '',
      errorMessage: '',
      errorCount: 0
    };
  },
  methods: {
    resetData: function resetData() {
      this.targetList = '';
      this.errorMessage = '';
      this.errorCount = 0;
    },
    removeError: function removeError() {
      if (this.targetList.length === 0) {
        this.resetData();
      }
    },
    addTargets: function addTargets(targets) {
      this.resetData();
      const promises = targets.split(/\n/).reduce((acc, value) => {
        const target = value.replace(/\s+/g, '');
        if (target.length > 0) {
          acc.push(
            this.addTargetApi(target).catch(error => {
              this.errorCount += 1;
              this.errorMessage = this.$i18n.t('home.modal.multi-host-registration.error-general', {
                count: this.errorCount
              });
              this.targetList += `${target}\t${error.message}\n`;
            })
          );
        }
        return acc;
      }, []);

      Promise.all(promises).then(results => {
        results.map(result => {
          if (result) window.eventBus.$emit('SCAN_REGISTERED', result);
          return result;
        });
        if (this.errorMessage === '') {
          this.resetData();
          $('#modal-multi-host-registration').modal('hide');
        }
      });
    }
  }
};
</script>
<style scoped>
.bg-none {
  background-image: none;
}
</style>
