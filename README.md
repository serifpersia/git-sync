# git-sync

A simple, cross-platform command-line tool to back up and sync your public GitHub repositories.


## Usage

First, ensure you have Python 3 installed on your system.

### Windows

1.  Open Command Prompt (`cmd.exe`) or PowerShell.
2.  Navigate to the `git-sync` directory.
3.  Run the command, providing the path to your backup folder:
    ```shell
    run.bat -b "C:\Path\To\Your\Backups"
    ```

### Linux / macOS

1.  Open your terminal.
2.  Navigate to the `git-sync` directory.
3.  Make the script executable (you only need to do this once):
    ```shell
    chmod +x run.sh
    ```
4.  Run the command, providing the path to your backup folder:
    ```shell
    ./run.sh -b "/path/to/your/backups"
    ```

**Note:** The backup directory must now be specified using the `-b` or `--backup-dir` flag. Always quote paths that contain spaces.

### First Run

The first time you run the tool on a new backup directory, it will prompt you to enter the GitHub username you wish to sync.

It will then create a `config.json` file in that directory to store your settings. Subsequent runs in that same directory will use the saved configuration.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
