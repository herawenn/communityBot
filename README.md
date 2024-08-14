# PortLords Discord Bot Documentation

## I. Introduction

### A. Bot Overview

The PortLords Discord bot is designed as a comprehensive cybersecurity companion, catering to both enthusiasts and professionals. It provides an array of tools and resources to aid in various security-related tasks, including vulnerability scanning, exploit research, password cracking, and more.

### B. Core Features

*   **Exploit Database Access:** Search and download exploits from ExploitDB.
*   **Vulnerability Scanning:** Perform active scans using Shodan.
*   **Password Cracking:** Utilize tools like John the Ripper for hash cracking.
*   **Code Obfuscation:** Obfuscate code in multiple programming languages.
*   **AI Interaction:** Engage with the PortLordsAI model for code assistance, vulnerability assessment, and general knowledge.
*   **Server Moderation:**  Basic moderation commands for managing users. 

## II. Getting Started

### A. Installation & Configuration

1.  **Prerequisites:**
    *   Python 3.8 or higher (recommended: 3.9+)
    *   `discord.py` library: `pip install discord.py`
    *   `shodan` library: `pip install shodan`
    *   `requests` library: `pip install requests` 
    *   John the Ripper (community edition)
    *   Hydra (password cracker)
    *   PyArmor (Python code obfuscator)
    *   Node.js and the `javascript-obfuscator` package (for JavaScript obfuscation) 
    *   Proguard (for Java obfuscation)

2.  **Configuration File (`config.json`):**

    *   Replace placeholders like `YOUR_DISCORD_BOT_TOKEN`, `YOUR_SHODAN_API_KEY`, etc. with your actual values.

3.  **Running the Bot:**
    *   Open a terminal or command prompt.
    *   Navigate to the bot's directory.
    *   Execute `python bot.py` (or the equivalent command for your Python installation). 

## III. Commands

Below is a categorized list of all the commands available within the PortLords Discord bot:

### A. Security Commands

| Command              | Description                                             | Usage                                      |
| :------------------- | :------------------------------------------------------ | :----------------------------------------- |
| `!brute`             | Attempts to brute-force a service on an IP address.     | `!brute <ip_address> <port> <service>`     |
| `!brutehelp`         | Displays help information for the `!brute` command.     | `!brutehelp`                               |
| `!cancelscan`        | Cancels ongoing brute force scans.                      | `!cancelscan`                              |
| `!categories`        | Lists available exploit categories from ExploitDB.      | `!categories`                              |
| `!exploits`          | Searches for exploits in ExploitDB using a keyword.     | `!exploits <keyword>`                      |
| `!download`          | Downloads an exploit by its ID from ExploitDB.          | `!download <exploit_id>`                   |
| `!shodanhost`        | Gets detailed information about a host from Shodan.     | `!shodanhost <ip_address>`                 |
| `!shodanhelp`        | Displays help information for the Shodan commands.      | `!shodanhelp`                              |
| `!shodansearch`      | Performs a Shodan search using a given query.           | `!shodansearch <query>`                    |
| `!shodanscan`        | Initiates a Shodan scan on a specific IP.               | `!shodanscan <ip_address>`                 |
| `!shodanscanstatus`  | Checks the status of a Shodan scan by ID.               | `!shodanscanstatus <scan_id>`              |
| `!shodanscanresults` | Retrieves the results of a completed Shodan scan.       | `!shodanscanresults <scan_id>`             |

### B. Moderation Commands:

| Command      | Description                                      | Usage                                  |
| :----------- | :----------------------------------------------- | :------------------------------------- |
| `!kick`      | Kicks a user from the server.                    | `!kick <user> [reason]`                |
| `!ban`       | Bans a user from the server.                     | `!ban <user> [reason]`                 |
| `!unban`     | Unbans a user from the server.                   | `!unban <user#discriminator>`          |
| `!mute`      | Mutes a user in the server.                      | `!mute <user> [reason]`                |
| `!unmute`    | Unmutes a user in the server.                    | `!unmute <user> [reason]`              |
| `!clear`     | Deletes a specified number of messages.          | `!clear <amount>`                      |
| `!warn`      | Issues a warning to a user.                      | `!warn <user> [reason]`                |

### C. Tools Commands:

