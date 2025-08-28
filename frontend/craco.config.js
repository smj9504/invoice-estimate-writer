const path = require('path');

module.exports = {
  // Webpack configuration
  webpack: {
    configure: (webpackConfig) => {
      // Set public path for proper routing
      webpackConfig.output.publicPath = '/';
      return webpackConfig;
    },
  },
  // Dev server configuration
  devServer: {
    port: 3000,
    hot: true,
    historyApiFallback: {
      index: '/index.html',
      disableDotRule: true,
    },
  },
};