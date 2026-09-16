import { ref } from 'vue'

const toastInstance = ref(null)

export function useToast() {
  const success = (message, duration) => {
    toastInstance.value?.show(message, 'success', duration)
  }

  const error = (message, duration) => {
    toastInstance.value?.show(message, 'error', duration)
  }

  const warning = (message, duration) => {
    toastInstance.value?.show(message, 'warning', duration)
  }

  const info = (message, duration) => {
    toastInstance.value?.show(message, 'info', duration)
  }

  const setInstance = (instance) => {
    toastInstance.value = instance
  }

  return {
    success,
    error,
    warning,
    info,
    setInstance
  }
}
