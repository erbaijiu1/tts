<script>
export default {
  onLaunch: function () {
    console.log('App Launch');
  },
  onShow: function () {
    console.log('App Show');
  },
  onHide: function () {
    console.log('App Hide');
  },
}
</script>

<style>
/* Global design system */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background-color: #0d1117;
  color: #e6edf3;
  font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* Base style resets for uni-app components in H5 */
uni-page-body {
  height: 100%;
}
</style>
