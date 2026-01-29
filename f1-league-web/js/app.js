// ═══════════════════════════════════════════════════════════════
// AUTH & ROUTING GUARD
// ═══════════════════════════════════════════════════════════════

// Auth guard removed for server-side auth integration.
// Public access enabled.

// ═══════════════════════════════════════════════════════════════
// MAIN APPLICATION LOGIC
// Data management, rendering, and app coordination
// ═══════════════════════════════════════════════════════════════

import { parseF125CSV, validateCSV, extractRaceMetadata, findFastestLap } from './csv-parser.js';
import { calculateStandings, getDriverStats, calculateTeamStandings, getPodium, calculateGapToLeader } from './standings.js';

// Data storage keys
const STORAGE_KEYS = {
  DRIVERS: 'f1_league_drivers',
  RACES: 'f1_league_races',
  CONFIG: 'f1_league_config',
  LEAGUE_MODE: 'f1_league_mode' // 'Main' or 'Academy'
};

// ═══════════════════════════════════════════════════════════════
// DATA MANAGEMENT
// ═══════════════════════════════════════════════════════════════

/**
 * Load data from localStorage
 */
export function loadData(key) {
  try {
    const data = localStorage.getItem(STORAGE_KEYS[key]);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error('Error loading data:', error);
    return null;
  }
}

/**
 * Save data to localStorage
 */
export function saveData(key, data) {
  try {
    localStorage.setItem(STORAGE_KEYS[key], JSON.stringify(data));
    return true;
  } catch (error) {
    console.error('Error saving data:', error);
    return false;
  }
}

/**
 * Get current league mode (Main or Academy)
 */
export function getLeagueMode() {
  return localStorage.getItem(STORAGE_KEYS.LEAGUE_MODE) || 'Main';
}

/**
 * Set league mode
 */
export function setLeagueMode(mode) {
  localStorage.setItem(STORAGE_KEYS.LEAGUE_MODE, mode);
  window.location.reload(); // Reload to refresh data
}

/**
 * Initialize default data structure
 */
export function initializeData() {
  if (!loadData('DRIVERS')) {
    saveData('DRIVERS', []);
  }

  if (!loadData('RACES')) {
    saveData('RACES', []);
  }

  if (!loadData('CONFIG')) {
    const defaultConfig = {
      leagueName: 'Renegade Racing League',
      season: 'Season 1',
      pointsSystem: [25, 18, 15, 12, 10, 8, 6, 4, 2, 1],
      fastestLapBonus: 1
    };
    saveData('CONFIG', defaultConfig);
  }
}

/**
 * Add a new driver
 */
export async function addDriver(driverData) {
  // Deprecated: usage should be via /api/register
  console.warn('addDriver via app.js is deprecated, use /api/register');
  return driverData;
}

/**
 * Remove a driver (Admin function)
 */
export function removeDriver(driverId) {
  const drivers = loadData('DRIVERS') || [];
  const updatedDrivers = drivers.filter(d => d.id !== driverId);

  if (drivers.length === updatedDrivers.length) {
    return false; // Driver not found
  }

  saveData('DRIVERS', updatedDrivers);
  return true;
}

/**
 * Add a new race from CSV
 */
export async function addRaceFromCSV(csvContent, filename, raceName) {
  const validation = validateCSV(csvContent);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const parsed = parseF125CSV(csvContent);
  const metadata = extractRaceMetadata(filename);
  const fastestLapDriver = findFastestLap(parsed.results);
  const currentLeague = getLeagueMode();

  // Mark fastest lap
  parsed.results.forEach(result => {
    result.hasFastestLap = result.driver === fastestLapDriver;
  });

  const race = {
    id: generateId(),
    name: raceName || `Race ${metadata.date}`,
    date: metadata.date,
    time: metadata.time,
    league: currentLeague, // Tag race with league
    results: parsed.results,
    incidents: parsed.incidents || [],
    fastestLap: fastestLapDriver,
    originalFilename: filename
  };

  try {
    const res = await fetch('/api/races', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(race)
    });
    if (!res.ok) throw new Error('Failed to save to server');
  } catch (e) {
    console.error('API Error', e);
    throw e;
  }

  const races = loadData('RACES') || [];
  races.push(race);
  saveData('RACES', races);

  return race;
}

/**
 * Get all drivers (filtered by current league)
 */
export function getDrivers() {
  const drivers = loadData('DRIVERS') || [];
  const currentLeague = getLeagueMode();
  return drivers.filter(d => d.league === currentLeague);
}

/**
 * Get all races (filtered by current league)
 */
export function getRaces() {
  const races = loadData('RACES') || [];
  const currentLeague = getLeagueMode();
  return races.filter(r => r.league === currentLeague);
}

/**
 * Get config
 */
export function getConfig() {
  return loadData('CONFIG') || {};
}

/**
 * Generate unique ID
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// ═══════════════════════════════════════════════════════════════
// RENDERING FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Render League Switcher
 */
