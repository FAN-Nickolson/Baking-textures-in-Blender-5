\# Bake Helper: High → Low



Аддон Blender 5 для запекания текстур с high-poly объекта на low-poly

с предполётными проверками и автоматическим созданием UV.



\# Bake Helper: High → Low



Blender 5 add‑on for baking textures from a high‑poly object to a low‑poly one, with pre‑flight checks and automatic UV generation.



\## Installation



1\. Download the `bake\_helper/` folder in its entirety.

2\. Copy it to:

&#x20;  - \*\*Windows:\*\* `%APPDATA%\\Blender Foundation\\Blender\\5.0\\scripts\\addons\\`

&#x20;  - \*\*Linux:\*\* `\~/.config/blender/5.0/scripts/addons/`

&#x20;  - \*\*macOS:\*\* `\~/Library/Application Support/Blender/5.0/scripts/addons/`

3\. In Blender: `Edit → Preferences → Add-ons` → enable \*\*Bake Helper: High → Low\*\*.



Or pack the folder in `.zip` (the `bake\_helper/` folder itself must be inside the zip) and install via `Preferences → Add-ons → Install...`.



\## Usage



1\. Open the N-sidebar in the 3D view (`N`), tab \*\*Bake\*\*.

2\. Select two objects: high-poly and low-poly (low is active).

3\. Click \*\*“Take from Selection”\*\* — the names will be filled in.

4\. Configure the map type, UV, and margin.

5\. Click \*\*“BAKE”\*\*.



\## Auto‑checks



When launched, the script checks and automatically fixes:

\- Metallic = 1.0 in high‑poly (resets for the baking time)

\- Cage Extrusion = 0 or too small (increases)

\- Inverted normals (recalculates outward)

\- Low-poly's lack of UV (creates via Smart UV Project)



Critical issues (no UV, Base Color = black, objects do not intersect)

are shown in the pre-check window and block baking.



\## License



MIT







\## Установка



1\. Скачайте папку `bake\_helper/` целиком.

2\. Скопируйте её в:

&#x20;  - \*\*Windows:\*\* `%APPDATA%\\Blender Foundation\\Blender\\5.0\\scripts\\addons\\`

&#x20;  - \*\*Linux:\*\* `\~/.config/blender/5.0/scripts/addons/`

&#x20;  - \*\*macOS:\*\* `\~/Library/Application Support/Blender/5.0/scripts/addons/`

3\. В Blender: `Edit → Preferences → Add-ons` → включите \*\*Bake Helper: High → Low\*\*.



Или запакуйте папку в `.zip` (сама папка `bake\_helper/` должна быть внутри zip) и

установите через `Preferences → Add-ons → Install...`.



\## Использование



1\. Откройте N-сайдбар в 3D-вьюпорте (`N`), вкладка \*\*Bake\*\*.

2\. Выделите два объекта: high-poly и low-poly (low активный).

3\. Нажмите \*\*«Взять из выделения»\*\* — имена подставятся.

4\. Настройте тип карты, UV, margin.

5\. Нажмите \*\*«ЗАПЕЧЬ»\*\*.



\## Автопроверки



При запуске скрипт проверяет и автоматически исправляет:

\- Metallic = 1.0 у high-poly (обнуляет на время запекания)

\- Cage Extrusion = 0 или слишком мал (увеличивает)

\- Перевёрнутые нормали (пересчитывает наружу)

\- Отсутствие UV у low-poly (создаёт через Smart UV Project)



Критические проблемы (нет UV, Base Color = чёрный, объекты не пересекаются)

показываются в окне предпроверки и блокируют запекание.



\## Лицензия



MIT

