<?php
/**
 * Simracing League Dashboard - Landing Page
 * 
 * Hlavní vstupní bod aplikace s controller pattern.
 */

// Konfigurace
define('APP_NAME', 'SimRacing Liga');
define('APP_VERSION', '1.0.0');

// Aktivní stránka pro navigaci
$currentPage = $_GET['page'] ?? 'dashboard';

// Definice navigačních položek
$navigation = [
    'hlavni' => [
        'title' => 'Hlavní',
        'items' => [
            'dashboard' => [
                'label' => 'Přehled',
                'icon' => 'dashboard',
                'href' => '?page=dashboard'
            ],
            'standings' => [
                'label' => 'Pořadí šampionátu',
                'icon' => 'trophy',
                'href' => '?page=standings'
            ],
            'races' => [
                'label' => 'Výsledky závodů',
                'icon' => 'flag',
                'href' => '?page=races'
            ],
        ]
    ],
    'sprava' => [
        'title' => 'Správa',
        'items' => [
            'upload' => [
                'label' => 'Nahrát výsledky',
                'icon' => 'upload',
                'href' => '?page=upload'
            ],
            'drivers' => [
                'label' => 'Jezdci',
                'icon' => 'users',
                'href' => '?page=drivers'
            ],
            'teams' => [
                'label' => 'Týmy',
                'icon' => 'team',
                'href' => '?page=teams'
            ],
        ]
    ],
    'statistiky' => [
        'title' => 'Statistiky',
        'items' => [
            'circuits' => [
                'label' => 'Okruhy',
                'icon' => 'circuit',
                'href' => '?page=circuits'
            ],
            'records' => [
                'label' => 'Rekordy',
                'icon' => 'chart',
                'href' => '?page=records'
            ],
        ]
    ]
];

// Mapování názvů stránek pro header
$pageTitles = [
    'dashboard' => 'Přehled',
    'standings' => 'Pořadí šampionátu',
    'races' => 'Výsledky závodů',
    'upload' => 'Nahrát výsledky',
    'drivers' => 'Jezdci',
    'teams' => 'Týmy',
    'circuits' => 'Okruhy',
    'records' => 'Rekordy',
];

$pageTitle = $pageTitles[$currentPage] ?? 'Přehled';

/**
 * Generuje SVG ikonu podle názvu
 */
function getIcon(string $name): string {
    $icons = [
        'dashboard' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
        'trophy' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>',
        'flag' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
        'upload' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        'users' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        'team' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        'circuit' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
        'chart' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    ];
    
    return $icons[$name] ?? '';
}
?>
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SimRacing Liga - Dashboard pro správu výsledků a statistik simracingové ligy">
    <title><?= htmlspecialchars($pageTitle) ?> | <?= APP_NAME ?></title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700&display=swap" rel="stylesheet">
    
    <!-- Styles -->
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <!-- Logo -->
            <div class="sidebar__logo">
                <div class="sidebar__logo-icon">SR</div>
                <div class="sidebar__logo-text">Sim<span>Racing</span></div>
            </div>
            
            <!-- Navigation -->
            <nav class="sidebar__nav">
                <?php foreach ($navigation as $sectionKey => $section): ?>
                <div class="sidebar__nav-section">
                    <h3 class="sidebar__nav-title"><?= htmlspecialchars($section['title']) ?></h3>
                    <ul class="sidebar__nav-list">
                        <?php foreach ($section['items'] as $itemKey => $item): ?>
                        <li class="sidebar__nav-item">
                            <a href="<?= htmlspecialchars($item['href']) ?>" 
                               class="sidebar__nav-link <?= $currentPage === $itemKey ? 'sidebar__nav-link--active' : '' ?>">
                                <span class="sidebar__nav-icon"><?= getIcon($item['icon']) ?></span>
                                <span class="sidebar__nav-label"><?= htmlspecialchars($item['label']) ?></span>
                            </a>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                </div>
                <?php endforeach; ?>
            </nav>
            
            <!-- Footer -->
            <div class="sidebar__footer">
                <p class="sidebar__footer-text">v<?= APP_VERSION ?></p>
            </div>
        </aside>
        
        <!-- Main Content -->
        <main class="main-content">
            <!-- Header -->
            <header class="main-header">
                <h1 class="main-header__title"><?= htmlspecialchars($pageTitle) ?></h1>
                <div class="main-header__actions">
                    <!-- Akční tlačítka budou zde -->
                </div>
            </header>
            
            <!-- Content Area -->
            <div class="content-area">
                <?php
                // Controller pattern - načtení obsahu podle aktuální stránky
                $viewFile = __DIR__ . '/views/' . $currentPage . '.php';
                
                if (file_exists($viewFile)) {
                    include $viewFile;
                } else {
                    // Výchozí obsah - placeholder
                    echo '<div class="placeholder">';
                    echo '<p class="text-muted">Obsah stránky "' . htmlspecialchars($pageTitle) . '" bude brzy k dispozici.</p>';
                    echo '</div>';
                }
                ?>
            </div>
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="assets/js/app.js" defer></script>
</body>
</html>
