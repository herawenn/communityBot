# PortLords Discord Bot 🤖

Thanks for checking out the bot! Its your ultimate Discord bot for cybersecurity exploration, learning, and community building. Whether you're a seasoned pro or just starting your cybersecurity journey, PortLords AI empowers you with a suite of powerful tools and features:

## Features 🗝️

**1. Open Source Intelligence (OSINT) & Reconnaissance**

* **Dehashed Search:**  Dive into leaked databases for OSINT. Search by email, username, and more.
* **Username Footprint:** Identify your online presence across hundreds of sites.
* **Privacy Removal:** Access links to remove your data from popular data brokers and services.
* **HIBP Breach Check:** Verify if your email has been involved in data breaches using Have I Been Pwned.
* **Password Strength:** Analyze the strength of your passwords.
* **Shodan Insights:** Explore detailed host information, vulnerabilities, and more.
* **Censys Intelligence:** Search for devices and vulnerabilities using Censys.
* **Ask Censys GPT:** Get search query suggestions from a powerful AI.
* **Nmap Scanning:** Perform network reconnaissance with customizable scans.
* **Visual Nmap Output:** Get a visual representation of scan results on a world map.

**2. Exploit Database & Security Learning**

* **ExploitDB Exploration:** Search for exploits by keyword, browse categories, and download files.
* **Cybersecurity Quiz:** Test your knowledge with daily quizzes and earn points.
* **Leaderboard:** Track your progress and see the top performers.
* **Privacy Tips:** Get regular, insightful privacy tips and best practices.

**3. AI-Powered Tools & Resources**

* **Chat with PortLordsAI:** Engage in conversation, ask questions, and get assistance.
* **Code Generation:** Generate code snippets and leverage AI coding help.
* **Linux Terminal:** Use an AI-powered Linux terminal to execute commands.
* **Hash Cracking:**  Attempt to crack hashes using Hashcat.
* **Proxy Retrieval:** Retrieve a list of working proxies.

**4. Community Engagement & Moderation**

* **Reaction Roles:** Easily self-assign roles based on your interests and skill levels.
* **Server Management:** Utilize essential moderation tools like kick, ban, mute, warn, and message clearing.

## Getting Started 🚀

