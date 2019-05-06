<template>
  <div id="modal-contacts" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('home.modal.contacts.title') }}</h5>
          <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('home.modal.contacts.message') }}<br />
            <small class="form-text text-danger">{{ errorMessage }}</small>
          </p>
          <div class="py-1">
            <div class="row pb-2" v-for="(contact, index) in contacts" :key="index">
              <div class="col-4">
                <input
                  class="form-control form-control-sm"
                  v-model="contact.name"
                  :placeholder="$t('home.modal.contacts.name')"
                  @keydown="addInputForm(index)"
                />
              </div>
              <div class="col">
                <input
                  class="form-control form-control-sm"
                  v-model="contact.email"
                  value=""
                  :placeholder="$t('home.modal.contacts.email')"
                  @keydown="addInputForm(index)"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            {{ $t('home.modal.contacts.cancel') }}
          </button>
          <button type="button" class="btn btn-primary" @click="changeContacts">
            {{ $t('home.modal.contacts.ok') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from 'jquery';
import 'bootstrap';

export default {
  name: 'ModalContacts',
  props: {
    audit: {
      type: Object,
      required: true
    },
    auditApiClient: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      contacts: this.audit.contacts,
      errorMessage: ''
    };
  },
  methods: {
    addInputForm: function addInputForm(index) {
      if (index + 1 === this.contacts.length) {
        this.contacts.push({ name: '', email: '' });
      }
    },
    changeContacts: async function changeContacts() {
      this.errorMessage = '';

      // eslint-disable-next-line arrow-body-style
      const filteredContacts = this.contacts.filter(item => {
        return item.name.length > 0 || item.email.length > 0;
      });

      filteredContacts.forEach(item => {
        const emailValidation = /^[\w.-]+@([\w-]+.)+\w+$/;
        if (item.email.length === 0) {
          this.errorMessage = this.$i18n.t('home.modal.contacts.error-no-email', { name: item.name });
        } else if (!emailValidation.test(item.email)) {
          this.errorMessage = this.$i18n.t('home.modal.contacts.error-invalid-email', { email: item.email });
        }
      });

      if (filteredContacts.length === 0) {
        this.errorMessage = this.$i18n.t('home.modal.contacts.error-no-name');
      }

      if (this.errorMessage.length > 0) {
        return;
      }

      try {
        const res = await this.auditApiClient.patch('/', {
          contacts: filteredContacts
        });
        switch (res.status) {
          case 200:
            this.errorMessage = '';
            $('#modal-contacts').modal('hide');
            break;
          default:
            this.errorMessage = this.$i18n.t('home.modal.contacts.error-general');
        }
      } catch (e) {
        this.errorMessage = this.$i18n.t('home.modal.contacts.error-general');
      }
    }
  },
  created: function created() {
    this.contacts.push({ name: '', email: '' });
  }
};
</script>
