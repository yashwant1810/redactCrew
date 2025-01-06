module.exports = {
  content: [
    "./index.html",        // Include your main HTML file
    "./src/**/*.{js,jsx,ts,tsx}" ,// Include all your source files
    'node_modules/flowbite-react/lib/esm/**/*.js',
  ],
  theme: {
    extend: {
      
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
};

