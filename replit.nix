{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.pip
    pkgs.python310Packages.setuptools
    pkgs.python310Packages.wheel
    pkgs.python310Packages.flask
    pkgs.python310Packages.python-dotenv
    pkgs.python310Packages.requests
    pkgs.python310Packages.gunicorn
    pkgs.bash
    pkgs.curl
    pkgs.coreutils
  ];
  env = {
    PYTHONBIN = "${pkgs.python310Full}/bin/python3.10";
    LANG = "en_US.UTF-8";
    PYTHONIOENCODING = "utf-8";
  };
}