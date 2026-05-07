{ pkgs, ... }: {
  environment.systemPackages = [ pkgs.git ];

  systemd.services.clone-tomitaro = {
    description = "Clone tomitaro repository to /usr/local/tomitaro";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    path = [ pkgs.git ];
    script = ''
      if [ ! -d /usr/local/tomitaro ]; then
        mkdir -p /usr/local/tomitaro
        git clone https://github.com/misogihagi/tomitaro.git /usr/local/tomitaro
      fi
    '';
  };
}
