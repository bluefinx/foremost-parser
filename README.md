# ⚡Foremost Parser
![](./resources/logos/fmparser.png)

`fmparser` parses Foremost audit file and carved files 🗂️, extracts metadata 🔍, detects duplicates ⚡ and generates a detailed report 📊.

## Features

🗂️ parses Foremost audit files<br>
🔧 extracts Metadata for all files using **ExifTool** or Python as fallback<br>
🔍 detects Duplicate files<br>
⚡ uses Batch processing for better performance<br>
📊 generates a detailed report with overview for each file (*work in progress*)<br>
🐳 is Platform independent thanks to **Docker Compose**<br>

## Active Development & Roadmap

`fmparser` is currently in **active development** and considered a **first beta version**.
The tool is still being tested and some features are **work in progress**.  

For detailed information, see the [Roadmap](ROADMAP.md).

## Installation & Usage

1. Make sure Docker is installed on your system 
2. Download the `fmparser` repository
3. Navigate to the `fmparser` directory

### For Linux/Unix

4. Make the main script executable:

```bash
chmod +x fmparser.sh
```

5. Run the tool via the shell script:

```bash
./fmparser.sh -i [input-folder] -o [output-folder]
```

The `--help` command shows all available parameters and options. 

### For PowerShell

4. Make the PowerShell script *executable* or check the *execution policy*
5. Run the tool via the PowerShell script:

```powershell
./fmparser.ps1 -InputPath [input-folder] -OutputPath [output-folder]
```

The `Get-Help` command shows all available parameters and options.

>  [!NOTE] 
>
> For further information about the tool's architecture, see [Architecture](./ARCHITECTURE.md) and the [docs](./docs/html/index.html).

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) © 2025 bluefinx.

See the [LICENSE](LICENSE) file for details.
