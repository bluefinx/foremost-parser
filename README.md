# ⚡Foremost Parser
![](./resources/logos/fmparser.png)

`fmparser` parses Foremost outputs and audit files 🗂️, extracts metadata 🔍, detects duplicates ⚡ and generates a detailed report 📊.

## Features

🗂️ parses Foremost audit files
🔧 Metadata for all files is extracted using **ExifTool** or Python as fallback
🔍 Duplicate files are detected
⚡ Batch processing for better performance
📊 Generates a detailed report with overview for each file (*work in progress*)
🐳 Platform independent thanks to **Docker Compose**

## Active Development & Roadmap

`fmparser` is currently in **active development** and considered a **first beta version**.
The tool is still being tested and some features are **work in progress**.  

For detailed information, see the [Roadmap](ROADMAP.md).

## Installation & Usage

1. Make sure Docker is installed on your system 🐳  
2. Download the `fmparser` repository  
3. Make the main script executable:

```bash
chmod +x fmparser.sh
```

Run the tool via the shell script:

```bash
./fmparser.sh -i [input-folder] -o [output-folder]
```

The `--help` command shows all available parameters and options. 

> [!NOTE]
>
> A PowerShell script is not yet available.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) © 2025 bluefinx.

See the [LICENSE](LICENSE) file for details.
