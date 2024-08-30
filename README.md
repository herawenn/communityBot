# PortLords Discord Bot Documentation

## I. Introduction

### A. Bot Overview

The PortLords Discord bot is a comprehensive cybersecurity companion for both enthusiasts and professionals. It offers a wide range of tools and resources to assist with various security-related tasks, including vulnerability scanning, exploit research, password cracking, and more.

### B. Core Features

* **Exploit Database Access:** Search and download exploits from ExploitDB.
* **Vulnerability Scanning:** Perform active scans using Shodan.
* **OSINT Tools:** Conduct OSINT investigations using Dehashed API.
* **Password Cracking:** Utilize tools like John the Ripper and Hydra for hash cracking and brute-forcing.
* **Code Obfuscation:** Obfuscate code in multiple programming languages.
* **AI Interaction:** Engage with PortLordsAI (powered by Google Gemini) for code assistance, vulnerability assessment, and general cybersecurity knowledge.
* **Server Moderation:** Basic moderation commands for managing users. 
* **Privacy Tools:** Provide guidance and tools for enhancing online privacy, including account removal and de-indexing assistance.
* **Community Engagement:**  Fun commands and tools for community interaction like quizzes, jokes, and reminders.
* **Role Management:** Allows users to self-assign roles based on their skill levels and interests.

## II. Getting Started

### A. Installation & Configuration

1. **Prerequisites:**
    * Python 3.8 or higher (recommended: 3.9+)
    * `discord.py` library: `pip install discord.py`
    * `shodan` library: `pip install shodan`
    * `requests` library: `pip install requests`
    * `aiohttp` library: `pip install aiohttp`
    * John the Ripper (community edition)
    * Hydra (password cracker)
    * PyArmor (Python code obfuscator)
    * Node.js and the `javascript-obfuscator` package (for JavaScript obfuscation)
    * Proguard (for Java obfuscation)
    * A Dehashed API key 
    * A Google Gemini API key (for PortLordsAI)
    * Maigret (for footprinting)

2. **Configuration File (`config.json`):**
    * Replace placeholders like `YOUR_DISCORD_BOT_TOKEN`, `YOUR_SHODAN_API_KEY`, `YOUR_DEHASHED_API_KEY`, and `YOUR_GEMINI_API_KEY` with your actual values.
    * Ensure your Dehashed and Gemini API keys are correctly configured in the `apis` section.
    * Configure the paths to your local resources (like ExploitDB data) in the `paths` section.

3. **Running the Bot:**
    * Open a terminal or command prompt.
    * Navigate to the bot's directory.
    * Execute `python bot.py` (or the equivalent command for your Python installation).

## III. Commands

### A. Security Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `shodanhost`        | Gets detailed information about a host from Shodan.     | `shodanhost <ip_address>`                 |
| `shodansearch`      | Performs a Shodan search using a given query.           | `shodansearch <query>`                    |
| `shodanscan`        | Initiates a Shodan scan on a specific IP.               | `shodanscan <ip_address>`                 |
| `shodanscanstatus`  | Checks the status of a Shodan scan by ID.               | `shodanscanstatus <scan_id>`              |
| `shodanscanresults` | Retrieves the results of a completed Shodan scan.       | `shodanscanresults <scan_id>`             |
| `shodanhelp`        | Displays help information for the Shodan commands.      | `shodanhelp`                              |
| `categories`        | Lists available exploit categories from ExploitDB.      | `categories`                              |
| `exploits`          | Searches for exploits in ExploitDB using a keyword.     | `exploits <keyword>`                      |
| `download`          | Downloads an exploit by its ID from ExploitDB.          | `download <exploit_id>`                   |
| `recon`             | Performs network reconnaissance using Nmap.             | `recon <target> [options]`                |
| `reconhelp`         | Displays help information for the `recon` command.      | `reconhelp`                               |
| `cancelscan`        | Cancels ongoing Nmap scans.                             | `cancelscan`                              |
| `aiscan`            | Generates a vulnerability assessment for an IP address. | `aiscan <ip_address>`                       |


