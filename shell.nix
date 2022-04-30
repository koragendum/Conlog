{ sources ? import ./nix/sources.nix
, pkgs ? import sources.nixpkgs { }
}:
let
  my-python-packages = python-packages: with python-packages; [
    isort
    flake8
    mccabe
    rope
    pyflakes
    pytest
    hypothesis
    line_profiler
    networkx
    matplotlib
  ];
  python-with-my-packages = pkgs.python310.withPackages my-python-packages;
in
pkgs.mkShell {
  buildInputs = [ python-with-my-packages pkgs.nodePackages.pyright ];
}
