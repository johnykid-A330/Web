require('dotenv').config();
const express = require('express');
const session = require('express-session');
const passport = require('passport');
const DiscordStrategy = require('passport-discord').Strategy;
const path = require('path');
const fs = require('fs');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000;

// -- Configuration --
const DATA_DIR = path.join(__dirname, '../data');
const PLAYERS_FILE = path.join(DATA_DIR, 'players.json');
const CONFIG_FILE = path.join(DATA_DIR, 'config.json');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// -- Helpers --
function loadPlayers() {
    if (!fs.existsSync(PLAYERS_FILE)) return [];
    try {
        return JSON.parse(fs.readFileSync(PLAYERS_FILE, 'utf8'));
    } catch (e) { return []; }
}

function savePlayers(players) {
    fs.writeFileSync(PLAYERS_FILE, JSON.stringify(players, null, 2));
}

function loadConfig() {
    if (!fs.existsSync(CONFIG_FILE)) return {};
    try {
        return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    } catch (e) { return {}; }
}

// -- Middleware --
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname))); // Serve static files (html, css, js)

app.use(session({
    secret: process.env.SESSION_SECRET || 'super_secret_f1_key',
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false, // Set to true if using HTTPS behind proxy
        maxAge: 7 * 24 * 60 * 60 * 1000 // 1 week
    }
}));

app.use(passport.initialize());
app.use(passport.session());

// -- Passport Setup --
passport.serializeUser((user, done) => {
    done(null, user);
});

passport.deserializeUser((obj, done) => {
    done(null, obj);
});

passport.use(new DiscordStrategy({
    clientID: process.env.DISCORD_CLIENT_ID,
    clientSecret: process.env.DISCORD_CLIENT_SECRET,
    callbackURL: process.env.DISCORD_CALLBACK_URL || 'http://localhost:3000/auth/discord/callback',
    scope: ['identify']
}, (accessToken, refreshToken, profile, done) => {
    return done(null, profile);
}));

// -- Routes --

// Auth Routes
app.get('/auth/discord', passport.authenticate('discord'));

app.get('/auth/discord/callback',
    passport.authenticate('discord', {
        failureRedirect: '/'
    }),
    (req, res) => {
        // Successful login
        res.redirect('/');
    }
);

app.get('/auth/logout', (req, res) => {
    req.logout(() => {
        res.redirect('/');
    });
});

app.get('/api/user', (req, res) => {
    if (req.isAuthenticated()) {
        res.json({
            authenticated: true,
            user: {
                id: req.user.id,
                username: req.user.username,
                global_name: req.user.global_name,
                avatar: req.user.avatar,
                discriminator: req.user.discriminator
            }
        });
    } else {
        res.json({ authenticated: false });
    }
});

// API Routes for Data
app.get('/api/players', (req, res) => {
    res.json(loadPlayers());
});

app.post('/api/register', (req, res) => {
    if (!req.isAuthenticated()) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const { league, team, racing_number, ea_id, bio } = req.body;
    const discordUser = req.user;

    let players = loadPlayers();

    // Check if duplicate number in same league
    if (racing_number) {
        const numberExists = players.some(p =>
            p.league === league &&
            p.racing_number === racing_number &&
            p.discord_id !== discordUser.id
        );
        if (numberExists) {
            return res.status(400).json({ error: 'Startovní číslo je již zabrané.' });
        }
    }

    // Update or Create
    const existingIndex = players.findIndex(p => p.discord_id === discordUser.id);

    const playerData = {
        id: existingIndex >= 0 ? players[existingIndex].id : Date.now().toString(),
        discord_id: discordUser.id,
        discord_name: discordUser.username,
        ea_id: ea_id,
        team: team,
        league: league,
        racing_number: racing_number,
        bio: bio,
        registered_at: new Date().toISOString()
    };

    if (existingIndex >= 0) {
        players[existingIndex] = { ...players[existingIndex], ...playerData };
    } else {
        players.push(playerData);
    }

    savePlayers(players);
    res.json({ success: true, player: playerData });
});

// Middleware for Admin Check
function ensureAdmin(req, res, next) {
    if (req.session.isAdmin) {
        next();
    } else {
        res.status(403).json({ error: 'Access denied' });
    }
}

app.post('/api/admin/login', (req, res) => {
    const { password } = req.body;
    const config = loadConfig();

    if (password === config.adminPassword) {
        req.session.isAdmin = true;
        res.json({ success: true });
    } else {
        res.status(401).json({ error: 'Invalid password' });
    }
});

app.get('/api/admin/check', (req, res) => {
    res.json({ isAdmin: !!req.session.isAdmin });
});

app.get('/api/admin/config', ensureAdmin, (req, res) => {
    res.json(loadConfig());
});

app.post('/api/admin/create_player', ensureAdmin, (req, res) => {
    const { username, team, role, total_points } = req.body;
    let players = loadPlayers();

    const newPlayer = {
        id: Date.now().toString(),
        discord_id: "manual_" + Date.now(),
        username: username,
        role: role || "driver",
        team: team || "Free Agent",
        total_points: parseInt(total_points) || 0,
        manual: true
    };

    players.push(newPlayer);
    savePlayers(players);
    res.json({ success: true, player: newPlayer });
});

app.post('/api/admin/save_player', ensureAdmin, (req, res) => {
    const { id, ...updates } = req.body;
    let players = loadPlayers();

    const index = players.findIndex(p => p.id === id);
    if (index === -1) {
        return res.status(404).json({ error: 'Player not found' });
    }

    // Update player
    players[index] = { ...players[index], ...updates };
    savePlayers(players);
    res.json({ success: true, player: players[index] });
});

app.post('/api/admin/delete_player', ensureAdmin, (req, res) => {
    const { id } = req.body;
    let players = loadPlayers();
    const newPlayers = players.filter(p => p.id !== id);

    if (players.length === newPlayers.length) {
        return res.status(404).json({ error: 'Player not found' });
    }

    savePlayers(newPlayers);
    res.json({ success: true });
});

// Races Data
const RACES_FILE = path.join(DATA_DIR, 'races.json');

function loadRaces() {
    if (!fs.existsSync(RACES_FILE)) return [];
    try {
        return JSON.parse(fs.readFileSync(RACES_FILE, 'utf8'));
    } catch (e) { return []; }
}

function saveRaces(races) {
    fs.writeFileSync(RACES_FILE, JSON.stringify(races, null, 2));
}

// API Routes for Races
app.get('/api/races', (req, res) => {
    res.json(loadRaces());
});

app.post('/api/races', ensureAdmin, (req, res) => {
    const raceData = req.body;
    let races = loadRaces();

    // Add new race
    races.push(raceData);
    saveRaces(races);
    res.json({ success: true });
});

app.post('/api/races/clear', ensureAdmin, (req, res) => {
    saveRaces([]);
    res.json({ success: true });
});

// Start Server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
