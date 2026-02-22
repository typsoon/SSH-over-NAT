<?php
error_reporting(0);
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Pragma: no-cache");

$action = $_GET['action'] ?? '';
$channel = $_GET['channel'] ?? ''; 

if (!in_array($channel, ['c2s', 's2c'])) {
    http_response_code(400);
    die("Zly kanal.");
}

$file = __DIR__ . '/' . $channel . '.txt';

if ($action === 'send') {
    $b64_data = file_get_contents('php://input');
    if (!empty($b64_data)) {
        // Dekodujemy Base64 od klienta NA CZYSTE BAJTY przed zapisem!
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
        if ($size > 0) {
            $raw_data = fread($fp, $size);
            ftruncate($fp, 0); 
            // Wysyłamy czyste bajty z powrotem spakowane w Base64
            echo "[[[" . base64_encode($raw_data) . "]]]";
        }
        flock($fp, LOCK_UN);
        fclose($fp);
    }
}
?>