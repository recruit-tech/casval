<template>
  <div>
    <div>
      <small class="text-dark" v-if="isSeverityUnrated">
        <font-awesome-icon icon="clock" class="mr-1"></font-awesome-icon>
        {{ $t('home.scan.result.severity-unrated') }}
      </small>
      <small class="text-dark" v-if="!isSeverityUnrated && !isFixRequired">
        {{ $t('home.scan.result.no-critical-issues') }}
      </small>
      <small class="text-dark" v-for="result in scan.results" :key="result.id">
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
        <font-awesome-icon icon="pencil-alt" class="mr-2"></font-awesome-icon>{{ scan.comment }}
      </small>
    </div>
    <div class="pt-3">
      <div class="form-row" v-if="isFixRequired">
        <div class="col text-right">
          <button
            class="btn mr-3"
            :class="{
              'btn-outline-secondary': scan.calculatedState !== 'unsafe',
              'btn-secondary': scan.calculatedState === 'unsafe',
              disabled: scan.calculatedState !== 'unsafe'
            }"
            @click="setComment"
          >
            <font-awesome-icon icon="pencil-alt"></font-awesome-icon> {{ $t('home.scan.result.ignore') }}
          </button>
          <button
            class="btn"
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
      updateTimer: null
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
    }
  },
  computed: {
    isFixRequired: function isFixRequired() {
      return this.scan.results.some(result => result.fix_required === 'REQUIRED');
    },
    isSeverityUnrated: function isSeverityUnrated() {
      return this.scan.results.some(result => result.fix_required === 'UNDEFINED');
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
