# Mugamoodi

A small, stylish, transparent URL alias tool for your terminal. Mugamoodi creates memorable local aliases and stores the real destination on your machine.

```text
+----------------------------------------------------------------------------+
| Mugamoodi :: transparent URL aliases for your terminal                      |
+----------------------------------------------------------------------------+

[ok] Alias created
        masked  https://mugamoodi.local/demo
   destination  https://example.com
```

## Linux Install

Clone the repo, make the launcher executable, then run it:

```bash
git clone https://github.com/YOUR-USERNAME/mugamoodi.git
cd mugamoodi
chmod +x mugamoodi
./mugamoodi --help
```

Optional: put it somewhere on your `PATH`:

```bash
sudo ln -s "$PWD/mugamoodi" /usr/local/bin/mugamoodi
mugamoodi --help
```

## Usage

```bash
./mugamoodi mask example.com -a demo
./mugamoodi reveal demo
./mugamoodi list
./mugamoodi remove demo
```

By default, aliases are displayed as `https://mugamoodi.local/<alias>`. You can change the shown base URL:

```bash
./mugamoodi --base-url https://go.local mask https://example.com -a docs
```

The destination is always shown when an alias is created, listed, or revealed.

## Terminal Style

Mugamoodi uses ANSI colors when your terminal supports them. Disable colors with:

```bash
NO_COLOR=1 ./mugamoodi list
```

## Storage

On Linux, aliases are stored in:

```text
~/.local/share/mugamoodi/links.json
```

You can override this with `MUGAMOODI_HOME`:

```bash
MUGAMOODI_HOME="$PWD/.data" ./mugamoodi list
```

## Windows

The Windows wrapper is still included:

```powershell
.\mugamoodi.cmd list
```

## Push To GitHub

After creating an empty GitHub repository named `mugamoodi`, run:

```bash
git init
git add .
git commit -m "Initial Mugamoodi CLI"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mugamoodi.git
git push -u origin main
```
