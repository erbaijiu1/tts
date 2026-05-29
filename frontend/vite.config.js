import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

const PROJECT_NAME = process.env.PROJECT_NAME || 'tts';
const APP_PORT = process.env.APP_PORT || '8009';

export default defineConfig({
  plugins: [vue()],
  // 必须配置 base 使得打包后的静态资源路径正确匹配 /{project_name}/html/
  base: `/${PROJECT_NAME}/html/`,
  server: {
    port: 3000,
    proxy: {
      // 本地开发代理转发
      [`/${PROJECT_NAME}/api`]: {
        target: `http://localhost:${APP_PORT}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(new RegExp(`^/${PROJECT_NAME}/api`), `/${PROJECT_NAME}/api`)
      },
      [`/${PROJECT_NAME}/static`]: {
        target: `http://localhost:${APP_PORT}`,
        changeOrigin: true
      }
    }
  }
});
