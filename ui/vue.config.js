const PrettierPlugin = require('prettier-webpack-plugin');

module.exports = {
  assetsDir: '',
  lintOnSave: true,
  configureWebpack: {
    plugins: [
      new PrettierPlugin({
        singleQuote: true,
        semi: true,
        tabWidth: 2,
        printWidth: 120
      })
    ]
  }
};