1. **Prerequisites:**
    * **Python 3.8+:**  Download and install Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)
    * **Discord.py:** Install the Discord.py library using `pip install discord.py`
    * **SQLite3:**  SQLite3 is built into Python, no additional installation is needed.
    * **API Keys:**  Obtain API keys for:
        * **Shodan:** [https://www.shodan.io/](https://www.shodan.io/)
        * **Censys:** [https://censys.io/](https://censys.io/)
        * **Censys GPT:** [https://censys.io/](https://censys.io/) 
        * **Dehashed:** [https://dehashed.com/](https://dehashed.com/)

2. **Configuration:**
    * **Download:** Clone this repository or download the ZIP file.
    * **Create `config.json`:** Create a file named `config.json` in the root directory with the following structure (replace placeholders):
    ```json
    {
        "discord": {
            "prefix": ".." // Prefix for bot commands
            "version": "0.1" // Bot version
        },
        "identifiers": {
            "owner_id": 1234567890 // Your Discord user ID
            "verification_channel_id": 1234567890 // Channel ID for verification
            "verified_role_id": 1234567890 // Role ID for verified users
            "unverified_role_id": 1234567890 // Role ID for unverified users
            "welcome_channel_id": 1234567890 // Channel ID for welcome messages
            "farewell_channel_id": 1234567890 // Channel ID for farewell messages
            "logging_channel_id": 1234567890 // Channel ID for logging events
            "react_channel_id": 1234567890 // Channel ID for reaction roles
            "quiz_channel_id": 1234567890 // Channel ID for quiz announcements
            "security_channel_id": 1234567890 // Channel ID for security tips
            "fullz_channel_id": 1234567890 // Channel ID for fullz postings
            "stealer_channel_id": 1234567890 // Channel ID for stealer postings
            "crawler_channel_id": 1234567890 // Channel ID for device postings
            "admin_id": 1234567890 // Your Discord user ID (for admin commands)
            "muted_id": 1234567890 // Role ID for the muted role
        },
        "paths": {
            "root_directory": "/path/to/your/bot/directory/", // Path to the bot's root directory
            "database_path": "files/json/portlords.db", // Path to the database file
            "cogs_directory": "cogs", // Directory where cogs are stored
            "fullz_path": "files/json/fullz.json", // Path to the fullz data file
            "stealzies_path": "files/json/stealzies", // Path to the stealer log files
            "exploit_path": "files/exploits", // Path to the ExploitDB directory
            "exploit_file": "files/json/exploits.csv", // Path to the ExploitDB CSV file
            "tips_file_path": "files/json/tips.json", // Path to the security tips file
            "brokers_file_path": "files/json/brokers.json", // Path to the data broker information file
            "removal_file_path": "files/json/removal_links.json", // Path to the data removal links file
            "posted_files_path": "files/json/posted_files.json" // Path to the record of posted files
        },
        "logging": {
            "log_path": "logs", // Path to the logs directory
            "log_file_name": "portlords.log", // Name of the log file
            "log_level": "INFO" // Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        },
        "embeds": {
            "embed_footer": "Made with 🧡 by PortLords", // Footer text for embeds
            "embed_banner": "https://example.com/banner.png", // Banner image URL for embeds
            "embed_colors": { // Color options for embeds
                "primary": "#007bff", 
                "error": "#dc3545" 
            }
        },
        "features": { // Enable/disable bot features
            "quiz": true, 
            "security_tips": true, 
            "fullz": true,
            "stealer": true,
            "crawler": true, 
            "newsfeed": true
        },
        "moderation": { // Moderation settings
            "spam_threshold": 5, 
            "spam_message_count": 3,
            "wall_of_text_length": 2000,
            "max_emojis": 10, 
            "max_attachments": 3,
            "max_mentions": 5, 
            "first_mute_duration": 300,
            "second_mute_duration": 600
        },
        "settings": { // Bot settings
            "delete_commands": true, // Delete commands after execution
            "delete_command_delay": 5, // Delay in seconds for deleting commands
            "delete_responses": true, // Delete bot responses
            "delete_response_delay": 15, // Delay in seconds for deleting responses
            "delete_errors": true, // Delete error messages
            "delete_errors_delay": 5 // Delay in seconds for deleting error messages
        }
    }
    ```

3. **Running the Bot:**
    * **Terminal:** Open a terminal or command prompt.
    * **Navigate:** Navigate to the bot's directory (where `bot.py` is located).
    * **Run:** Execute `python bot.py` (or the equivalent command for your Python installation).

## Commands 🕹️

**Security**
* `..host <IP address>` - Host info from Shodan.
* `..recon <IP address>` - Perform an Nmap scan.
* `..cancelscan` - Cancel an ongoing Nmap scan.
* `..categories` - List ExploitDB categories.
* `..exploits <keyword>` - Search ExploitDB for exploits.
* `..download <exploit ID>` - Download an exploit by ID.
* `..censys <query>` - Search Censys using natural language.
* `..search <query type> <query>` - Search leaked databases.
* `..vulnerability <message>` - Vulnerability analysis by PortLordsAI.
* `..malware <message>` - Malware analysis by PortLordsAI.

**Tools**
* `..chat <message>` - Converse with PortLordsAI.
* `..code <message>` - Code help from PortLordsAI.
* `..sudo <command>` - Use an AI-powered Linux terminal.
* `..crack <hash> <hash_type>` - Crack a hash using Hashcat.
* `..fullz` - Sends random person data.
* `..stealer` - Sends random stealer data.
* `..privacy <service>` - Get data removal links for popular data brokers or specific services.
* `..username <username>` - Search for your digital footprint.
* `..password <password>` - Check the strength of a password.
* `..hibp <email>` - Check if an email has been involved in a data breach using 'Have I Been Pwned?'.
* `..obfuscate` - Obfuscate code (in the #obfuscation channel).
* `..proxy` - Retrieve proxies.

**Community**
* `..help <category>` - Show this message.
* `..ping` - Check the bot's latency.
* `..8ball <question>` - Ask the magic 8-ball a question.
* `..dice` - Roll a 6-sided dice.
* `..coinflip` - Flip a coin.
* `..joke` - Tell a programming joke.
* `..reminder <seconds> <message>` - Set a reminder.
* `..userinfo <user mention>` - Get information about a user.
* `..serverinfo` - Get information about the current server.
* `..quiz` - Start a new quiz.
* `..leaderboard` - Show the quiz leaderboard

**Moderation**
* `..kick <user mention> <reason>` - Kick a user.
* `..ban <user mention> <reason>` - Ban a user.
* `..unban <user#1234>` - Unban a user.
* `..mute <user mention> <reason>` - Mute a user.
* `..unmute <user mention> <reason>` - Unmute a user.
* `..clear <number of messages>` - Clear messages.
* `..warn <user mention> <reason>` - Warn a user.

**Owner**
* `..crawl <range_name>` - Start the PortLords crawler.
* `..reload <cog>` - Reload bot cogs.
* `..verification` - Manage the verification process.
* `..tiers` - Show the tier structure.
* `..impersonate <user mention> <message>` - Impersonate a user and send a message.
* `..postdevice` - Post a random device from the crawler's data.
* `..adduser <user ID> <username>` - Add a user to the database.
* `..getuser <user ID>` - Retrieve information about a user from the database.
* `..userpoints <user ID> <points>` - Update points for a user.
* `..usertier <user ID> <tier>` - Update the tier for a user.

**Note:** Some commands may have additional requirements or options. Use the `..help` command for specific instructions.

## Contributing 🤝

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to contribute.

## License 🔐

PortLords AI is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer ⚠️

This Discord bot is provided "as is" for educational and research purposes only. By using this bot, you acknowledge that you are solely responsible for your actions and that you will comply with all applicable laws and regulations.
