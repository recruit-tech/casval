<template>
  <div>
    <div class="d-flex align-items-start flex-row">
      <div class="py-1">
        <small class="text-dark">
          {{ guideMessage }}<br />
          <span class="text-danger">{{ errorMessage }}</span>
        </small>
      </div>
    </div>
    <div class="align-items-start flex-row">
      <div class="py-1">
        <textarea
          class="form-control form-control-sm"
          rows="5"
          :placeholder="textareaPlaceholder"
          v-model="comment"
        ></textarea>
      </div>
    </div>
    <div class="pt-3">
      <div class="form-row">
        <div class="col text-right">
          <button v-if="this.$parent.requireComment" class="btn btn-outline-secondary mr-3" @click="cancelComment">
            <font-awesome-icon icon="arrow-left"></font-awesome-icon>
            {{ $t('home.scan.back') }}
          </button>
          <button type="button" class="btn btn-primary" @click="registerComment">
            <font-awesome-icon icon="pencil-alt"></font-awesome-icon> {{ commentButtonTitle }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScanPanelComment',
  props: {
    scan: {
      type: Object,
      required: true
    },
    scanApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      errorMessage: '',
      comment: this.scan.comment
    };
  },
  methods: {
    cancelComment: async function cancelComment() {
      this.$parent.requireComment = false;
    },
    registerComment: async function registerComment() {
      try {
        const res = await this.scanApiClient.patch(`${this.scan.uuid}/`, {
          comment: this.comment
        });
        switch (res.status) {
          case 200: {
            this.errorMessage = '';
            this.$parent.requireComment = false;
            window.eventBus.$emit('SCAN_UPDATED', this.scan.uuid);
            break;
          }
          default: {
            this.errorMessage = `判断理由の登録に失敗しました（Status：${res.status}）`;
          }
        }
      } catch (e) {
        this.errorMessage = `判断理由の登録に失敗しました（${e.message}）`;
      }
    }
  },
  computed: {
    isFixRequired: function isFixRequired() {
      return this.scan.results.some(result => result.fix_required === 'REQUIRED');
    },
    guideMessage: function guideMessage() {
      const text = this.isFixRequired ? 'home.scan.result.fill-reason' : 'home.scan.result.fill-comment';
      return this.$i18n.t(text, { reminingLength: this.reminingStringLength });
    },
    textareaPlaceholder: function textareaPlaceholder() {
      const text = this.isFixRequired ? 'home.scan.result.reason' : 'home.scan.result.comment';
      return this.$i18n.t(text);
    },
    commentButtonTitle: function commentButtonTitle() {
      const title = this.isFixRequired ? 'home.scan.result.submit-reason' : 'home.scan.result.submit-comment';
      return this.$i18n.t(title);
    },
    reminingStringLength: function getReminingStringLength() {
      const maxLength = 1000;
      return maxLength - this.comment.length;
    }
  }
};
</script>
