# 🛢️ ANH Bolivia — Dashboard de Producción por Campo

Dashboard interactivo de producción de hidrocarburos de Bolivia.  
**Tecnología:** HTML + JavaScript puro (sin backend). Se puede alojar en GitHub Pages de forma gratuita.

---

## 📁 Archivos del proyecto

```
ANH_Bolivia_Dashboard.html    ← Dashboard principal (abrir en cualquier navegador)
actualizar_dashboard.py       ← Script de actualización automática
PRODUCCION_POR_CAMPO.accdb    ← Base de datos Access (NO subir a GitHub público)
.gitignore                    ← Excluye el .accdb del repositorio
```

---

## 🚀 Paso 1 — Subir a GitHub Pages

### 1.1 Crear el repositorio

1. Ir a [github.com](https://github.com) → **New repository**
2. Nombre sugerido: `anh-dashboard`
3. Visibilidad: **Public** (necesario para GitHub Pages gratis)
4. No inicializar con README (lo haremos manualmente)

### 1.2 Inicializar y subir desde tu computadora

Abre una terminal (CMD, PowerShell o Terminal) en la carpeta donde están los archivos:

```bash
# Inicializar repositorio local
git init
git add ANH_Bolivia_Dashboard.html actualizar_dashboard.py README.md .gitignore

# Primer commit
git commit -m "Dashboard ANH Bolivia - versión inicial"

# Conectar con GitHub (reemplazar con tu usuario y nombre de repositorio)
git remote add origin https://github.com/TU_USUARIO/anh-dashboard.git
git branch -M main
git push -u origin main
```

### 1.3 Activar GitHub Pages

1. En tu repositorio → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `/ (root)`
4. Clic en **Save**

⏳ En 2-3 minutos el dashboard estará disponible en:
```
https://TU_USUARIO.github.io/anh-dashboard/ANH_Bolivia_Dashboard.html
```

Esa URL funciona en **cualquier dispositivo** (PC, tablet, celular).

---

## 🔄 Paso 2 — Actualizar el dashboard cuando cambia el .accdb

### Requisitos previos (solo una vez)

**Linux / macOS:**
```bash
# Ubuntu/Debian
sudo apt install mdbtools

# macOS
brew install mdbtools

# Python
pip install mdbtools-python
```

**Windows:**
```
Opción A (recomendada): Usar WSL2
  1. Instalar WSL2: wsl --install
  2. Abrir terminal Ubuntu y seguir instrucciones de Linux arriba

Opción B: Docker
  1. Instalar Docker Desktop
  2. docker run --rm -v "%CD%":/data ubuntu bash -c "apt-get install -y mdbtools && python3 /data/actualizar_dashboard.py"
```

### Ejecutar la actualización

```bash
# Actualizar solo el dashboard (sin push automático)
python actualizar_dashboard.py

# Especificar rutas personalizadas
python actualizar_dashboard.py --accdb "C:/datos/PRODUCCION_POR_CAMPO.accdb" --html "ANH_Bolivia_Dashboard.html"

# Actualizar Y hacer push automático a GitHub en un solo comando
python actualizar_dashboard.py --push
```

### ¿Qué hace el script?

1. Lee el archivo `.accdb` con `mdb-export`
2. Recalcula TODOS los datos: anuales, mensuales, por campo, por región, por operador
3. Inyecta los datos actualizados dentro del HTML (reemplaza el bloque `const DB=...`)
4. (Opcional) Hace `git add`, `git commit`, `git push` automáticamente

---

## ⏰ Paso 3 — Automatización programada (opcional)

Si quieres que se actualice automáticamente sin intervención manual:

### Windows — Programador de Tareas

```
1. Abrir "Programador de tareas" → Crear tarea básica
2. Nombre: "ANH Dashboard Update"
3. Desencadenador: Mensual (o el intervalo deseado)
4. Acción: Iniciar programa
   Programa: python
   Argumentos: C:\ruta\actualizar_dashboard.py --push
   Iniciar en: C:\ruta\
```

### Linux/macOS — Cron

```bash
# Editar crontab
crontab -e

# Ejecutar el primer día de cada mes a las 8:00 AM
0 8 1 * * cd /ruta/proyecto && python actualizar_dashboard.py --push

# O cada semana los lunes
0 8 * * 1 cd /ruta/proyecto && python actualizar_dashboard.py --push
```

### GitHub Actions (actualización desde la nube)

Si tienes el `.accdb` en un servidor o SharePoint accesible, puedes crear un workflow:

```yaml
# .github/workflows/update.yml
name: Actualizar Dashboard
on:
  schedule:
    - cron: '0 8 1 * *'   # primer día de cada mes a las 8 AM UTC
  workflow_dispatch:        # también permite ejecutar manualmente desde GitHub

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Instalar mdbtools
        run: sudo apt-get install -y mdbtools
      - name: Descargar .accdb actualizado
        run: |
          # Ejemplo: descargar desde una URL (SharePoint, servidor, etc.)
          # curl -o PRODUCCION_POR_CAMPO.accdb "${{ secrets.ACCDB_URL }}"
      - name: Actualizar dashboard
        run: python actualizar_dashboard.py
      - name: Push cambios
        run: |
          git config user.name "ANH Bot"
          git config user.email "bot@anh.gob.bo"
          git add ANH_Bolivia_Dashboard.html
          git diff --staged --quiet || git commit -m "Actualización automática $(date +%Y-%m-%d)"
          git push
```

---

## 🔒 Seguridad — El .accdb NO va al repositorio

El archivo `.gitignore` ya incluye:

```
*.accdb
*.mdb
```

Esto evita que la base de datos con información sensible sea publicada en GitHub.

---

## 📋 Flujo de trabajo resumido

```
Tu computadora                         GitHub
─────────────────────────────────────────────────────
1. Recibes nuevo .accdb del sistema ANH
2. python actualizar_dashboard.py --push
   ├── Lee .accdb
   ├── Recalcula todos los datos
   ├── Actualiza el HTML
   └── git push ──────────────────→ GitHub Pages actualiza
                                    URL pública disponible
                                    en ~30 segundos
```

---

## 📞 Soporte técnico

Si hay problemas con `mdbtools` en Windows, la alternativa más simple es:
1. Instalar **WSL2** (subsistema Linux para Windows)
2. Correr el script dentro de WSL2

Esto garantiza compatibilidad total con el formato `.accdb`.
