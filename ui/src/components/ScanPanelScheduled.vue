<template>
  <div>
    <div class="pb-1">
      <small class="text-dark">
        {{ schedule }}<br />
        {{ $t('home.scan.source-ip-notification', { sourceIp: scan.source_ip }) }}
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
    }
  },
  computed: {
    schedule: function getSchedule() {
      moment.locale(this.$i18n.locale);
      const utcOffset = moment().utcOffset();
      let start = moment(this.scan.start_at, 'YYYY-MM-DD hh:mm:ss').add(utcOffset, 'minutes');
      start = start.format(this.$i18n.t('home.scan.datetime'));
      let end = moment(this.scan.end_at, 'YYYY-MM-DD hh:mm:ss').add(utcOffset, 'minutes');
      end = end.format(this.$i18n.t('home.scan.datetime'));
      return this.$i18n.t('home.scan.scheduled', { start, end });
    }
  }
};
</script>
