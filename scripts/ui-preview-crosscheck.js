// Runs the filter logic embedded in the UI preview (the "PURE" block) on a list of filters and
// prints how many events each returns. Used by the backend test that compares it with the API.
//   node scripts/ui-preview-crosscheck.js <index.html> <cases.json>
const fs = require('fs');

const html = fs.readFileSync(process.argv[2], 'utf8');
const cases = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const data = html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const pure = script.slice(0, script.indexOf('// ===== PURE:END'));
const document = { getElementById: () => ({ textContent: data }) };
const api = (0, eval)('(function(document){' + pure + '; return {applyFilters};})')(document);
process.stdout.write(JSON.stringify(cases.map((filters) => api.applyFilters(filters).length)));
