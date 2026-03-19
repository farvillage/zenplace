/**
 * ZenPlace — Express server
 *
 * Serves the frontend static files.
 * The API key must be in a .env file (never commit it to the repository).
 *
 * To run:
 *   npm install
 *   echo "PORT=4001" > .env
 *   node server.js
 */

require('dotenv').config();

const express = require('express');
const path    = require('path');

const PORT = process.env.PORT || 4001;
const app  = express();

// Serve all static files from the root folder
app.use(express.static(__dirname));

// Fallback: any unmatched route returns index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ ZenPlace running at http://localhost:${PORT}`);
});
