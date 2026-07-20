import { createApp } from 'vue';
import App from './App.vue';

// 登录过期时统一回到 SSO，并在登录成功后返回当前页面。
const nativeFetch = window.fetch.bind(window);
window.fetch = async (...args) => {
  const response = await nativeFetch(...args);
  if (response.status === 401) {
    const redirect = `${window.location.pathname}${window.location.search}`;
    window.location.assign(`/sso_auth/html/?redirect=${encodeURIComponent(redirect)}`);
  }
  return response;
};

const app = createApp(App);
app.mount('#app');
