<!-- spellchecker: ignore fuchsr romakev -->

# Hardware Models

This directory contains (or references) 3D-printable components for the Life
Check project.

## Philosophy

We believe in supporting the 3D printing community. Our strategy for hardware
models follows two rules:

1. **Vendor for Customization**: We only vendor `.scad` or source files when
   we've applied specific project-level defaults (e.g., specific dimensions for
   the level shifter board and Dupont connectors).
1. **Link for Traffic**: For standard components (like ESP32 cases), we link
   directly to the original author's page on platforms like MakerWorld. This
   ensures creators receive the "model visits" and engagement they deserve.

## Parts Catalog

| Component              | Source                                             | Strategy     | Notes                                                                                        |
| :--------------------- | :------------------------------------------------- | :----------- | :------------------------------------------------------------------------------------------- |
| **Level Shifter Case** | [Matthew](https://makerworld.com/en/models/46852)  | **Vendored** | [level-shifter-case.scad](./level-shifter-case.scad) is pre-configured for the BSS138 board. |
| **Pi Zero Case**       | [Romakev](https://makerworld.com/en/models/548199) | **Linked**   | Slim snap-fit case for Pi Zero / Zero W.                                                     |
| **ESP32 Case**         | [fuchsr](https://makerworld.com/en/models/1891997) | **Linked**   | Standard enclosure for ESP32 WROOM DevKit v1.                                                |

## Tools

- [OpenSCAD](https://openscad.org/) — Required for the Level Shifter Case.
