// ═══════════════════════════════════════════════════════════════
// CSV PARSER FOR F1 25 RESULTS
// Parses session_results CSV files from F1 25
// ═══════════════════════════════════════════════════════════════

/**
 * Parse F1 25 CSV file content
 * @param {string} csvContent - Raw CSV file content
 * @returns {Object} Parsed race data with results and incidents
 */
export function parseF125CSV(csvContent) {
    const lines = csvContent.split('\n').map(line => line.trim()).filter(line => line);

    let raceResults = [];
    let incidents = [];
    let parsingResults = true;

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];

        // Empty line indicates switch from results to incidents
        if (line === '' || line === '""') {
            parsingResults = false;
            continue;
        }

        // Check if this is the incidents header
        if (line.includes('"Time","Lap","Driver","Team","Incident","Penalty"')) {
            parsingResults = false;
            i++; // Skip header
            continue;
        }

        if (parsingResults) {
            const result = parseResultLine(line);
            if (result) {
                raceResults.push(result);
            }
        } else {
            const incident = parseIncidentLine(line);
            if (incident) {
                incidents.push(incident);
            }
        }
    }

    return {
        results: raceResults,
        incidents: incidents
    };
}

/**
 * Parse a single race result line
 * Format: "Pos.","Driver","Team","Grid","Stops","Best","Time","Pts.","driver type"
 */
function parseResultLine(line) {
    const values = parseCSVLine(line);

    if (values.length < 9) return null;

    const position = parseInt(values[0]) || 0;
    const driver = values[1];
    const team = values[2];
    const grid = parseInt(values[3]) || 0;
    const stops = parseInt(values[4]) || 0;
    const bestLap = values[5];
    const time = values[6];
    const points = parseInt(values[7]) || 0;
    const driverType = values[8];

    // Skip if not a valid position
    if (!position || !driver || driver === 'Driver') return null;

    return {
        position,
        driver,
        team,
        grid,
        stops,
        bestLap,
        time,
        points,
        driverType,
        dnf: time === 'DNF',
        dsq: time === 'DSQ'
    };
}

/**
 * Parse a single incident line
 * Format: "Time","Lap","Driver","Team","Incident","Penalty"
 */
function parseIncidentLine(line) {
    const values = parseCSVLine(line);

    if (values.length < 6) return null;

    const time = values[0];
    const lap = parseInt(values[1]) || 0;
    const driver = values[2];
    const team = values[3];
    const incident = values[4];
    const penalty = values[5];

    // Skip header or invalid lines
    if (!lap || driver === 'Driver') return null;

    return {
        time,
        lap,
        driver,
        team,
        incident,
        penalty
    };
}

/**
 * Parse CSV line handling quoted values
 */
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }

    values.push(current.trim());
    return values;
}

/**
 * Calculate championship points based on F1 2025 system
 */
export function calculateChampionshipPoints(position, hasFastestLap = false) {
    const pointsSystem = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1];

    let points = 0;

    // Base points for finishing position
    if (position >= 1 && position <= 10) {
        points = pointsSystem[position - 1];
    }

    // Fastest lap bonus (only if finished in top 10)
    if (hasFastestLap && position <= 10) {
        points += 1;
    }

    return points;
}

/**
 * Find fastest lap from results
 */
export function findFastestLap(results) {
    let fastest = null;
    let fastestTime = Infinity;

    for (const result of results) {
        if (result.dnf || result.dsq || result.bestLap === '--:--.---') continue;

        const lapTime = convertLapTimeToSeconds(result.bestLap);
        if (lapTime < fastestTime) {
            fastestTime = lapTime;
            fastest = result.driver;
        }
    }

    return fastest;
}

/**
 * Convert lap time string to seconds
 * Format: "1:30.347" -> 90.347
 */
function convertLapTimeToSeconds(lapTime) {
    if (!lapTime || lapTime === '--:--.---') return Infinity;

    const parts = lapTime.split(':');
    if (parts.length !== 2) return Infinity;

    const minutes = parseInt(parts[0]) || 0;
    const seconds = parseFloat(parts[1]) || 0;

    return minutes * 60 + seconds;
}

/**
 * Validate CSV content
 */
export function validateCSV(csvContent) {
    if (!csvContent || typeof csvContent !== 'string') {
        return { valid: false, error: 'Invalid CSV content' };
    }

    const lines = csvContent.split('\n');
    if (lines.length < 2) {
        return { valid: false, error: 'CSV is empty or too short' };
    }

    // Check for expected header
    const header = lines[0];
    if (!header.includes('Pos.') || !header.includes('Driver')) {
        return { valid: false, error: 'Invalid CSV format - missing expected headers' };
    }

    return { valid: true };
}

/**
 * Extract race metadata from filename or content
 * Example: "session_results_12012026_2225.csv" -> Date
 */
export function extractRaceMetadata(filename) {
    const dateMatch = filename.match(/session_results_(\d{8})_(\d{4})\.csv/);

    if (dateMatch) {
        const dateStr = dateMatch[1]; // e.g., "12012026"
        const timeStr = dateMatch[2]; // e.g., "2225"

        // Parse date: DDMMYYYY
        const day = dateStr.substring(0, 2);
        const month = dateStr.substring(2, 4);
        const year = dateStr.substring(4, 8);

        const date = new Date(`${year}-${month}-${day}`);

        return {
            date: date.toISOString().split('T')[0],
            time: `${timeStr.substring(0, 2)}:${timeStr.substring(2, 4)}`,
            timestamp: date.getTime()
        };
    }

    return {
        date: new Date().toISOString().split('T')[0],
        time: '00:00',
        timestamp: Date.now()
    };
}
