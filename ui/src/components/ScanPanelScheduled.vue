<template>
  <div>
    <div class="pb-1">
      <small class="text-dark">
        {{ schedule }}<br />
        {{ $t('home.scan.source-ip-notification', { sourceIp: scan.source_ip }) }}<br />
        {{ scanStartedAt }}
      </small>
    </div>
    <div class="pt-3">
      <div class="form-row">
        <div class="col text-right">
          <button class="btn btn-dark" @click="deleteScanSchedule">
            {{ $t('home.scan.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment';

export default {
  name: 'ScanPanelScheduled',
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
  methods: {
    deleteScanSchedule: async function deleteScanSchedule() {
      try {
        const res = await this.scanApiClient.delete(`${this.scan.uuid}/schedule/`);
        switch (res.status) {
          case 200: {
            window.eventBus.$emit('SCAN_UPDATED', this.scan.uuid);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('home.scan.error-deletion');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.scan.error-deletion');
      }
    },
    getUtcTime: function getUtcTime(time) {
      moment.locale(this.$i18n.locale);
      const utcOffset = moment().utcOffset();
      return moment(time, 'YYYY-MM-DDThh:mm:ss').add(utcOffset, 'minutes');
    }
  },
  computed: {
    schedule: function getSchedule() {
      let start = this.getUtcTime(this.scan.start_at);
      start = start.format(this.$i18n.t('home.scan.datetime'));
      let end = this.getUtcTime(this.scan.end_at);
      end = end.format(this.$i18n.t('home.scan.datetime'));
      return this.$i18n.t('home.scan.scheduled', { start, end });
    },
    scanStartedAt: function getScanStartedAt() {
      let startedAt = this.getUtcTime(this.scan.started_at);
      if (startedAt.year() < 2000) {
        return '';
      }
      startedAt = startedAt.format(this.$i18n.t('home.scan.scantime'));
      return this.$i18n.t('home.scan.scan-started', { startedAt });
    }
  },
  mounted() {
    this.updateTimer = window.setInterval(() => {
      window.eventBus.$emit('SCAN_UPDATED', this.scan.uuid);
    }, 60 * 1000);
  },
  beforeDestroy() {
    window.clearInterval(this.updateTimer);
  }
};
</script>
