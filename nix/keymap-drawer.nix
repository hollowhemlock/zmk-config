{ lib
, buildPythonApplication
, buildPythonPackage
, callPackage
, fetchFromGitHub
, setuptools
, poetry-core
, pydantic
, pyparsing
, pcpp
, pyyaml
, platformdirs
, pydantic-settings
, tree-sitter
}:
let
  tree-sitter-devicetree = callPackage ./tree-sitter-devicetree.nix {};
in
buildPythonApplication rec {
  pname = "keymap-drawer";
  version = "0.21.0";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "hollowhemlock";
    repo = pname;
    rev = "feature/merge-layers-with-corner-glyphs";
    hash = "sha256-LanOW/U/K1sXa/WdjIlg99scYnpe7ojRHVJ+iUZCEP0=";
  };

  build-system = [ poetry-core ];

  propagatedBuildInputs = [
    pydantic
    pcpp
    pyyaml
    platformdirs
    pydantic-settings
    pyparsing
    tree-sitter
    tree-sitter-devicetree
  ];

  doCheck = false;

  meta = {
    homepage = "https://github.com/caksoylar/keymap-drawer";
    description = "Parse QMK & ZMK keymaps and draw them as vector graphics";
    license = lib.licenses.mit;
  };
}
