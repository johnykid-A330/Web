// ═══════════════════════════════════════════════════════════════
// STANDINGS & CHAMPIONSHIP CALCULATIONS
// Manages championship standings, points, and statistics
// ═══════════════════════════════════════════════════════════════

/**
 * Calculate and return current championship standings
 * @param {Array} races - Array of race objects
 * @param {Array} drivers - Array of registered drivers
 * @returns {Array} Sorted standings
 */
export function calculateStandings(races, drivers) {
    const driverStats = {};

    // Initialize stats for all registered drivers
    drivers.forEach(driver => {
        driverStats[driver.discord_name] = {
            name: driver.discord_name,
            team: driver.team || 'No Team',
            ea_id: driver.ea_id,
            totalPoints: 0,
            races: 0,
            wins: 0,
            podiums: 0,
            dnfs: 0,
            bestFinish: null,
            fastestLaps: 0
        };
    });

    // Process each race
    races.forEach(race => {
        race.results.forEach(result => {
            const driverName = result.driver;

            // Initialize if driver not registered
            if (!driverStats[driverName]) {
                driverStats[driverName] = {
                    name: driverName,
                    team: result.team,
                    ea_id: 'N/A',
                    totalPoints: 0,
                    races: 0,
                    wins: 0,
                    podiums: 0,
                    dnfs: 0,
                    bestFinish: null,
                    fastestLaps: 0
                };
            }

            const stats = driverStats[driverName];

            // Add points
            stats.totalPoints += result.points;
            stats.races++;

            // Track achievements
            if (!result.dnf && !result.dsq) {
                if (result.position === 1) stats.wins++;
                if (result.position <= 3) stats.podiums++;

                // Best finish
                if (stats.bestFinish === null || result.position < stats.bestFinish) {
                    stats.bestFinish = result.position;
                }
            } else {
                stats.dnfs++;
            }

            // Fastest laps
            if (result.hasFastestLap) {
                stats.fastestLaps++;
            }
        });
    });

    // Convert to array and sort
    const standings = Object.values(driverStats);

    standings.sort((a, b) => {
        // Primary: Total points
        if (b.totalPoints !== a.totalPoints) {
            return b.totalPoints - a.totalPoints;
        }

        // Tiebreaker 1: Wins
        if (b.wins !== a.wins) {
            return b.wins - a.wins;
        }

        // Tiebreaker 2: Podiums
        if (b.podiums !== a.podiums) {
            return b.podiums - a.podiums;
        }

        // Tiebreaker 3: Best finish
        if (a.bestFinish !== b.bestFinish) {
            if (a.bestFinish === null) return 1;
            if (b.bestFinish === null) return -1;
            return a.bestFinish - b.bestFinish;
        }

        return 0;
    });

    return standings;
}

/**
 * Get driver statistics
 */
export function getDriverStats(driverName, races) {
    const stats = {
        name: driverName,
        raceResults: [],
        totalPoints: 0,
        avgPosition: 0,
        consistency: 0
    };

    let positionSum = 0;
    let finishedRaces = 0;

    races.forEach(race => {
        const result = race.results.find(r => r.driver === driverName);
        if (result) {
            stats.raceResults.push({
                raceName: race.name,
                date: race.date,
                position: result.position,
                points: result.points,
                team: result.team,
                dnf: result.dnf,
                dsq: result.dsq
            });

            stats.totalPoints += result.points;

            if (!result.dnf && !result.dsq) {
                positionSum += result.position;
                finishedRaces++;
            }
        }
    });

    if (finishedRaces > 0) {
        stats.avgPosition = (positionSum / finishedRaces).toFixed(1);

        // Calculate consistency (lower standard deviation = more consistent)
        const positions = stats.raceResults
            .filter(r => !r.dnf && !r.dsq)
            .map(r => r.position);

        if (positions.length > 1) {
            const mean = stats.avgPosition;
            const variance = positions.reduce((sum, pos) => sum + Math.pow(pos - mean, 2), 0) / positions.length;
            stats.consistency = Math.sqrt(variance).toFixed(1);
        }
    }

    return stats;
}

/**
 * Get team standings (constructor championship)
 */
export function calculateTeamStandings(races) {
    const teamPoints = {};

    races.forEach(race => {
        race.results.forEach(result => {
            const team = result.team;

            if (!teamPoints[team]) {
                teamPoints[team] = {
                    name: team,
                    points: 0,
                    wins: 0,
                    podiums: 0
                };
            }

            teamPoints[team].points += result.points;

            if (!result.dnf && !result.dsq) {
                if (result.position === 1) teamPoints[team].wins++;
                if (result.position <= 3) teamPoints[team].podiums++;
            }
        });
    });

    // Convert to array and sort
    const standings = Object.values(teamPoints);
    standings.sort((a, b) => {
        if (b.points !== a.points) return b.points - a.points;
        if (b.wins !== a.wins) return b.wins - a.wins;
        return b.podiums - a.podiums;
    });

    return standings;
}

/**
 * Get recent race winner
 */
export function getRecentWinner(races) {
    if (races.length === 0) return null;

    // Get most recent race
    const sortedRaces = [...races].sort((a, b) => {
        return new Date(b.date) - new Date(a.date);
    });

    const recentRace = sortedRaces[0];
    const winner = recentRace.results.find(r => r.position === 1);

    return {
        raceName: recentRace.name,
        date: recentRace.date,
        winner: winner ? winner.driver : 'Unknown',
        team: winner ? winner.team : 'Unknown'
    };
}

/**
 * Get top 3 podium from standings
 */
export function getPodium(standings) {
    return standings.slice(0, 3);
}

/**
 * Calculate points difference from leader
 */
export function calculateGapToLeader(standings) {
    if (standings.length === 0) return standings;

    const leaderPoints = standings[0].totalPoints;

    return standings.map(driver => ({
        ...driver,
        gapToLeader: leaderPoints - driver.totalPoints
    }));
}
