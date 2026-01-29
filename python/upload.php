<?php
$message = "";

if (isset($_POST["submit"])) {
    $target_dir = "uploads/";
    if (!file_exists($target_dir)) {
        mkdir($target_dir, 0777, true);
    }

    $filename = basename($_FILES["fileToUpload"]["name"]);
    $target_file = $target_dir . time() . "_" . $filename; // Unikátní název

    if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
        // CESTY - Uprav podle svého PC!
        $python_path = "py"; // Nebo celá cesta k python.exe
        $script_path = "C:/Projects/python/good-night/f1hook.py";
        $abs_image_path = realpath($target_file);

        // SPUŠTĚNÍ PYTHONU
        // Příkaz: py c:/cesta/skript.py c:/cesta/obrazek.jpg
        $command = escapeshellcmd(
            "$python_path \"$script_path\" \"$abs_image_path\"",
        );
        $output = shell_exec($command . " 2>&1"); // Zachytí i případné chyby

        $message = "✅ Obrázek nahrán a odeslán ke zpracování!<br><pre>$output</pre>";
    } else {
        $message = "❌ Chyba při nahrávání souboru.";
    }
}
?>

<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>F1 OCR Uploader</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background: #121212; color: white; }
        .box { border: 2px solid #333; padding: 20px; border-radius: 10px; display: inline-block; }
        input { margin: 10px; }
        button { padding: 10px 20px; cursor: pointer; background: #e10600; color: white; border: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🏎️ F1 Results OCR</h2>
        <form action="" method="post" enctype="multipart/form-data">
            Vyber screenshot: <br>
            <input type="file" name="fileToUpload" id="fileToUpload"><br>
            <button type="submit" name="submit">ODESLAT NA DISCORD</button>
        </form>
        <p><?php echo $message; ?></p>
    </div>
</body>
</html>
