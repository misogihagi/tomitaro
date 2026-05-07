{ config, lib, pkgs, ... }:

{
  networking.networkmanager = {
    enable = true;
  };

  # NetworkManagerやiwdとの競合を回避
  networking.wireless.enable = lib.mkForce false;
  networking.wireless.iwd.enable = lib.mkForce false;

  # Wi-Fi設定を /etc/NetworkManager/system-connections に直接書き込む

  # environment.etc."NetworkManager/system-connections/default-wifi.nmconnection".text = "...";）を作成した場合、その大元の実体ファイルは /nix/store/ 配下に保存されます。 /nix/store/ 内のファイルは**システムの全ユーザーから読み取り可能（World-readable）**となってしまうため、Wi-Fiのパスワード（PSK）が誰でも覗き見できる状態になってしまいます。
  # もし「実機に自分しかログインしない」ので許容できる場合
  # Raspberry Piで自分しか使わないのでパスワードが見えても構わない、という場合は、環境変数ファイル（wireless.env）の使用をやめて、Nix側に寄せることで非常にすっきりと書くことができます。


  systemd.services.setup-wifi-connection = {
    description = "Setup Wi-Fi connection directly to system-connections";
    # NetworkManagerが起動する前に実行する
    wantedBy = [ "NetworkManager.service" ];
    before = [ "NetworkManager.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      # 実際のパスに合わせて読み込む（先頭の - はファイルが無くてもエラーにしないためのもの）
      EnvironmentFile = "-/etc/nixos/secrets/wireless.env";
    };
    script = ''
      # 環境変数が読み込めていない場合は何もしない
      if [ -z "$SSID_WIFI" ] || [ -z "$PSK_WIFI" ]; then
        echo "SSID_WIFI or PSK_WIFI is not set in /etc/nixos/secrets/wireless.env, skipping Wi-Fi setup."
        exit 0
      fi

      mkdir -p /etc/NetworkManager/system-connections
      FILE="/etc/NetworkManager/system-connections/default-wifi.nmconnection"

      # NetworkManagerのKeyfileフォーマット（INI形式）で直接書き込む
      # ※NetworkManagerは行頭の空白を嫌うため、左詰めで記述します
      cat <<EOF > "$FILE"
[connection]
id=$SSID_WIFI
uuid=f5541fe5-a769-4c72-b106-d87d1432792e
type=wifi
interface-name=wlan0

[wifi]
mode=infrastructure
ssid=$SSID_WIFI

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk=$PSK_WIFI

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto

[proxy]
EOF

      # パーミッションを 600 にしないと NetworkManager はファイルを無視するため注意
      chmod 600 "$FILE"
    '';
  };
}
