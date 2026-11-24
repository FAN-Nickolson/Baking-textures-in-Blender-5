EN
# 🍞 Bake Helper: High → Low for Blender 5

[![Blender](https://img.shields.io/badge/Blender-5.0%2B-orange.svg?style=flat-square&logo=blender)](https://www.blender.org/)
[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg?style=flat-square)](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

**Bake Helper** is a powerful and smart add-on for Blender 5 that automates the texture baking workflow from high-poly to low-poly meshes. Say goodbye to manual selection setup, black texture issues, and hand-wiring shader nodes.

## ✨ Key Features

*   **🧠 Smart Auto-Connect:** After baking, the resulting texture is automatically plugged into the correct Principled BSDF input (Base Color, Roughness, Normal, AO, etc.).
*   **🧹 Auto-Align Nodes:** The Shader Editor nodes are automatically arranged into a clean `Image → Principled → Output` chain for perfect readability.
*   **🌍 Bilingual UI:** Full support for both English and Russian. Switch languages right from the panel.
*   **🛡️ Preflight Checks:** The add-on validates your scene and auto-fixes common issues before baking:
    *   *Automatically zeroes out `Metallic = 1.0`* (the #1 cause of black textures).
    *   *Enables render visibility* (fixes the `is not enabled for rendering` error).
    *   *Recalculates normals* and checks bounding box overlap.
    *   *Auto-boosts `Cage Extrusion`* if the value is too small.
*   **🧵 Auto UV Unwrap:** If the low-poly object lacks UVs, the add-on generates them using *Smart UV Project*.
*   **📦 Smart Saving:** Saves the baked PNG next to your `.blend` file or into your Documents folder.

## 🖼️ Screenshots
<!-- Uncomment and add your images if available -->
<!-- 
![Add-on Panel](docs/panel.png)
![Aligned Nodes](docs/nodes.png)
-->

## 🚀 Installation

1. Download **`bake_helper.zip`** from the [Releases](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases/latest) page.
2. Open Blender 5.0 or newer.
3. Go to `Edit → Preferences → Add-ons`.
4. Click the arrow in the top-right corner and select **Install from Disk...**.
5. Choose the downloaded `bake_helper.zip` and click **Install**.
6. **Make sure to check the box** next to `Bake Helper: High → Low` to enable it.

## 📖 How to Use

1. Open the sidebar in the 3D Viewport (press **`N`**).
2. Switch to the **Bake** tab.
3. Select **two objects** in the scene: first the high-poly, then (with `Shift` held) the low-poly (it must become the active object).
4. Click **"Take from selection"** — the object names will be filled in automatically.
5. Choose the **Map Type** (e.g., Base Color).
6. Set the desired resolution and margins.
7. Click **"BAKE"**.

The add-on will run preflight checks, bake the texture, connect it to the material, and align the nodes.

## 🛠️ Technical Details & Compatibility

| Parameter | Value |
| :--- | :--- |
| **Blender Version** | 5.0 and newer |
| **Render Engine** | Cycles (switched automatically) |
| **Supported Maps** | Diffuse, Normal, Roughness, Metallic, AO, EMIT (Height) |

### ⚠️ Important Note on Displacement / Height Maps
Blender cannot natively bake `DISPLACEMENT` from high-poly to low-poly. In this add-on, that option is replaced with **Height / Displacement (Emit)**.
To produce a height map, plug the desired signal (e.g., a procedural texture or `Geometry → Pointiness`) into the **Emission** input of the high-poly material. The add-on will bake it as an `EMIT` pass and automatically assign the correct `Non-Color` color space to the resulting texture.

### 🩺 Troubleshooting
*   **The texture is completely black:** Make sure the `Metallic` value on the high-poly material is below 1.0 (the add-on fixes this automatically, but check if a texture is plugged into it). Also make sure the objects actually overlap in 3D space.
*   **The texture bleeds onto neighboring UV islands:** Reduce `Margin` to `2` or `4` pixels and choose the `Adjacent Faces` margin type.
*   **"Object is not enabled for rendering" error:** The add-on automatically enables render visibility. If the error persists, make sure the object isn't hidden inside an excluded collection.

## 🤝 Contributing
Found a bug or have a feature request? Please open an [Issue](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/issues). Pull requests are welcome!

## 📄 License
This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.





RU
# 🍞 Bake Helper: High → Low для Blender 5

[![Blender](https://img.shields.io/badge/Blender-5.0%2B-orange.svg?style=flat-square&logo=blender)](https://www.blender.org/)
[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg?style=flat-square)](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

**Bake Helper** — это мощный и умный аддон для Blender 5, который автоматизирует процесс переноса текстур с High-poly на Low-poly объекты. Забудьте о ручной настройке выделения, поиске ошибок с черными текстурами и ручном подключении нод.

## ✨ Главные возможности

*   **🧠 Умное автоподключение:** После запекания текстура автоматически подключается к нужному входу Principled BSDF (Base Color, Roughness, Normal, AO и др.).
*   **🧹 Авто-выравнивание нод:** Ноды в Shader Editor выстраиваются в ровную цепочку `Image → Principled → Output` для идеального порядка.
*   **🌍 Двуязычный интерфейс:** Полная поддержка русского и английского языков. Переключение прямо в панели.
*   **🛡️ Предполётные проверки (Preflight):** Аддон заранее проверяет модель и исправляет типовые ошибки:
    *   *Автоматически обнуляет `Metallic = 1.0`* (главная причина черных текстур).
    *   *Включает видимость для рендера* (исправляет ошибку `is not enabled for rendering`).
    *   *Пересчитывает нормали* и проверяет пересечение bounding box.
    *   *Автоматически подбирает `Cage Extrusion`*, если значение слишком мало.
*   **🧵 Авто-UV:** Если у Low-poly нет развертки, аддон создаст её методом *Smart UV Project*.
*   **📦 Умное сохранение:** Сохраняет PNG рядом с `.blend` файлом или в папку Документы.

## 🖼️ Скриншоты
<!-- Раскомментируйте и добавьте свои картинки, если они есть -->
<!-- 
![Панель аддона](docs/panel.png)
![Выровненные ноды](docs/nodes.png)
-->

## 🚀 Установка

1. Скачайте файл **`bake_helper.zip`** со страницы [Releases](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/releases/latest).
2. Откройте Blender 5.0 или новее.
3. Перейдите в `Edit → Preferences → Add-ons`.
4. Нажмите стрелочку в правом верхнем углу и выберите **Install from Disk...** (Установить из диска).
5. Выберите скачанный `bake_helper.zip` и нажмите **Install**.
6. **Обязательно поставьте галочку** напротив аддона `Bake Helper: High → Low`, чтобы активировать его.

## 📖 Как пользоваться

1. Откройте боковую панель в 3D-вьюпорте (нажмите клавишу **`N`**).
2. Перейдите на вкладку **Bake**.
3. Выделите в сцене **два объекта**: сначала High-poly, затем с зажатым `Shift` — Low-poly (он должен стать активным).
4. Нажмите кнопку **«Взять из выделения»** — имена объектов подставятся автоматически.
5. Выберите **Тип карты** (например, Base Color).
6. Настройте желаемое разрешение и отступы (Margin).
7. Нажмите **«ЗАПЕЧЬ»**.

Аддон проведет проверку, запечет текстуру, подключит её к материалу и выровняет ноды.

## 🛠️ Технические детали и совместимость

| Параметр | Значение |
| :--- | :--- |
| **Версия Blender** | 5.0 и выше |
| **Движок рендера** | Cycles (переключается автоматически) |
| **Поддерживаемые карты** | Diffuse, Normal, Roughness, Metallic, AO, EMIT (Height) |

### ⚠️ Важно про карту высот (Displacement / Height)
Blender не умеет напрямую запекать тип `DISPLACEMENT` с High-poly на Low-poly. В аддоне этот пункт заменён на **Height / Displacement (Emit)**. 
Чтобы получить карту высот, подключите нужный сигнал (например, процедурную текстуру или `Geometry → Pointiness`) к узлу **Emission** в материале High-poly. Аддон запечет это как тип `EMIT` и автоматически поставит текстуре правильное цветовое пространство `Non-Color`.

### 🩺 Решение проблем (Troubleshooting)
*   **Текстура получилась черной:** Убедитесь, что у High-poly материала `Metallic` меньше 1.0 (аддон исправляет это автоматически, но если стоит галочка на текстуре — проверьте её). Также проверьте, что объекты не смещены друг относительно друга.
*   **Текстура «наползает» на соседние UV-острова:** Уменьшите `Margin` до `2` или `4` пикселей и выберите тип `Adjacent Faces`.
*   **Ошибка "Object is not enabled for rendering":** Аддон автоматически включает видимость для рендера. Если ошибка осталась, проверьте, не скрыт ли объект в исключенной коллекции (исключите коллекцию из `exclude`).

## 🤝 Участие в разработке (Contributing)
Если вы нашли баг или хотите предложить фичу — создайте [Issue](https://github.com/FAN-Nickolson/Baking-textures-in-Blender-5/issues). Pull requests приветствуются!

## 📄 Лицензия
Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).
