{
  description = "CSCI 1710 Flake";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    utils,
    ...
  } @ inputs:
    utils.lib.eachDefaultSystem
    (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in rec
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python313
            python313Packages.z3-solver
            pyright
          ];

          # Make zsh the shell
          shellHook = ''
            SHELL="$(which zsh)"
            zsh
          '';
        };
      }
    );
}
