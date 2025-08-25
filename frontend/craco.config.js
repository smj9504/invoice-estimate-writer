// Use environment variable or default to localhost:8000
const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
      },
    },
    setupMiddlewares: (middlewares, devServer) => {
      // Custom middleware configuration here if needed
      return middlewares;
    },
  },
};