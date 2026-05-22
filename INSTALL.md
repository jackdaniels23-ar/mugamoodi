# Install Mugamoodi On Linux

Mugamoodi is a dependency-free Python 3 CLI tool. You only need `git` and `python3`.

## 1. Check Requirements

```bash
python3 --version
git --version
```

If Python is missing on Debian/Ubuntu/Kali:

```bash
sudo apt update
sudo apt install python3 git
```

## 2. Clone The Repository

```bash
git clone https://github.com/jackdaniels23-ar/mugamoodi.git
cd mugamoodi
```

## 3. Make It Executable

```bash
chmod +x mugamoodi
```

## 4. Run Mugamoodi

Start with help:

```bash
./mugamoodi --help
```

Use the interactive two-question mode:

```bash
./mugamoodi mask
```

Mugamoodi will ask:

```text
1. URL to be changed: https://example.com
2. Masking website: https://my-site.com
Alias slug (press Enter for random): demo
```

Expected output:

```text
[ok] Alias created
        masked  https://my-site.com/demo
   destination  https://example.com
```

Then check or manage the alias:

```bash
./mugamoodi reveal demo
./mugamoodi list
./mugamoodi remove demo
```

You can also run it directly without prompts:

```bash
./mugamoodi mask https://example.com -a demo
./mugamoodi reveal demo
./mugamoodi list
```

## 5. Install Globally

This lets you run `mugamoodi` from any folder:

```bash
sudo ln -s "$PWD/mugamoodi" /usr/local/bin/mugamoodi
mugamoodi --help
```

After global install, use:

```bash
mugamoodi mask
mugamoodi list
```

## Update

From inside the repo:

```bash
git pull
```

## Uninstall

If you installed the global command:

```bash
sudo rm /usr/local/bin/mugamoodi
```

Then remove the cloned folder:

```bash
cd ..
rm -rf mugamoodi
```

## Data Location

Mugamoodi stores aliases here by default:

```text
~/.local/share/mugamoodi/links.json
```

Use a custom storage folder:

```bash
MUGAMOODI_HOME="$PWD/.data" mugamoodi list
```
