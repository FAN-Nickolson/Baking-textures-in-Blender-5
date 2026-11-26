# 🍞 Bake Helper: High → Low for Blender 5

[![Blender](https://img.shields.io/badge/Blender-5.0%2B-orange.svg?style=flat-square&logo=blender)](https://www.blender.org/)
[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg?style=flat-square)](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases)
[![License](https://www.gnu.org/licenses/gpl-3.0.txt)](LICENSE)

**Bake Helper** is a robust, production-ready add-on for Blender 5 that completely automates the texture baking workflow from High-poly to Low-poly meshes. Say goodbye to manual node wiring, black texture frustrations, and hidden object errors.

## ✨ Key Features

### 🚀 Core Baking & Workflow

- **Smart Auto-Connect:** Automatically routes the baked textures into the correct Principled BSDF inputs (Base Color, Roughness, Metallic, Normal, AO).
- **Auto-Align Nodes:** Arranges your Shader Editor nodes into a perfect, readable `Image → Principled → Output` chain after baking.
- **GPU Acceleration:** Automatically detects and utilizes OptiX/CUDA for baking, making high-res (4K/8K) bakes up to 20x faster.
- **Auto-UV:** Generates UV unwraps automatically using _Smart UV Project_ if your Low-poly lacks one.

### 🛡️ Advanced Preflight & Safety

- **Safety Rollback (Undo):** If a bake fails or crashes, the add-on automatically restores your original Low-poly materials. No more broken models!
- **Smart Metallic Baking:** Blender cannot natively bake `METALLIC` maps. The add-on solves this by temporarily routing the Metallic signal through an `Emission` shader, baking it, and perfectly restoring your nodes.
- **Modifier & UV Warnings:** Warns you if High-poly has active modifiers (Subsurf, Solidify) or if Low-poly has multiple UV layers.
- **Auto-Fix Errors:** Automatically enables render visibility (fixes _"Object not enabled for rendering"_), zeroes out problematic Metallic values, and recalculates normals.
- **Adaptive Margin:** Automatically calculates the perfect margin/padding based on your texture resolution (prevents UV bleeding).

### 🌍 User Interface

- **Bilingual UI (EN/RU):** Switch between English and Russian on the fly. The add-on defaults to English.
- **Dynamic Tooltips:** Button tooltips instantly update when you change the interface language.

## 📦 Installation

1. Download the latest ZIP from the [Releases](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases/latest) page (the file is named like `bake_helper-<version>.zip`, e.g. `bake_helper-1.5.0.zip`).

2. Open Blender 5.0 or newer.
3. Go to `Edit → Preferences → Get Extensions → Install from Disk`.
4. Click the arrow in the top-right corner and select **Install from Disk...**.
5. Select the downloaded ZIP file and enable the checkbox next to **Bake Helper: High → Low**.

## 📖 How to Use

1. Open the sidebar in the 3D Viewport (press **`N`**) and switch to the **Bake** tab.
2. Select **two objects** in the scene: first the High-poly, then (with `Shift` held) the Low-poly (it must become the active object).
3. Click **"Take from Selection"** — the names will be filled in automatically.
4. Choose the **Map Type** (e.g., Base Color).
5. Click **"BAKE"**.

The add-on will run preflight checks, bake the texture, connect it to the material, and align the nodes.

## 🛠️ Technical Notes & Compatibility

| Parameter           | Value                                                   |
| :------------------ | :------------------------------------------------------ |
| **Blender Version** | 5.0 and newer                                           |
| **Render Engine**   | Cycles (switched automatically)                         |
| **Supported Maps**  | Diffuse, Normal, Roughness, Metallic, AO, EMIT (Height) |

### ⚠️ Important Notes

- **Metallic Maps:** The add-on uses a clever `EMIT` workaround to bake Metallic maps. Just select `Metallic` in the dropdown and hit Bake—everything happens automatically.
- **Height / Displacement:** Blender cannot natively bake `DISPLACEMENT` from High to Low. Use the `Height / Displacement (Emit)` option and plug your height data into the Emission shader on the High-poly material.
- **Color Space:** The add-on automatically assigns `sRGB` to Base Color and `Non-Color` to technical maps (Normal, Metallic, Roughness).

## 🩺 Troubleshooting

- **The texture is completely black:** The add-on should auto-fix this, but ensure your High-poly object is not hidden in the Outliner (Camera and Eye icons must be enabled). Also, ensure the objects actually overlap in 3D space.
- **Texture bleeds onto neighboring UVs:** The Adaptive Margin usually handles this. If it persists, reduce the `Margin` to `2` or `4` pixels in the panel.
- **"Enum 'DISPLACEMENT' not found":** This error is fixed in v1.5.0. Please ensure you are using the latest version.

## 🤝 Contributing

Found a bug or have a feature request? Please open an [Issue](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/issues). Pull requests are welcome!

## 📄 License

This project is distributed under the GPL-3.0-or-later License. See the [LICENSE](LICENSE) file for details.
