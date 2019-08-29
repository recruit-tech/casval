<template>
  <div>
    <div id="overlay" v-if="isNonEditable"></div>

    <div id="menu" class="container-fluid px-0 pb-0">
      <div class="container-fluid pt-3 pb-3">
        <div class="row">
          <div class="col text-right">
            <div class="dropdown">
              <button class="btn btn-outline-dark dropdown-toggle bg-white" data-toggle="dropdown">
                <font-awesome-icon icon="bars"></font-awesome-icon> {{ settingMenuTitle }}
              </button>
              <div class="dropdown-menu dropdown-menu-right">
                <button class="dropdown-item" type="button" @click="downloadAudit" v-if="auditDownloadable">
                  {{ $t('home.modal.download-audit') }}
                </button>
                <a href="#" class="dropdown-item" data-toggle="modal" data-target="#modal-contacts">{{
                  $t('home.modal.change-contact')
                }}</a>
                <a href="#" class="dropdown-item" data-toggle="modal" data-target="#modal-slack-integration">{{
                  $t('home.modal.slack-integration.title')
                }}</a>
                <a href="#" class="dropdown-item" data-toggle="modal" data-target="#modal-restriction">{{
                  $t('home.modal.restrict-access')
                }}</a>
                <div class="dropdown-divider"></div>
                <a :href="adminContacts" class="dropdown-item">{{ $t('home.modal.contact-admin') }}</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div id="header" class="container-fluid px-0 pb-0" :class="{ grayscale: isNonEditable }">
      <div class="container-fluid pt-3 pb-3">
        <div class="row">
          <div class="col">
            <img src="../assets/logo-grey.svg" class="logo" />
          </div>
        </div>
      </div>
      <div class="container pt-2 pb-5">
        <div class="row">
          <div class="col">
            <p class="h4 text-dark mb-3">
              <b>{{ audit.name }}</b>
            </p>
            <target-form :audit="audit" :audit-api-client="auditApiClient"></target-form>
          </div>
        </div>
      </div>
    </div>

    <div v-for="scanUUID in scanOrder" :key="scanUUID" :class="{ grayscale: isNonEditable }">
      <scan-panel
        :scan="scans[scanUUID]"
        :scan-api-client="scanApiClient"
        :restricted-token="restrictedToken"
      ></scan-panel>
    </div>
    <div class="pt-5 pb-5"></div>
    <modal-contacts :audit="audit" :audit-api-client="auditApiClient"></modal-contacts>
    <modal-slack-integration :audit="audit" :audit-api-client="auditApiClient"></modal-slack-integration>
    <modal-access-restriction :audit="audit" :audit-api-client="auditApiClient"></modal-access-restriction>
    <audit-status-bar :audit="audit" :audit-api-client="auditApiClient" :audit-status="auditStatus"></audit-status-bar>
  </div>
</template>

<script>
import Vue from 'vue';
import AuditStatusBar from './AuditStatusBar.vue';
import ModalContacts from './ModalContacts.vue';
import ModalSlackIntegration from './ModalSlackIntegration.vue';
import ModalAccessRestriction from './ModalAccessRestriction.vue';
import ScanPanel from './ScanPanel.vue';
import TargetForm from './TargetForm.vue';

function getScanStatus(scan) {
  if (scan.scheduled === true) {
    return 'scheduled';
  }
  if (scan.scheduled === false && scan.processed === false) {
    return 'unscheduled';
  }
  if (scan.scheduled === false && scan.processed === true) {
    if (scan.error_reason.length > 0) {
      return 'failure';
    }
    if (scan.results.some(result => result.fix_required === 'UNDEFINED')) {
      return 'severity-unrated';
    }
    if (scan.results.every(result => result.fix_required !== 'REQUIRED')) {
      return 'completed';
    }
    if (scan.results.some(result => result.fix_required === 'REQUIRED') && scan.comment.length > 0) {
      return 'completed';
    }
    return 'unsafe';
  }
  return 'unknown-state';
}

