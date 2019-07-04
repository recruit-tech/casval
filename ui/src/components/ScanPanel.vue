<template>
  <div class="container pt-2rem">
    <div class="row">
      <div class="col align-items-center">
        <div class="card" :class="cardBorderClass">
          <div class="card-header bg-white">
            <span>
              <b>
                <a :name="scan.uuid">{{ scan.target }}</a>
              </b>
              <small class="text-muted" style="opacity: 0.33"> ({{ scan.uuid.toUpperCase().substr(24, 8) }})</small>
            </span>
            <span class="float-right">
              <button type="button" class="close" @click="deleteScan"><span>&times;</span></button>
            </span>
          </div>
          <div class="card-header bg-white">
            <b class="card-text text-primary" v-if="scan.calculatedState === 'unscheduled'">
              {{ $t('home.scan.status.unscheduled') }}
            </b>
            <b class="card-text text-dark" v-else-if="scan.calculatedState === 'scheduled'">
              {{ $t('home.scan.status.scheduled') }}
            </b>
            <b class="card-text text-danger" v-else-if="scan.calculatedState === 'failure'">
              <font-awesome-icon icon="exclamation-circle"></font-awesome-icon> {{ $t('home.scan.status.failure') }}
            </b>
            <b class="card-text text-dark" v-else-if="scan.calculatedState === 'severity-unrated'">
              {{ $t('home.scan.status.severity-unrated') }}
            </b>
            <b class="card-text text-dark" v-else-if="scan.calculatedState === 'completed'">
              {{ $t('home.scan.status.completed') }}
            </b>
            <b class="card-text text-danger" v-else-if="scan.calculatedState === 'unsafe'">
              <font-awesome-icon icon="exclamation-circle"></font-awesome-icon> {{ $t('home.scan.status.unsafe') }}
            </b>
            <b class="card-text text-secondary" v-else>
              <font-awesome-icon icon="spinner" pulse></font-awesome-icon> {{ $t('home.scan.status.loading') }}
            </b>
          </div>
          <div class="card-body">
            <scan-panel-comment v-if="requireComment" :scan="scan" :scan-api-client="scanApiClient">
            </scan-panel-comment>
            <scan-panel-scheduled
              v-else-if="scan.calculatedState === 'scheduled'"
              :scan="scan"
              :scan-api-client="scanApiClient"
            >
            </scan-panel-scheduled>
            <scan-panel-scheduler
              v-else-if="
                scan.calculatedState === 'unscheduled' || scan.calculatedState === 'failure' || requireReschedule
              "
              :scan="scan"
              :scan-api-client="scanApiClient"
            >
            </scan-panel-scheduler>
            <scan-panel-result
              v-else-if="
                scan.calculatedState === 'completed' ||
                  scan.calculatedState === 'unsafe' ||
                  scan.calculatedState === 'severity-unrated'
              "
              :scan="scan"
              :scan-api-client="scanApiClient"
            >
            </scan-panel-result>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ScanPanelComment from './ScanPanelComment.vue';
import ScanPanelResult from './ScanPanelResult.vue';
import ScanPanelScheduled from './ScanPanelScheduled.vue';
import ScanPanelScheduler from './ScanPanelScheduler.vue';

export default {
  name: 'ScanPanel',
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
      requireComment: false,
      requireReschedule: false
    };
  },
  computed: {
    cardBorderClass: function cardBorderClass() {
      return {
        'border-primary': this.scan.calculatedState === 'unscheduled',
        'border-danger': this.scan.calculatedState === 'failure' || this.scan.calculatedState === 'unsafe'
      };
    }
  },
  components: {
    ScanPanelComment,
    ScanPanelResult,
    ScanPanelScheduled,
    ScanPanelScheduler
  },
  methods: {
    deleteScan: async function deleteScan() {
      try {
        const res = await this.scanApiClient.delete(`/${this.scan.uuid}/`);
        switch (res.status) {
          case 200:
            window.eventBus.$emit('SCAN_DELETED', this.scan.uuid);
            break;
          default:
            console.error(`Scan Deletion Failure: scanId=${this.scan.uuid}, status=${res.status}`);
        }
      } catch (e) {
        console.error(`Loading Failure: scanId=${this.scan.uuid}, exception=${e.message}`);
      }
    }
  }
};
</script>

<style scoped>
.pt-2rem {
  padding-top: 2rem;
}
</style>
