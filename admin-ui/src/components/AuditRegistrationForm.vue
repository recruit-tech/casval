<template>
  <div class="col py-5">
    <div class="card">
      <div class="card-body">
        <form @submit.prevent="addAudit">
          <div class="h5">{{ $t('audit.register-new-audit') }}</div>
          <hr class="mb-2" />
          <div class="row pt-3 pb-3">
            <div class="col-2 pt-1 mt-1 text-secondary">
              {{ $t('audit.name') }}
            </div>
            <div class="col">
              <input type="text" class="form-control" v-model="name" :placeholder="$t('audit.name')" />
            </div>
          </div>
          <div class="row pb-3">
            <div class="col-2 pt-1 mt-1 text-secondary">
              {{ $t('audit.description') }}
            </div>
            <div class="col">
              <input type="text" class="form-control" v-model="description" :placeholder="$t('audit.description')" />
            </div>
          </div>
          <div class="row pb-3" v-for="(contact, index) in contacts" :key="index">
            <div class="col-2 pt-1 mt-1 text-secondary">{{ $t('audit.contact') }} {{ index + 1 }}</div>
            <div class="col-4">
              <input
                type="text"
                class="form-control"
                v-model="contact.name"
                :placeholder="$t('audit.contact-name')"
                @keydown="addInputForm(index)"
              />
            </div>
            <div class="col">
              <input
                type="text"
                class="form-control"
                v-model="contact.email"
                :placeholder="$t('audit.contact-email')"
                @keydown="addInputForm(index)"
              />
            </div>
          </div>
          <div class="row">
            <div class="col">
              <small class="text-danger">{{ errorMessage }}</small>
            </div>
          </div>
          <div class="row">
            <div class="col text-right">
              <button class="btn btn-primary" type="submit">{{ $t('audit.register') }}</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuditRegistrationForm',
  props: {
    auditApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      contacts: [{ name: '', email: '' }],
      errorMessage: '',
      name: '',
      description: ''
    };
  },
  methods: {
    addInputForm: function addInputForm(index) {
      if (index + 1 === this.contacts.length) {
        this.contacts.push({ name: '', email: '' });
      }
    },
    addAudit: async function addAudit() {
      this.errorMessage = '';

      if (this.name.length === 0) {
        this.errorMessage = this.$i18n.t('audit.error-no-audit-name');
        return;
      }

      const emailValidation = /^[\w\.-]+@([\w-]+\.)+\w+$/; // eslint-disable-line
      const noEmptyContacts = [];

      this.contacts.forEach(contact => {
        if (contact.name.length === 0 && contact.email.length > 0) {
          this.errorMessage = this.$i18n.t('audit.error-no-name', { email: contact.email });
          return;
        }
        if (contact.name.length > 0 && contact.email.length === 0) {
          this.errorMessage = this.$i18n.t('audit.error-no-email', { name: contact.name });
          return;
        }
        if (contact.name.length > 0 && contact.email.length > 0) {
          if (!emailValidation.test(contact.email)) {
            this.errorMessage = this.$i18n.t('audit.error-invalid-email', { email: contact.email });
            return;
          }
          noEmptyContacts.push(contact);
        }
      });

      if (this.errorMessage.length > 0) {
        return;
      }

      if (noEmptyContacts.length === 0) {
        this.errorMessage = this.$i18n.t('audit.error-no-contact');
        return;
      }

      try {
        const res = await this.auditApiClient.post('/', {
          name: this.name,
          description: this.description,
          contacts: noEmptyContacts
        });
        switch (res.status) {
          case 200: {
            this.contacts = [{ name: '', email: '' }];
            this.errorMessage = '';
            this.name = '';
            this.description = '';
            window.location.reload(true);
            break;
          }
          default: {
            this.errorMessage = this.$i18n.t('audit.error-general');
          }
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('audit.error-general');
      }
    }
  }
};
</script>
