<template>
  <div class="container-fluid h-100 bg-dark">
    <div class="row align-items-center h-100">
      <div class="col text-center">
        <img src="../assets/logo-white.svg" class="logo mb-4" />
        <div class="text-light message">
          <font-awesome-icon icon="check-circle" v-if="status === 'loaded'"></font-awesome-icon>
          <font-awesome-icon icon="spinner" pulse v-else-if="status === 'loading'"></font-awesome-icon>
          <font-awesome-icon icon="exclamation-circle" v-else></font-awesome-icon>
          {{ $t(`entrance.status.${status}`) }}
        </div>
        <form @submit.prevent :class="status === 'restricted-by-password' ? 'visible' : 'invisible'">
          <div class="form-row align-items-center">
            <div class="col"></div>
            <div class="col-auto">
              <input
                type="password"
                class="form-control"
                name="password"
                :placeholder="$t('entrance.password')"
                v-model="password"
              />
            </div>
            <div class="col-auto">
              <button type="submit" class="btn btn-light" @click="generateToken">{{ $t('entrance.open') }}</button>
            </div>
            <div class="col"></div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Entrance',
  props: {
    status: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      password: ''
    };
  },
  methods: {
    generateToken: async function generateToken() {
      window.eventBus.$emit('TOKEN_REQUESTED', this.password);
      this.password = '';
    }
  },
  created: function created() {
    this.generateToken();
  }
};
</script>

<style scoped>
div.message {
  height: 2rem;
}
img.logo {
  height: 2rem;
}
</style>