### B. Moderation Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `kick`      | Kicks a user from the server.                 | `kick <user> [reason]`                |
| `ban`       | Bans a user from the server.                  | `ban <user> [reason]`                 |
| `unban`     | Unbans a user from the server.                | `unban <user#discriminator>`          |
| `mute`      | Mutes a user in the server.                   | `mute <user> [reason]`                |
| `unmute`    | Unmutes a user in the server.                 | `unmute <user> [reason]`              |
| `clear`     | Deletes a specified number of messages.       | `clear <amount>`                      |
| `warn`      | Issues a warning to a user.                   | `warn <user> [reason]`                |

### C. Tools Commands

| Command      | Description                                              | Usage                                       |
| :----------- | :------------------------------------------------------- | :------------------------------------------ |
| `obfuscate`  | Obfuscates the source code of an attached file.          | `obfuscate` (attach the file to obfuscate)  |
| `chat`       | Interacts with PortLordsAI (powered by Google Gemini).   | `chat <message>`                            |
| `aiscan`     | Generates a vulnerability report for a given IP address. | `aiscan <ip_address>`                       |
| `build`      | Creates an executable from a given Python file.          | `build` (follow prompts)                    |

### D. OSINT Commands

| Command  | Description                                             | Usage                         |
| :------- | :------------------------------------------------------ | :---------------------------- |
| `search` | Searches for leaked data using the Dehashed API.        | `search <query_type> <query>` |
| `footprint` |  Searches your digital footprint online.             | `footprint <username>`        | 
| `removeaccount` | Provides instructions for removing accounts.     | `removeaccount <platform>`    |
| `deindex` |  Guides you on de-indexing information from Google.    | `deindex`                     |

### E. Community Commands

| Command      | Description                                 | Usage                                 |
| :----------- | :------------------------------------------ | :------------------------------------ |
| `ping`       | Checks the bot's latency.                   | `ping`                                |
| `joke`       | Tells a developer joke.                     | `joke`                                |
| `dice`       | Rolls a 6-sided dice.                       | `dice`                                |
| `8ball`      | Asks the Magic 8 Ball a question.           | `8ball <question>`                    |
| `coinflip`   | Flips a coin.                               | `coinflip`                            |
| `remind`     | Sets a reminder.                            | `remind <time> <message>`             |
| `userinfo`   | Gets information about a user.              | `userinfo [member]`                   |
| `serverinfo` | Gets information about the server.          | `serverinfo`                          |
| `quiz`       | Starts a cybersecurity quiz.                | `quiz`                                |
| `testtip`    |  Tests the security tip of the day.         | `testtip`                             | 

### F. Admin Commands

| Command        | Description                                               | Usage                 |
| :------------- | :-------------------------------------------------------- | :-------------------- |
| `help`         | Displays an overview of the bot's commands.               | `help`                |
| `verification` | Manages user verification and role assignment.            | `verification`        |
| `reload`       | Reloads all cogs (extensions) or a specific cog.          | `reload [cog_name]`   |
| `adduser`    |  Adds a user to the database.                               | `adduser <user_id> <username>`                         |
| `getuser`     | Retrieves information about a user.                        | `getuser <user_id>`                                    | 
| `updateuserpoints` | Updates a user's points in the database.              | `updateuserpoints <user_id> <points>`                  |
| `updateusertier` | Updates a user's tier in the database.                  | `updateusertier <user_id> <tier>`                      |
| `updateuserverified` | Updates a user's verified status.                   | `updateuserverified <user_id> true/false`              | 
| `updateusermuteduntil` | Updates a user's muted timestamp.                 | `updateusermuteduntil <user_id> <YYYY-MM-DD HH:MM:SS>` |
| `updateuserbanreason` | Updates a user's ban reason.                       | `updateuserbanreason <user_id> <reason>`               |
| `updateuserwarncount` | Updates a user's warn count.                       | `updateuserwarncount <user_id> <warn_count>`           |
| `embed`        |  Sends the code obfuscation embed to channel.             | `embed`                 |
| `tiers`        |  Displays the tier structure of the server.               | `tiers`                 |
| `report`      |  Submits a bug report.                                     | `report <your message>` |


