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
    hash = "sha256-InddS9NxVrYOufiP7iWQTQ3VBeJgX2UlBA+Gf7ZfFrI=";
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
