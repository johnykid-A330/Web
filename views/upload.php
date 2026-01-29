<?php
/**
 * Upload View - Nahrát výsledky
 * 
 * Stránka pro nahrávání CSV souborů s výsledky závodů.
 * Obsahuje bezpečnostní opatření: MIME type validace, povoleny pouze CSV soubory.
 */

// Zpracování uploadu
$uploadMessage = '';
$uploadSuccess = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['resultsFile'])) {
    $file = $_FILES['resultsFile'];
    
    // Povolené MIME typy pro CSV
    $allowedMimeTypes = [
        'text/csv',
        'text/plain',
        'application/csv',
        'application/vnd.ms-excel', // Některé systémy
    ];
    
    // Kontrola MIME type pomocí finfo
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $detectedMime = $finfo->file($file['tmp_name']);
    
    // Kontrola přípony souboru
    $fileExtension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    
    // Validace
    $errors = [];
    
    // 1. Kontrola chyb při uploadu
    if ($file['error'] !== UPLOAD_ERR_OK) {
        $uploadErrors = [
            UPLOAD_ERR_INI_SIZE => 'Soubor je příliš velký (limit php.ini).',
            UPLOAD_ERR_FORM_SIZE => 'Soubor je příliš velký.',
            UPLOAD_ERR_PARTIAL => 'Soubor byl nahrán pouze částečně.',
            UPLOAD_ERR_NO_FILE => 'Žádný soubor nebyl nahrán.',
            UPLOAD_ERR_NO_TMP_DIR => 'Chybí dočasná složka.',
            UPLOAD_ERR_CANT_WRITE => 'Nepodařilo se zapsat soubor.',
        ];
        $errors[] = $uploadErrors[$file['error']] ?? 'Neznámá chyba při uploadu.';
    }
    
    // 2. Kontrola přípony
    if ($fileExtension !== 'csv') {
        $errors[] = 'Povolená je pouze přípona .csv';
    }
    
    // 3. Kontrola MIME typu
    if (!in_array($detectedMime, $allowedMimeTypes, true)) {
        $errors[] = 'Neplatný typ souboru. Povolen je pouze CSV. (Detekovaný MIME: ' . htmlspecialchars($detectedMime) . ')';
    }
    
    // 4. Kontrola velikosti (max 5MB)
    $maxSize = 5 * 1024 * 1024;
    if ($file['size'] > $maxSize) {
        $errors[] = 'Soubor je příliš velký. Maximální velikost je 5 MB.';
    }
    
    // 5. Dodatečná validace obsahu CSV
    if (empty($errors)) {
        $handle = fopen($file['tmp_name'], 'r');
        if ($handle) {
            $firstLine = fgets($handle);
            fclose($handle);
            
            // Kontrola, zda první řádek vypadá jako CSV (obsahuje oddělovače)
            if ($firstLine && strpos($firstLine, ',') === false && strpos($firstLine, ';') === false) {
                $errors[] = 'Soubor neobsahuje platná CSV data.';
            }
        }
    }
    
    if (empty($errors)) {
        // Generování bezpečného názvu souboru
        $timestamp = date('Y-m-d_H-i-s');
        $safeName = preg_replace('/[^a-zA-Z0-9_-]/', '', pathinfo($file['name'], PATHINFO_FILENAME));
        $newFileName = $timestamp . '_' . ($safeName ?: 'results') . '.csv';
        $uploadPath = __DIR__ . '/../data/races/' . $newFileName;
        
        if (move_uploaded_file($file['tmp_name'], $uploadPath)) {
            $uploadSuccess = true;
            $uploadMessage = 'Soubor "' . htmlspecialchars($file['name']) . '" byl úspěšně nahrán.';
        } else {
            $uploadMessage = 'Nepodařilo se uložit soubor. Zkontrolujte oprávnění složky.';
        }
    } else {
        $uploadMessage = implode('<br>', $errors);
    }
}
?>

