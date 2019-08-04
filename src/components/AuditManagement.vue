<template>
  <div>
    <div class="container">
      <div class="row">
        <audit-registration-form :audit-api-client="auditApiClient"></audit-registration-form>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <audit-urgent-list :audit-api-client="auditApiClient"></audit-urgent-list>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <audit-list :audit-api-client="auditApiClient"></audit-list>
      </div>
    </div>
  </div>
</template>

<script>
import AuditList from './AuditList.vue';
import AuditUrgentList from './AuditUrgentList.vue';
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
    AuditUrgentList,
    AuditRegistrationForm
  }
};
</script>
