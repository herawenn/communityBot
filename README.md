# PortLords Discord Bot Documentation

## I. Introduction

### A. Bot Overview

The PortLords Discord bot is a powerful cybersecurity learning and engagement tool designed to help both beginners and experienced security professionals. It offers a variety of resources and features to aid in security education, community interaction, and basic server moderation.

### B. Core Features

* **Interactive Tutorials:**  Learn practical cybersecurity skills through engaging, step-by-step tutorials for Shodan, Censys, OSINT, and ExploitDB.
* **Cybersecurity Quizzes:**  Test your knowledge with daily quizzes covering various security concepts. Earn points and level up to unlock exclusive benefits.
* **Community Engagement:**  Connect with other cybersecurity enthusiasts, share knowledge, and participate in fun community activities.
* **Server Moderation:**  Basic moderation commands to help manage your server, including kicking, muting, and clearing messages. 
* **User Management:**  The bot tracks user information, points, and tiers to foster a rewarding learning experience.

## II. Getting Started

### A. Installation & Configuration

1. **Prerequisites:**
    * Python 3.8 or higher (recommended: 3.9+)
    * `discord.py` library: `pip install discord.py`
    * `sqlite3` library (built-in with Python)
    * A Dehashed API key (for OSINT searches)
    * A Google Gemini API key (for AI interaction, optional)

2. **Configuration File (`config.json`):**
    * Create a `config.json` file in the root of your bot's directory with the following structure:
    * Replace placeholders with your actual values.

3. **Running the Bot:**
    * Open a terminal or command prompt.
    * Navigate to the bot's directory.
    * Execute `python bot.py` (or the equivalent command for your Python installation).

## III. Commands

### A. Tutorial Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `tutorial shodan`     | Guides you through the fundamentals of Shodan.       | `tutorial shodan`                          |
| `tutorial censys`    | Introduces you to Censys and how to use it for searches. | `tutorial censys`                         |
| `tutorial recon`     | Teaches you basic Nmap reconnaissance techniques.      | `tutorial recon`                          |
| `tutorial osint`     |  Explains OSINT principles and uses Dehashed API for searches.    | `tutorial osint`                         | 
| `tutorial exploitdb` |  Guides you on using the ExploitDB database for searching and downloading exploits.   | `tutorial exploitdb`                     |

### B. Quiz Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `quiz`      | Starts a daily cybersecurity quiz.               | `quiz`                                | 

### C. Moderation Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `kick`      | Kicks a user from the server.                 | `kick <user> [reason]`                |
| `ban`       | Bans a user from the server.                  | `ban <user> [reason]`                 |
| `unban`     | Unbans a user from the server.                | `unban <user#discriminator>`          |
| `mute`      | Mutes a user in the server.                   | `mute <user> [reason]`                |
| `unmute`    | Unmutes a user in the server.                 | `unmute <user> [reason]`              |
| `clear`     | Deletes a specified number of messages.       | `clear <amount>`                      |
| `warn`      | Issues a warning to a user.                   | `warn <user> [reason]`                |

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

### F. Admin Commands

| Command        | Description                                               | Usage                 |
| :------------- | :-------------------------------------------------------- | :-------------------- |
| `help`         | Displays an overview of the bot's commands.               | `help`                |
| `reload`       | Reloads all cogs (extensions) or a specific cog.          | `reload [cog_name]`   |
| `adduser`    |  Adds a user to the database.                               | `adduser <user_id> <username>`                         |
| `getuser`     | Retrieves information about a user.                        | `getuser <user_id>`                                    | 
| `updateuserpoints` | Updates a user's points in the database.              | `updateuserpoints <user_id> <points>`                  |
| `updateusertier` | Updates a user's tier in the database.                  | `updateusertier <user_id> <tier>`                      |
| `updateuserverified` | Updates a user's verified status.                   | `updateuserverified <user_id> true/false`              | 
| `updateusermuteduntil` | Updates a user's muted timestamp.                 | `updateusermuteduntil <user_id> <YYYY-MM-DD HH:MM:SS>` |
| `updateuserbanreason` | Updates a user's ban reason.                       | `updateuserbanreason <user_id> <reason>`               |
| `updateuserwarncount` | Updates a user's warn count.                       | `updateuserwarncount <user_id> <warn_count>`           | 

## IV. Advanced Features

### A. AI Integration (PortLordsAI - Optional)

PortLordsAI, powered by Google Gemini (optional), adds conversational AI capabilities to the bot. Interact with it using the `!chat` command. 

**Key Features:**

* **Cybersecurity Knowledge:** Ask questions about cybersecurity concepts or request definitions.

**Important Considerations:**

* **API Key:** Ensure you have a valid Google Gemini API key configured in your `config.json` file.
* **Limitations:** The AI model has limitations, and its responses might not always be perfect or suitable for production use. Always double-check its outputs.
* **Biases:** AI models are trained on vast datasets and can reflect biases present in those datasets. Be aware that responses are not always objective.

### B. Dehashed Integration

The bot enables you to search for leaked data using the Dehashed API through the `!search` command. Provide the query type (e.g., 'email', 'username', 'password') and your query to retrieve related information. 

## V. Development & Support

### A. To-Do List

* **[High Priority]**  Investigate using the AI for basic malware analysis (e.g., identifying potentially malicious strings in code).
* **[Medium Priority]** Expand the AI to include more features like generating security scripts. 
* **[Low Priority]**  Create a web-based dashboard for managing the bot, viewing logs, and potentially controlling some functionalities remotely.

**Note:** Priorities are subject to change based on user feedback and development progress.

### B. Support

For questions, support, or to report issues, please join the [PortLords Discord Server](https://discord.gg/portlords)

### C. Disclaimer

This Discord bot is provided "as is" for educational and research purposes only. By using this bot, you acknowledge that you are solely responsible for your actions and that you will comply with all applicable laws and regulations.
