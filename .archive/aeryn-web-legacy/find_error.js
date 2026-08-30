const fs = require('fs');
const path = require('path');
const nextDir = 'node_modules/next/dist';
const files = fs.readdirSync(nextDir).filter(f => f.endsWith('.js'));
for (const f of files) {
  const content = fs.readFileSync(path.join(nextDir, f), 'utf8');
  if (content.includes("doesn't exist")) {
    const idx = content.indexOf("doesn't exist");
    console.log('FILE:', f);
    console.log(content.substring(Math.max(0, idx-100), idx+100));
    console.log('---');
  }
}