export function renderLeagueSwitcher() {
  const navContainer = document.querySelector('nav .container');
  if (!navContainer) return;

  const currentMode = getLeagueMode();

  // Create switcher element if not exists
  let switcher = document.getElementById('league-switcher');
  if (!switcher) {
    switcher = document.createElement('div');
    switcher.id = 'league-switcher';
    switcher.className = 'league-switcher';

    // Insert after logo
    const logo = navContainer.querySelector('.logo');
    logo.after(switcher);
  }

  switcher.innerHTML = `
    <select onchange="window.switchLeague(this.value)" class="league-select">
      <option value="Main" ${currentMode === 'Main' ? 'selected' : ''}>🏆 Main League</option>
      <option value="Academy" ${currentMode === 'Academy' ? 'selected' : ''}>🎓 Academy</option>
    </select>
  `;

  // Expose switch function globally
  window.switchLeague = (mode) => {
    setLeagueMode(mode);
  };
}

/**
 * Render standings table
 */
export function renderStandingsTable(containerId) {
  const drivers = getDrivers();
  const races = getRaces();
  const standings = calculateStandings(races, drivers);
  const standingsWithGap = calculateGapToLeader(standings);

  const container = document.getElementById(containerId);
  if (!container) return;

  let html = `
    <table class="standings-table">
      <thead>
        <tr>
          <th>POZ</th>
          <th>JEZDEC</th>
          <th>TÝM</th>
          <th>ZÁVODY</th>
          <th>VÝHRY</th>
          <th>PODIA</th>
          <th>BODY</th>
        </tr>
      </thead>
      <tbody>
  `;

  standingsWithGap.forEach((driver, index) => {
    const position = index + 1;
    const positionClass = position <= 3 ? `p${position}` : '';
    const initial = driver.name.charAt(0).toUpperCase();

    html += `
      <tr>
        <td>
          <div class="position-badge ${positionClass}">${position}</div>
        </td>
        <td>
          <div class="driver-info">
            <div class="driver-avatar">${initial}</div>
            <div>
              <div class="driver-name">${driver.name}</div>
              <div class="driver-team">${driver.team}</div>
            </div>
          </div>
        </td>
        <td>${driver.team}</td>
        <td>${driver.races}</td>
        <td>${driver.wins}</td>
        <td>${driver.podiums}</td>
        <td><span class="points">${driver.totalPoints}</span></td>
      </tr>
    `;
  });

  if (standingsWithGap.length === 0) {
    html += `<tr><td colspan="7" class="text-center p-3 text-muted">V této lize zatím nejsou žádní jezdci.</td></tr>`;
  }

  html += `
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}

/**
 * Render podium
 */
export function renderPodium(containerId) {
  const drivers = getDrivers();
  const races = getRaces();
  const standings = calculateStandings(races, drivers);
  const podium = getPodium(standings);

  const container = document.getElementById(containerId);
  if (!container) return;

  if (podium.length === 0) {
    container.innerHTML = '<p class="text-center text-muted">Zatím žádná data pro podium</p>';
    return;
  }

  const html = `
    <div class="podium-container">
      ${podium.map((driver, index) => {
    const position = index + 1;
    const initial = driver.name.charAt(0).toUpperCase();

    return `
          <div class="podium-position p${position}">
            <div class="podium-driver">
              <div class="podium-rank">${position}</div>
              <div class="driver-info">
                <div class="driver-avatar">${initial}</div>
                <div>
                  <div class="driver-name">${driver.name}</div>
                  <div class="driver-team">${driver.team}</div>
                </div>
              </div>
              <div class="points mt-1">${driver.totalPoints} pts</div>
            </div>
            <div class="podium-base">${position}</div>
          </div>
        `;
  }).join('')}
    </div>
  `;

  container.innerHTML = html;
}

/**
 * Render race results
 */
export function renderRaceResults(containerId) {
  const races = getRaces();
  const container = document.getElementById(containerId);
  if (!container) return;

  // Sort races by date (newest first)
  const sortedRaces = [...races].sort((a, b) => new Date(b.date) - new Date(a.date));

  if (sortedRaces.length === 0) {
    container.innerHTML = `<p class="text-muted text-center card">V lize ${getLeagueMode()} zatím nejsou žádné závody.</p>`;
    return;
  }

  let html = '';

  sortedRaces.forEach(race => {
    html += `
      <div class="card mb-2">
        <div class="card-header">
          <div>
            <h3 class="card-title">${race.name}</h3>
            <p class="text-muted">${formatDate(race.date)}</p>
          </div>
          <div class="text-muted">${race.results.length} jezdců</div>
        </div>
        
        <table class="standings-table">
          <thead>
            <tr>
              <th>POZ</th>
              <th>JEZDEC</th>
              <th>TÝM</th>
              <th>ČAS</th>
              <th>BEST LAP</th>
              <th>BODY</th>
            </tr>
          </thead>
          <tbody>
            ${race.results.map(result => `
              <tr>
                <td><div class="position-badge">${result.position}</div></td>
                <td>
                  <div class="driver-name">
                    ${result.driver}
                    ${result.hasFastestLap ? '<span style="color: var(--f1-orange);">⚡</span>' : ''}
                  </div>
                </td>
                <td>${result.team}</td>
                <td>${result.time}</td>
                <td>${result.bestLap}</td>
                <td><span class="points">${result.points}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  });

  container.innerHTML = html;
}

/**
 * Render driver list with Admin actions
 */
export function renderDriverList(containerId) {
  const drivers = getDrivers();
  const races = getRaces();
  const container = document.getElementById(containerId);
  if (!container) return;

  const standings = calculateStandings(races, drivers);

  if (standings.length === 0) {
    container.innerHTML = `<p class="text-muted text-center">V lize ${getLeagueMode()} zatím nejsou žádní registrovaní jezdci.</p>`;
    return;
  }

  let html = '<div class="grid grid-2">';

  // Get current user for permissions
  const user = JSON.parse(localStorage.getItem('f1_league_user') || '{}');
  const isAdmin = user.isAdmin;

  standings.forEach(driver => {
    // Najdeme original ID drivera pro mazání (standings objekt ho nemusí mít přímo, pokud byl generován dynamicky)
    // Proto v standings.js bychom měli zajistit, že id je předáváno, nebo ho najdeme tady:
    const originalDriver = drivers.find(d => d.discord_name === driver.name);
    const driverId = originalDriver ? originalDriver.id : null;

    const initial = driver.name.charAt(0).toUpperCase();

    // Admin Kick Button HTML
    const kickButton = isAdmin
      ? `<button onclick="window.confirmKick('${driverId}', '${driver.name}')" class="btn-kick" title="Vyhodit jezdce">🗑️</button>`
      : '';

    html += `
      <div class="card relative">
        <div class="driver-info mb-1">
          <div class="driver-avatar" style="width: 60px; height: 60px; font-size: 1.5rem;">${initial}</div>
          <div>
            <h3 class="driver-name" style="margin: 0;">${driver.name}</h3>
            <p class="driver-team" style="margin: 0;">${driver.team}</p>
          </div>
          
          ${kickButton}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
          <div>
            <div class="text-muted" style="font-size: 0.875rem;">Body</div>
            <div class="points">${driver.totalPoints}</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 0.875rem;">Závody</div>
            <div style="font-weight: 600;">${driver.races}</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 0.875rem;">Výhry</div>
            <div style="font-weight: 600;">${driver.wins}</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 0.875rem;">Podia</div>
            <div style="font-weight: 600;">${driver.podiums}</div>
          </div>
        </div>
      </div>
    `;
  });

  html += '</div>';

  container.innerHTML = html;

  // Expose kick functionality
  window.confirmKick = (id, name) => {
    if (confirm(`Opravdu chcete vyhodit jezdce ${name} z ligy ${getLeagueMode()}?`)) {
      if (removeDriver(id)) {
        window.location.reload();
      } else {
        alert('Chyba: Jezdec nenalezen.');
      }
    }
  };
}

/**
 * Format date
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('cs-CZ', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// Initialize data and UI
initializeData();
renderLeagueSwitcher();

// ═══════════════════════════════════════════════════════════════
// DATA SYNC & INITIALIZATION
// ═══════════════════════════════════════════════════════════════

export async function syncData() {
  try {
    const [driversRes, racesRes] = await Promise.all([
      fetch('/api/players'),
      fetch('/api/races')
    ]);

    const drivers = await driversRes.json();
    const races = await racesRes.json();

    saveData('DRIVERS', drivers);
    saveData('RACES', races);

    checkAdminStatus();

    // Re-render UI with fresh data
    if (document.getElementById('standings-table')) renderStandingsTable('standings-table');
    if (document.getElementById('driver-list')) renderDriverList('driver-list');
    if (document.getElementById('race-results')) renderRaceResults('race-results');

    return true;
  } catch (error) {
    console.error('Data Sync Error:', error);
    return false;
  }
}

async function checkAdminStatus() {
  try {
    const res = await fetch('/api/admin/check');
    const { isAdmin } = await res.json();

    const navMenu = document.getElementById('nav-menu');
    if (navMenu && isAdmin) {
      // Show Upload link
      const links = navMenu.getElementsByTagName('li');
      for (let li of links) {
        if (li.textContent.includes('Nahrát CSV')) li.style.display = 'block';
      }
      // Show Admin Link
      if (!document.getElementById('admin-link')) {
        const li = document.createElement('li');
        li.id = 'admin-link';
        li.innerHTML = '<a href="admin.html" style="color: #ff4444;">Admin Panel</a>';
        navMenu.appendChild(li);
      }
    }
  } catch (e) { }
}

// Auto-sync on load
(async function init() {
  await syncData();
})();
