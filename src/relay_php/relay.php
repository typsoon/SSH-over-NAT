<?php
error_reporting(0);
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Pragma: no-cache");

$action = $_GET['action'] ?? '';
$channel = $_GET['channel'] ?? ''; 

// 1. NOWOŚĆ: Ręczny reset - czyści oba bufory (wywoływany przy nowym połączeniu SSH)
if ($action === 'reset') {
    file_put_contents(__DIR__ . '/c2s.txt', '');
    file_put_contents(__DIR__ . '/s2c.txt', '');
    echo "OK_RESET";
    exit;
}

if (!in_array($channel, ['c2s', 's2c'])) {
    http_response_code(400);
    die("Zly kanal.");
}

$file = __DIR__ . '/' . $channel . '.txt';

// 2. NOWOŚĆ: Auto-cleanup - Jeśli w pliku są dane, których nikt nie odebrał od 30 sekund,
// to znaczy, że któraś strona padła. Wyrzucamy je, żeby nie psuły kolejnych sesji.
if (file_exists($file) && filesize($file) > 0) {
    if ((time() - filemtime($file)) > 30) {
        file_put_contents($file, '');
    }
}

if ($action === 'send') {
    $b64_data = file_get_contents('php://input');
    if (!empty($b64_data)) {
        $raw_data = base64_decode($b64_data);
        if ($raw_data !== false) {
            file_put_contents($file, $raw_data, FILE_APPEND | LOCK_EX);
            echo "OK";
        }
    }
} elseif ($action === 'recv') {
    $fp = @fopen($file, "c+");
    if ($fp && flock($fp, LOCK_EX)) {
        clearstatcache();
        $size = filesize($file);
        
        // 3. NOWOŚĆ: Ochrona przed przepelnieniem pamięci PHP (limit 5MB na plik). 
        // Jak urośnie wyżej, to tniemy bezlitośnie.
        if ($size > 5 * 1024 * 1024) { 
            ftruncate($fp, 0);
            $size = 0;
        }

        if ($size > 0) {
            $raw_data = fread($fp, $size);
            ftruncate($fp, 0); 
            echo "[[[" . base64_encode($raw_data) . "]]]";
        }
        flock($fp, LOCK_UN);
        fclose($fp);
    }
}
?>