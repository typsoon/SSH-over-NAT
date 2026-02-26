<?php
header('Content-Type: application/json');
// $db_file = 'peers.json';
$db_file = 'hashed_peers.json';

$json = file_get_contents('php://input');
$data = json_decode($json, true);

$db = file_exists($db_file) ? json_decode(file_get_contents($db_file), true) : [];

if ($data && isset($data['hash'])) {
    $hash = $data['hash'];
    $db[$hash] = ['ip' => $data['ip'], 'port' => $data['port'], 'time' => time()];

    foreach($db as $u => $info) {
        if (time() - $info['time'] > 60) unset($db[$u]);
    }
    file_put_contents($db_file, json_encode($db));

    $peerhash = null;
    $peerinfo = null;
    foreach($db as $u => $info) {
        if ($u !== $hash) {
            $peerhash = $u;
            $peerinfo = $info;
            break;
        }
    }

    if ($peerhash) {
        echo json_encode(["status" => "ok", "peerhash" => $peerhash, "ip" => $peerinfo['ip'], "port" => $peerinfo['port']]);
    } else {
        echo json_encode(["status" => "waiting"]);
    }
} else {
    echo json_encode(["error" => "Brak danych"]);
}