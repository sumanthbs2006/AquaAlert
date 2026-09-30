const http = require('http');
const { spawn } = require('child_process');

// Launch headless chrome
const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  'http://localhost:5173'
]);

setTimeout(async () => {
  try {
    http.get('http://localhost:9222/json', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log('Chrome tabs:', data);
        chrome.kill();
        process.exit(0);
      });
    }).on('error', (err) => {
      console.log('Chrome HTTP error:', err.message);
      chrome.kill();
      process.exit(1);
    });
  } catch (e) {
    console.error(e);
    chrome.kill();
    process.exit(1);
  }
}, 3000);
