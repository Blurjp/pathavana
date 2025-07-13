module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Disable hot module replacement
      webpackConfig.optimization = {
        ...webpackConfig.optimization,
        runtimeChunk: false,
      };
      
      // Disable dev server hot reload
      if (webpackConfig.devServer) {
        webpackConfig.devServer.hot = false;
        webpackConfig.devServer.liveReload = false;
        webpackConfig.devServer.webSocketServer = false;
        webpackConfig.devServer.client = {
          ...webpackConfig.devServer.client,
          overlay: false,
          webSocketURL: 'ws://0.0.0.0:0/ws',
        };
      }
      
      // Remove hot module replacement plugin
      webpackConfig.plugins = webpackConfig.plugins.filter(
        plugin => plugin.constructor.name !== 'HotModuleReplacementPlugin'
      );
      
      return webpackConfig;
    },
  },
  devServer: {
    hot: false,
    liveReload: false,
    webSocketServer: false,
    client: {
      overlay: false,
      webSocketURL: 'ws://0.0.0.0:0/ws',
    },
  },
};