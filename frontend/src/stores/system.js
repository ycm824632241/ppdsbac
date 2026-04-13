import { defineStore } from 'pinia'
import { setupApi } from '../api/index.js'

export const useSystemStore = defineStore('system', {
  state: () => ({
    initialized: false, hasRA: false, hasTA: false,
    numAAs: 0, users: [],
  }),
  actions: {
    async refresh() {
      try {
        const { data } = await setupApi.state()
        this.initialized = data.has_params
        this.hasRA = data.has_ra
        this.hasTA = data.has_ta
        this.numAAs = data.num_aas
        this.users = data.users
      } catch (_) {}
    }
  }
})
