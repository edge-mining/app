import { computed, ref } from 'vue'

export const useLoader = () => {
  const loaderSemaphore = ref(0)

  const isLoading = computed(() => loaderSemaphore.value != 0)

  function show() {
    loaderSemaphore.value++
  }

  function hide() {
    if (loaderSemaphore.value > 0) {
      loaderSemaphore.value--
    }
  }

  return {
    isLoading,
    show,
    hide
  }
}