| Command      | Description                                              | Usage                                       |
| :----------- | :------------------------------------------------------- | :------------------------------------------ |
| `!obfuscate` | Obfuscates the source code of an attached file.          | `!obfuscate` (attach the file to obfuscate) |
| `!crack`     | Attempts to crack a provided hash.                       | `!crack <hash> [hash_type]`                 |
| `!phish`     | \[Incomplete/Potentially Dangerous].                     |                                             |

### D. Support Commands:

| Command | Description                                                                     | Usage              |
| :------- | :----------------------------------------------------------------------------- | :----------------- |
| `!chat`  | Interacts with PortLordsAI (powered by Google Gemini).                         | `!chat <message>`  |
| `!help`  | Displays a help menu providing an overview of the bot's commands.              | `!help`            |

### E. Admin Commands:

| Command         | Description                                                         | Usage                  |
| :-------------- | :------------------------------------------------------------------ | :--------------------- |
| `!embeds`       | Triggers specific embed messages for designated channels.           | `!embeds <embed_name>` |
| `!verification` | Manages user verification and role assignment.                      | `!verification`        |
| `!reload`       | Reloads all cogs (extensions) or a specific cog.                    | `!reload [cog_name]`   |

## IV. Advanced Features

### A. AI Integration (PortLordsAI)

The PortLordsAI model, powered by Google Gemini, introduces conversational AI capabilities to the bot. You can engage with PortLordsAI using the `!chat` command. It can assist with tasks such as: 

*   **Code Generation & Assistance:**  Request code snippets or get help with debugging. 
*   **Vulnerability Assessments:**  Use the `!aiscan` command to request a vulnerability assessment. Keep in mind this is a *high-level assessment.*
*   **General Knowledge:** Ask general cybersecurity questions or get definitions.

**Important Considerations:**

*   **Limitations:** The AI model has limitations. Its responses might not always be perfect or suitable for production use. Always double-check its outputs.
*   **Biases:** AI models are trained on vast datasets and can reflect biases present in those datasets. Be aware that responses are not always objective. 

### B. Exploit Database Management

The bot accesses a local copy of an ExploitDB database (in `.csv` format). It's crucial to keep this database up-to-date. You can download the latest version from ExploitDB's website (\[https://www.exploit-db.com/](https://www.exploit-db.com/)). 

### C. Shodan Integration 

Shodan integration allows for powerful network scanning and reconnaissance. Here's how to use the Shodan commands effectively:

*   **Shodan API Key:** Ensure you have a valid Shodan API key in your `config.json` file. 
*   **Targeted Searches:**  When using `!shodansearch`, provide specific queries for better results. Examples: 
    *   Search by software: `!shodansearch apache` 
    *   Search by vulnerability: `!shodansearch "cve:2021-44228"` 
    *   Search by port: `!shodansearch port:22`

### D. Password Cracking

The bot provides basic password cracking functionality using John the Ripper.

*   **Wordlists:** The effectiveness depends heavily on the wordlists provided. You can customize the wordlist path in `config.json`.
*   **Hash Types:**  Use the `[hash_type]` argument (optional) to specify the hash format. Refer to John the Ripper's documentation for supported hash types.

### E. Obfuscation

The bot offers code obfuscation for various programming languages.

*   **Language Support:**  Currently supports: Python, JavaScript, Java, Go, Rust.
*   **Limitations:**  Obfuscation makes code harder to read but does not make it impossible to reverse engineer. Deobfuscation tools and techniques exist. 

## V. To-Do List

Here's a list of features and enhancements planned for future versions of the bot: 

*   **[High Priority]** Implement automatic updates for the ExploitDB database.
*   **[High Priority]**  Add error handling to Shodan commands to gracefully handle API limits and connection issues.
*   **[Medium Priority]**  Expand AI capabilities:
    *   Explore using the AI for basic malware analysis (e.g., identifying potentially malicious strings in code).
    *   Research integrating with a service like VirusTotal for file analysis. 
*   **[Low Priority]** Design and implement the `!phish` command.
*   **[Low Priority]**  Create a web-based dashboard for managing the bot, viewing logs, and potentially controlling some functionalities remotely.

**Note:** Priorities are subject to change based on user feedback and development progress. 

### Support:

For questions, support, or to report issues, please join the [PortLords Discord Server](https://discord.gg/portlords)

### Disclaimer:

This Discord bot is provided "as is" for educational and research purposes only. By using this bot, you acknowledge that you are solely responsible for your actions and that you will comply with all applicable laws and regulations. 
