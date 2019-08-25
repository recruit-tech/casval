<template>
  <div>
    <div>
      <small class="text-dark"> {{ scanEndedAt }}<br /> </small>
      <small class="text-dark" v-if="isSeverityUnrated">
        <font-awesome-icon icon="clock" class="mr-1"></font-awesome-icon>
        {{ $t('home.scan.result.severity-unrated') }}<br />
      </small>
      <small class="text-dark" v-if="!isSeverityUnrated && !isFixRequired">
        {{ $t('home.scan.result.no-critical-issues') }}<br />
      </small>
      <small class="text-dark" v-if="!isSeverityUnrated" v-for="result in scan.results" :key="result.id">
        <span v-if="result.fix_required === 'REQUIRED'">
          <a v-tooltip="{ content: result.advice }">
            <font-awesome-icon icon="exclamation-circle" class="mr-2"></font-awesome-icon>{{ result.name }} -
            {{ result.port }}
          </a>
          <br />
        </span>
      </small>
      <small v-if="scan.comment" class="text-secondary">
        <hr class="mb-3" />
        <font-awesome-icon icon="pencil-alt" class="mr-2"></font-awesome-icon>{{ scan.comment }}<br />
      </small>
    </div>
    <div class="pt-3">
      <div class="form-row">
        <div class="col text-right">
          <button
            v-if="isFixRequired || commentEnabled"
            class="btn"
            :class="{
              'btn-outline-secondary': scan.calculatedState !== 'unsafe',
              'btn-secondary': scan.calculatedState === 'unsafe',
              disabled: scan.calculatedState !== 'unsafe'
            }"
            @click="setComment"
          >
            <font-awesome-icon icon="pencil-alt"></font-awesome-icon> {{ commentButtonTitle }}
          </button>
          <button
            v-if="isFixRequired"
            class="btn ml-3"
            :class="{
              'btn-outline-secondary': scan.calculatedState !== 'unsafe',
              'btn-primary': scan.calculatedState === 'unsafe',
              disabled: scan.calculatedState !== 'unsafe'
            }"
            @click="setReschedule"
          >
            <font-awesome-icon icon="clock"></font-awesome-icon> {{ $t('home.scan.result.reschedule') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment';
import ScanPanelScheduler from './ScanPanelScheduler.vue';

export default {
  name: 'ScanPanelResult',
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
      updateTimer: null,
      commentEnabled: process.env.VUE_APP_SCAN_COMMENT_ENABLED === 'true'
    };
  },
  components: {
    ScanPanelScheduler
  },
  methods: {
    setComment: function setComment() {
      this.$parent.requireComment = true;
    },
    setReschedule: function setReschedule() {
      this.$parent.requireReschedule = true;
    },
    getUtcTime: function getUtcTime(time) {
      moment.locale(this.$i18n.locale);
      const utcOffset = moment().utcOffset();
      return moment(time, 'YYYY-MM-DD hh:mm:ss').add(utcOffset, 'minutes');
    }
  },
  computed: {
    commentButtonTitle: function commentButtonTitle() {
      const title = this.isFixRequired ? 'home.scan.result.ignore' : 'home.scan.result.write-comment';
      return this.$i18n.t(title);
    },
    isFixRequired: function isFixRequired() {
      return this.scan.results.some(result => result.fix_required === 'REQUIRED');
    },
    isSeverityUnrated: function isSeverityUnrated() {
      return this.scan.results.some(result => result.fix_required === 'UNDEFINED');
    },
    scanEndedAt: function scanEndedAt() {
      let endedAt = this.getUtcTime(this.scan.ended_at);
      if (endedAt.year() < 2000) {
        return '';
      }
      endedAt = endedAt.format(this.$i18n.t('home.scan.scantime'));
      return this.$i18n.t('home.scan.scan-ended', { endedAt });
    }
  },
  mounted() {
    if (this.isSeverityUnrated) {
      this.updateTimer = window.setInterval(() => {
        window.eventBus.$emit('SCAN_UPDATED', this.scan.uuid);
      }, 60 * 1000);
    }
  },
  beforeDestroy() {
    if (this.updateTimer !== null) {
      window.clearInterval(this.updateTimer);
    }
  }
};
</script>

<style lang="scss">
.tooltip {
  &[aria-hidden='true'] {
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.15s, visibility 0.15s;
  }

  .tooltip-inner {
    max-width: 60rem;
    text-align: left;
  }

  &[aria-hidden='false'] {
    visibility: visible;
    opacity: 1;
    transition: opacity 0.15s;
  }

  &.popover {
    $color: #f9f9f9;

    .popover-inner {
      background: $color;
      color: red;
      padding: 24px;
      border-radius: 5px;
      box-shadow: 0 5px 30px rgba(black, 0.1);
    }

    .popover-arrow {
      border-color: $color;
    }
  }

  display: block !important;
  z-index: 2000;
}
</style>