## IV. Advanced Features

### A. AI Integration (PortLordsAI)

PortLordsAI, powered by Google Gemini, integrates conversational AI capabilities into the bot. Interact with it using the `!chat` command. Key features include:

* **Code Generation & Assistance:** Request code snippets, get help with debugging, and troubleshoot code-related issues.
* **Vulnerability Assessments:** Use the `!aiscan` command for high-level vulnerability reports on provided IP addresses.
* **General Cybersecurity Knowledge:** Ask questions about cybersecurity concepts or request definitions.

**Important Considerations:**

* **Limitations:** The AI model has limitations, and its responses might not always be perfect or suitable for production use. Always double-check its outputs.
* **Biases:** AI models are trained on vast datasets and can reflect biases present in those datasets. Be aware that responses are not always objective.

### B. Exploit Database Management

The bot accesses a local copy of the ExploitDB database (in `.csv` format).  It's crucial to keep this database up-to-date to ensure access to the latest exploits. Download the latest version from ExploitDB's website ([https://www.exploit-db.com/](https://www.exploit-db.com/)).

### C. Shodan Integration

Shodan integration empowers the bot for network scanning and reconnaissance.  Use these Shodan commands effectively:

* **Shodan API Key:** Ensure you have a valid Shodan API key configured in your `config.json` file.
* **Targeted Searches:** When using `!shodansearch`, provide specific search queries for accurate results.  Examples:
    *  Search by software: `!shodansearch apache`
    *  Search by vulnerability: `!shodansearch "cve:2021-44228"`
    *  Search by port: `!shodansearch port:22` 

### D. Password Cracking

The bot offers password cracking functionality using John the Ripper and brute-force capabilities using Hydra. 

* **Wordlists:** The effectiveness of password cracking largely depends on the quality of the wordlists provided. Customize the wordlist path in `config.json`.
* **Hash Types:** When using John the Ripper, you can optionally specify the hash format using the `[hash_type]` argument. Refer to John the Ripper's documentation for supported hash types. 
* **Brute-force Attacks:** Utilize the `!brute` command with the target IP address, port, and service to initiate a brute-force attack using Hydra. 

### E. Obfuscation

The bot provides code obfuscation for several programming languages. 

* **Language Support:** Currently supports Python, JavaScript, Java, Go, and Rust.
* **Limitations:** Obfuscation makes code more challenging to read, but it doesn't make it impossible to reverse engineer. Deobfuscation tools and techniques exist.

### F. Dehashed Integration

The bot enables you to search for leaked data using the Dehashed API through the `!search` command. Provide the query type (e.g., 'email', 'username', 'password') and your query to retrieve related information. 

## V. To-Do List

Here's a list of features and enhancements planned for future versions of the bot:

* **[High Priority]** Implement automatic updates for the ExploitDB database.
* **[High Priority]** Add error handling to Shodan commands to gracefully handle API limits and connection issues.
* **[Medium Priority]** Expand AI capabilities:
    * Explore using the AI for basic malware analysis (e.g., identifying potentially malicious strings in code).
    * Research integrating with a service like VirusTotal for file analysis.
* **[Low Priority]** Design and implement the `!phish` command.
* **[Low Priority]** Create a web-based dashboard for managing the bot, viewing logs, and potentially controlling some functionalities remotely.

**Note:** Priorities are subject to change based on user feedback and development progress.

### Support

For questions, support, or to report issues, please join the [PortLords Discord Server](https://discord.gg/portlords)

### Disclaimer

This Discord bot is provided "as is" for educational and research purposes only. By using this bot, you acknowledge that you are solely responsible for your actions and that you will comply with all applicable laws and regulations.
