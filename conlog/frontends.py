from conlang.datatypes import *

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Text frontend (similar to DOT)
#
#   operation := "+=" | "-="
#
#   statement := node-name (":" var-name operation (var-name | const))?
#              | var-name "=" (const | "?")
#              | node-name ("--" node-name)+
#
#   program := statement (";" statement)* ";"?
#
#   Variables that are not explicitly set to a constant or "?" are implictly left free.
#   Nodes that are never declared are assumed to be None nodes.
