const next = require('next');
console.log('Next:', next.version || 'unknown');
console.log('Turbopack:', process.env.TURBOPACK ? 'enabled' : 'check next.config');
