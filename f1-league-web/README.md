# 🏎️ F1 League 2026 - Web Application

Moderní webová aplikace pro správu F1 ligy s tabulkou, výsledky závodů, statistikami jezdců a registrací.

## 🚀 Features

- ✅ **Championship Standings** - Real-time standings s podiem
- ✅ **Race Results** - Kompletní výsledky všech závodů
- ✅ **Driver Profiles** - Statistiky a historie každého jezdce
- ✅ **Driver Registration** - Online registrační formulář
- ✅ **CSV Import** - Drag & drop upload F1 25 results
- ✅ **Modern Design** - Dark mode, glassmorphism, responsive
- ✅ **24/7 Hosting** - Ready for Netlify/GitHub Pages

## 📁 Project Structure

```
f1-league-web/
├── index.html          # Homepage - Standings
├── results.html        # Race Results
├── drivers.html        # Driver Profiles
├── register.html       # Driver Registration
├── upload.html         # CSV Upload (Admin)
├── css/
│   └── style.css      # Complete design system
├── js/
│   ├── app.js         # Main application logic
│   ├── csv-parser.js  # F1 25 CSV parser
│   └── standings.js   # Championship calculations
└── data/
    ├── config.json    # League configuration
    ├── drivers.json   # Registered drivers
    └── races.json     # Race results
```

## 🎨 Design Features

- **Dark Mode First** - F1-inspired color palette
- **Glassmorphism** - Modern glass effects on cards
- **Animations** - Smooth transitions and hover effects
- **Responsive** - Mobile-first design
- **F1 Theme** - Red/Orange gradients, racing aesthetics

## 🛠️ Local Development

1. **Open in browser:**
   ```
   Otevřete index.html v browseru
   ```

2. **Or use a local server:**
   ```powershell
   # Python
   python -m http.server 8000
   
   # Node.js
   npx serve
   ```

3. **Visit:** `http://localhost:8000`

## 📤 Deployment na Netlify (Free 24/7 Hosting)

### Method 1: Drag & Drop (Nejjednodušší)

1. Jděte na [netlify.com](https://netlify.com)
2. Přihlaste se (GitHub/GitLab/Email)
3. Klikněte na "Add new site" → "Deploy manually"
4. Přetáhněte celou složku `f1-league-web` do uploadu
5. ✅ Hotovo! Dostanete URL např. `f1-league-abc123.netlify.app`

### Method 2: GitHub + Netlify (Automatické updaty)

1. **Upload na GitHub:**
   ```powershell
   cd c:\Projects\standingsbot\f1-league-web
   git init
   git add .
   git commit -m "Initial F1 League website"
   git remote add origin https://github.com/YOUR_USERNAME/f1-league-web.git
   git push -u origin main
   ```

2. **Connect Netlify:**
   - Jděte na [netlify.com](https://netlify.com)
   - "Add new site" → "Import an existing project"
   - Vyberte GitHub repository
   - Deploy settings: (nechte prázdné, je to statická stránka)
   - Klikněte "Deploy"

3. **✅ Hotovo!** Každý push na GitHub = automatický deploy

### Custom Domain (Optional)

V Netlify settings můžete nastavit vlastní doménu (např. `f1league.cz`)

## 📊 Jak Používat

### 1. Registrace Jezdců

- Otevřete `/register.html`
- Vyplňte Discord jméno a EA ID
- Data se ukládají do `localStorage`

### 2. Upload CSV z F1 25

1. Otevřete `/upload.html`
2. Přetáhněte CSV soubor z:
   ```
   C:\Users\jonas\Documents\My Games\F1 25\session results\
   ```
3. Zadejte název závodu
4. Klikněte "Import"

### 3. Zobrazení Standings

- Homepage automaticky zobrazuje:
  - Top 3 Podium
  - Kompletní standings
  - Poslední vítěz

## 🔧 Konfigurace

Upravte `data/config.json` pro změnu nastavení ligy:

```json
{
  "leagueName": "F1 League 2026",
  "season": "Season 1",
  "pointsSystem": [25, 18, 15, 12, 10, 8, 6, 4, 2, 1],
  "fastestLapBonus": 1
}
```

## 💾 Data Storage

Aplikace používá **localStorage** pro persistenci dat:
- Funguje offline v browseru
- Data jsou na straně klienta
- Pro sdílení mezi uživateli je potřeba deploy na hosting

**Pro produkci:** Všichni uživatelé vidí stejná data přes hosting URL.

## 🎯 Supported CSV Format

Aplikace parsuje F1 25 CSV výstupy s formátem:

```csv
"Pos.","Driver","Team","Grid","Stops","Best","Time","Pts.","driver type"
"1","Player","Ferrari","6","0","1:30.347","7:39.054","25","Player"
...
```

## 📝 Todo / Future Features

- [ ] Backend API pro sdílení dat mezi uživateli
- [ ] Admin dashboard
- [ ] Export standings to PDF
- [ ] Discord integration
- [ ] Live timing during races

## 🐛 Troubleshooting

**CSV import nefunguje:**
- Zkontrolujte formát CSV (musí být z F1 25)
- Soubor musí mít header s "Pos.", "Driver", "Team", etc.

**Data se neukládají:**
- Zkontrolujte localStorage v browser DevTools
- Některé browsery blokují localStorage v "private" mode

**Stránky nefungují po deployu:**
- Ujistěte se, že jsou všechny soubory nahráné
- Zkontrolujte browser console pro chyby

## 📧 Support

Pro otázky a problémy kontaktujte admina ligy.

---

**Made with ❤️ for F1 League 2026** 🏁
