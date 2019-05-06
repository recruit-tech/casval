<template>
  <div>
    <div class="container py-5">
      <div class="row">
        <div class="col">
          <div class="card">
            <div class="card-body">
              <div class="h5">{{ $t('audit.register-new-audit') }}</div>
              <hr class="mb-2" />
              <audit-registration-form :audit-api-client="auditApiClient"></audit-registration-form>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="container pb-5">
      <div class="row">
        <div class="col">
          <div class="card">
            <div class="card-body">
              <div class="h5 mb-3">{{ $t('audit.ongoing') }}</div>
              <audit-list
                :audit-api-client="auditApiClient"
                :submitted="false"
                :approved="false"
                @columnUpdated="reloadAuditList"
                ref="auditListOngoing"
              ></audit-list>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="container pb-5">
      <div class="row">
        <div class="col">
          <div class="card">
            <div class="card-body">
              <div class="h5 mb-3">{{ $t('audit.completed') }}</div>
              <audit-list
                :audit-api-client="auditApiClient"
                :submitted="true"
                :approved="false"
                @columnUpdated="reloadAuditList"
                ref="auditListCompleted"
              ></audit-list>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="container pb-5">
      <div class="row">
        <div class="col">
          <div class="card">
            <div class="card-body">
              <div class="h5 mb-3">{{ $t('audit.approved') }}</div>
              <audit-list
                :audit-api-client="auditApiClient"
                :submitted="true"
                :approved="true"
                @columnUpdated="reloadAuditList"
                ref="auditListApproved"
              ></audit-list>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AuditList from './AuditList.vue';
import AuditRegistrationForm from './AuditRegistrationForm.vue';

export default {
  name: 'AuditManagement',
  props: {
    auditApiClient: {
      type: Function,
      required: true
    }
  },
  components: {
    AuditList,
    AuditRegistrationForm
  },

  methods: {
    reloadAuditList: function reloadAuditList(reason) {
      switch (reason) {
        case 'withdrawn':
          this.$refs.auditListOngoing.loadAuditIndex(1);
          break;
        case 'rescinded':
          this.$refs.auditListCompleted.loadAuditIndex(1);
          break;
        case 'approved':
          this.$refs.auditListApproved.loadAuditIndex(1);
          break;
        default:
      }
    }
  }
};
</script>
