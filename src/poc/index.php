<?php
header('Content-Type: application/json');
$db_file = 'peers.json';

$json = file_get_contents('php://input');
$data = json_decode($json, true);

$db = file_exists($db_file) ? json_decode(file_get_contents($db_file), true) : [];

if ($data && isset($data['user'])) {
    $user = $data['user'];
    $db[$user] = ['ip' => $data['ip'], 'port' => $data['port'], 'time' => time()];

    foreach($db as $u => $info) {
        if (time() - $info['time'] > 60) unset($db[$u]);
    }
    file_put_contents($db_file, json_encode($db));

    $peername = null;
    $peerinfo = null;
    foreach($db as $u => $info) {
        if ($u !== $user) {
            $peername = $u;
            $peerinfo = $info;
            break;
        }
    }

    if ($peername) {
        echo json_encode(["status" => "ok", "peername" => $peername, "ip" => $peerinfo['ip'], "port" => $peerinfo['port']]);
    } else {
        echo json_encode(["status" => "waiting"]);
    }
} else {
    echo json_encode(["error" => "Brak danych"]);
}