<div class="upload-page">
    <?php if ($uploadMessage): ?>
    <div class="alert <?= $uploadSuccess ? 'alert--success' : 'alert--error' ?>">
        <div class="alert__icon">
            <?php if ($uploadSuccess): ?>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <?php else: ?>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <?php endif; ?>
        </div>
        <div class="alert__content"><?= $uploadMessage ?></div>
    </div>
    <?php endif; ?>

    <div class="card">
        <div class="card__header">
            <h2 class="card__title">Nahrát výsledky závodu</h2>
            <p class="card__subtitle">Nahrajte CSV soubor s výsledky závodu</p>
        </div>
        
        <div class="card__body">
            <form method="POST" enctype="multipart/form-data" id="uploadForm" class="upload-form">
                <div class="upload-dropzone" id="dropzone">
                    <div class="upload-dropzone__icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17 8 12 3 7 8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                    </div>
                    <div class="upload-dropzone__text">
                        <span class="upload-dropzone__main">Přetáhněte sem CSV soubor</span>
                        <span class="upload-dropzone__sub">nebo klikněte pro výběr souboru</span>
                    </div>
                    <input 
                        type="file" 
                        id="resultsFile" 
                        name="resultsFile" 
                        accept=".csv,text/csv" 
                        class="upload-dropzone__input"
                        required
                    >
                </div>
                
                <div class="upload-info" id="fileInfo" style="display: none;">
                    <div class="upload-info__file">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="upload-info__icon">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13"/>
                            <line x1="16" y1="17" x2="8" y2="17"/>
                        </svg>
                        <span id="fileName" class="upload-info__name"></span>
                        <span id="fileSize" class="upload-info__size"></span>
                    </div>
                    <button type="button" id="removeFile" class="upload-info__remove" title="Odebrat soubor">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                
                <div class="upload-error" id="uploadError" style="display: none;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <span id="errorText"></span>
                </div>
                
                <button type="submit" class="btn btn--primary btn--lg" id="submitBtn" disabled>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn__icon">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    Nahrát výsledky
                </button>
            </form>
        </div>
    </div>
    
    <div class="card card--info">
        <div class="card__header">
            <h3 class="card__title">Formát CSV souboru</h3>
        </div>
        <div class="card__body">
            <p class="mb-md">CSV soubor by měl obsahovat následující sloupce:</p>
            <div class="code-block">
                <code>position,driver_name,team,laps,time,gap,points</code>
            </div>
            <ul class="info-list">
                <li><strong>position</strong> – Pořadí v závodě</li>
                <li><strong>driver_name</strong> – Jméno jezdce</li>
                <li><strong>team</strong> – Název týmu</li>
                <li><strong>laps</strong> – Počet kol</li>
                <li><strong>time</strong> – Celkový čas</li>
                <li><strong>gap</strong> – Ztráta na prvního</li>
                <li><strong>points</strong> – Získané body</li>
            </ul>
        </div>
    </div>
</div>

<script>
(function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('resultsFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const removeFile = document.getElementById('removeFile');
    const uploadError = document.getElementById('uploadError');
    const errorText = document.getElementById('errorText');
    const submitBtn = document.getElementById('submitBtn');
    
    // Povolené MIME typy
    const allowedMimeTypes = ['text/csv', 'text/plain', 'application/csv', 'application/vnd.ms-excel'];
    const maxFileSize = 5 * 1024 * 1024; // 5MB
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function validateFile(file) {
        const errors = [];
        
        // Kontrola přípony
        const extension = file.name.split('.').pop().toLowerCase();
        if (extension !== 'csv') {
            errors.push('Povolená je pouze přípona .csv');
        }
        
        // Kontrola MIME typu (některé prohlížeče mohou hlásit jiný MIME)
        if (file.type && !allowedMimeTypes.includes(file.type) && extension !== 'csv') {
            errors.push('Neplatný typ souboru. Povolen je pouze CSV.');
        }
        
        // Kontrola velikosti
        if (file.size > maxFileSize) {
            errors.push('Soubor je příliš velký. Maximální velikost je 5 MB.');
        }
        
        return errors;
    }
    
    function showError(message) {
        uploadError.style.display = 'flex';
        errorText.textContent = message;
        fileInfo.style.display = 'none';
        submitBtn.disabled = true;
        dropzone.classList.add('upload-dropzone--error');
        dropzone.classList.remove('upload-dropzone--success');
    }
    
    function showFile(file) {
        uploadError.style.display = 'none';
        fileInfo.style.display = 'flex';
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        submitBtn.disabled = false;
        dropzone.classList.add('upload-dropzone--success');
        dropzone.classList.remove('upload-dropzone--error');
    }
    
    function resetForm() {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadError.style.display = 'none';
        submitBtn.disabled = true;
        dropzone.classList.remove('upload-dropzone--success', 'upload-dropzone--error');
    }
    
    function handleFile(file) {
        const errors = validateFile(file);
        
        if (errors.length > 0) {
            showError(errors.join(' '));
            return;
        }
        
        showFile(file);
    }
    
    // Click handler
    dropzone.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    // Drag & drop handlers
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('upload-dropzone--dragover');
    });
    
    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.classList.remove('upload-dropzone--dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('upload-dropzone--dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Nastavit soubor do input elementu
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;
            
            handleFile(files[0]);
        }
    });
    
    // Remove file handler
    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        resetForm();
    });
})();
</script>