export default {
  name: 'Home',
  props: {
    audit: {
      type: Object,
      required: true
    },
    auditApiClient: {
      type: Function,
      required: true
    },
    scanApiClient: {
      type: Function,
      required: true
    },
    restrictedToken: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      adminContacts: process.env.VUE_APP_ADMIN_CONTACTS,
      scans: {},
      scanOrder: []
    };
  },
  methods: {
    getTimezoneOffset: function getTimezoneOffset() {
      const date = new Date();
      return -1 * date.getTimezoneOffset();
    },
    downloadAudit: async function downloadAudit() {
      try {
        const offset = this.getTimezoneOffset();
        const res = await this.auditApiClient.get(`/download/?tz_offset=${offset}`);
        switch (res.status) {
          case 200: {
            const csv = res.data;
            const mime = 'text/csv';
            const filename = `casval-audit-result-${this.audit.uuid}.csv`;
            const blob = new Blob([csv], { type: mime });
            if (window.navigator.msSaveBlob) {
              window.navigator.msSaveBlob(blob, filename); // IE
            } else if (window.URL && window.URL.createObjectURL) {
              const a = document.createElement('a');
              a.href = window.URL.createObjectURL(blob);
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }
            break;
          }
          default:
            alert(this.$i18n.t('home.modal.error-download'));
        }
      } catch (e) {
        alert(this.$i18n.t('home.modal.error-download'));
      }
    }
  },
  components: {
    AuditStatusBar,
    ModalContacts,
    ModalSlackIntegration,
    ModalAccessRestriction,
    ScanPanel,
    TargetForm
  },
  computed: {
    settingMenuTitle: function settingMenuTitle() {
      return this.isNonEditable ? this.$t('home.modal.settings') : '';
    },
    auditDownloadable: function auditDownloadable() {
      return Object.keys(this.scans).some(scanUUID => {
        if (this.scans[scanUUID] && this.scans[scanUUID].processed) {
          return true;
        }
        return false;
      });
    },
    auditStatus: function auditStatus() {
      if (this.audit.approved) {
        return 'approved';
      }
      if (this.audit.submitted) {
        return 'submitted';
      }
      if (Object.keys(this.scans).length === 0) {
        return 'ongoing';
      }
      let status = 'submit-ready';
      Object.keys(this.scans).some(scanUUID => {
        const state = this.scans[scanUUID].calculatedState;
        if (state === 'unsafe') {
          status = 'fatal';
          return true;
        }
        if (state !== 'completed') {
          status = 'ongoing';
          return true;
        }
        return false;
      });
      return status;
    },
    isNonEditable: function isNonEditable() {
      return this.audit.approved || this.audit.submitted;
    }
  },
  created: function created() {
    window.eventBus.$on('AUDIT_UPDATED', async data => {
      Object.keys(data).forEach(key => {
        // todo
        console.log(key);
      });
    });
    window.eventBus.$on('SCAN_REGISTERED', async scanUUID => {
      this.scanOrder.unshift(scanUUID);
      Vue.set(this.scans, scanUUID, { uuid: scanUUID, target: '', calculatedState: 'loading' });
      window.eventBus.$emit('SCAN_UPDATED', scanUUID);
    });
    window.eventBus.$on('SCAN_UPDATED', async scanUUID => {
      try {
        const res = await this.scanApiClient.get(`/${scanUUID}/`);
        switch (res.status) {
          case 200: {
            const scan = res.data;
            scan.calculatedState = getScanStatus(scan);
            Vue.set(this.scans, scanUUID, scan);
            break;
          }
          default: {
            console.error(`Loading Failure: scanUUID=${scanUUID}, status=${res.status}`);
            break;
          }
        }
      } catch (e) {
        console.error(`Loading Failure: scanUUID=${scanUUID}, exception=${e.message}`);
      }
    });
    window.eventBus.$on('SCAN_DELETED', async scanUUID => {
      const index = this.scanOrder.indexOf(scanUUID);
      Vue.delete(this.scanOrder, index);
      Vue.delete(this.scans, scanUUID);
    });
    this.audit.scans.forEach(scanUUID => {
      window.eventBus.$emit('SCAN_REGISTERED', scanUUID);
    });
  }
};
</script>

<style scoped>
img.logo {
  height: 1rem;
}

button.bg-white {
  background-color: white !important;
}

button.bg-white:hover {
  background-color: #343a40 !important;
}

button.bg-white.disabled,
button.bg-white:disabled {
  background-color: white !important;
}

button.bg-white:not(:disabled):not(.disabled):active,
button.bg-white:not(:disabled):not(.disabled).active,
.show > .btn-outline-dark.dropdown-toggle {
  background-color: #343a40 !important;
}

#menu {
  position: absolute;
  z-index: 1000;
}

#header {
  background-color: #ffffff;
  border-width: 0px 0px 1px 0px;
  border-style: solid;
  border-color: #d7d7d7;
}

.grayscale {
  filter: grayscale(100%);
}

#overlay {
  cursor: default;
  background-color: #666666;
  position: fixed;
  width: 100%;
  height: 100%;
  top: 0px;
  left: 0px;
  z-index: 10;
  opacity: 0.2;
}
</style>
