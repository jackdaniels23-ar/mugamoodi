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

```bash
./mugamoodi --help
./mugamoodi mask
./mugamoodi mask https://example.com -a demo
./mugamoodi reveal demo
./mugamoodi list
```

Interactive mode asks for:

```text
1. URL to be changed
2. Masking website
```

## 5. Install Globally

This lets you run `mugamoodi` from any folder:

```bash
sudo ln -s "$PWD/mugamoodi" /usr/local/bin/mugamoodi
mugamoodi --help
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
