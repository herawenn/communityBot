# PortLords AI - Discord Bot

## I. Introduction

### A. Bot Overview

PortLords AI is an advanced Discord bot meticulously crafted to empower cybersecurity enthusiasts and professionals with cutting-edge tools and knowledge. It serves as a comprehensive hub for learning, research, and community engagement, enhancing your cybersecurity journey.

### B. Core Features

* **Interactive Tutorials:** Embark on hands-on learning adventures with step-by-step tutorials covering Shodan, Censys, OSINT, and ExploitDB.
* **Cybersecurity Quizzes:** Test your expertise through engaging daily quizzes encompassing a wide array of security concepts. Accumulate points, ascend through tiers, and unlock exclusive rewards.
* **Community Collaboration:** Connect with fellow cybersecurity aficionados, fostering a vibrant environment for knowledge exchange and collaborative learning.
* **Server Moderation:** Maintain order and harmony within your Discord server using essential moderation commands, including kick, ban, mute, unmute, clear, and warn.
* **User Management:** The bot meticulously tracks user information, points, and tier progression, creating a personalized and rewarding experience for every user.

## II. Getting Started

### A. Installation & Configuration

1. **Prerequisites:**
    * Python 3.8 or higher (recommended: 3.9+)
    * `discord.py` library: `pip install discord.py`
    * `sqlite3` library (built-in with Python)
    * A Shodan API key 
    * A Censys API ID and Secret
    * A Censys GPT API Key
    * A Dehashed API key (for OSINT searches)

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
| `..tutorial shodan`     | Guides you through the fundamentals of Shodan.       | `..tutorial shodan`                          |
| `..tutorial censys`    | Introduces you to Censys and how to use it for searches. | `..tutorial censys`                         |
| `..tutorial recon`     | Teaches you basic Nmap reconnaissance techniques.      | `..tutorial recon`                          |
| `..tutorial osint`     |  Explains OSINT principles and uses Dehashed API for searches.    | `..tutorial osint`                         | 
| `..tutorial exploitdb` |  Guides you on using the ExploitDB database for searching and downloading exploits.   | `..tutorial exploitdb`                     |

### B. Quiz Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `..quiz`      | Starts a daily cybersecurity quiz.               | `..quiz`                                | 

### C. Moderation Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `..kick`      | Kicks a user from the server.                 | `..kick <user> [reason]`                |
| `..ban`       | Bans a user from the server.                  | `..ban <user> [reason]`                 |
| `..unban`     | Unbans a user from the server.                | `..unban <user#discriminator>`          |
| `..mute`      | Mutes a user in the server.                   | `..mute <user> [reason]`                |
| `..unmute`    | Unmutes a user in the server.                 | `..unmute <user> [reason]`              |
| `..clear`     | Deletes a specified number of messages.       | `..clear <amount>`                      |
| `..warn`      | Issues a warning to a user.                   | `..warn <user> [reason]`                |

### D. OSINT Commands

| Command  | Description                                             | Usage                         |
| :------- | :------------------------------------------------------ | :---------------------------- |
| `..search` | Searches for leaked data using the Dehashed API.        | `..search <query_type> <query>` |
| `..footprint` |  Searches your digital footprint online.             | `..footprint <username>`        | 
| `..removeaccount` | Provides instructions for removing accounts.     | `..removeaccount <platform>`    |
| `..databreach` | Check if an email has been involved in data breaches. | `..databreach <email>`         |
| `..privacytips` | Provide privacy tips and best practices.       | `..privacytips`                   |

### E. Community Commands

| Command      | Description                                 | Usage                                 |
| :----------- | :------------------------------------------ | :------------------------------------ |
| `..ping`       | Checks the bot's latency.                   | `..ping`                                |
| `..joke`       | Tells a developer joke.                     | `..joke`                                |
| `..dice`       | Rolls a 6-sided dice.                       | `..dice`                                |
| `..8ball`      | Asks the Magic 8 Ball a question.           | `..8ball <question>`                    |
| `..coinflip`   | Flips a coin.                               | `..coinflip`                            |
| `..remind`     | Sets a reminder.                            | `..remind <time> <message>`             |
| `..userinfo`   | Gets information about a user.              | `..userinfo [member]`                   |
| `..serverinfo` | Gets information about the server.          | `..serverinfo`                          |

### F. Admin Commands

| Command        | Description                                               | Usage                 |
| :------------- | :-------------------------------------------------------- | :-------------------- |
| `..help`         | Displays an overview of the bot's commands.               | `..help`                |
| `..reload`       | Reloads all cogs (extensions) or a specific cog.          | `..reload [cog_name]`   |
| `..adduser`    |  Adds a user to the database.                               | `..adduser <user_id> <username>`                         |
| `..getuser`     | Retrieves information about a user.                        | `..getuser <user_id>`                                    | 
| `..userpoints` | Updates a user's points in the database.              | `..userpoints <user_id> <points>`                  |
| `..usertier` | Updates a user's tier in the database.                  | `..usertier <user_id> <tier>`                      |

### G. AI Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `..aiscan`     | Request a vulnerability assessment report for a given IP Address.       | `..aiscan <IP Address>`                          |
| `..chat`    | Engage in a conversation with PortLords AI. | `..chat <message>`                         |

### H. Shodan Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `..shodanhost`     | View detailed information about a specific host on Shodan.       | `..shodanhost <IP Address>`                          |
| `..shodansearch`    | Conduct a search on Shodan using a given query. | `..shodansearch <query>`                         |
| `..shodanscan`     | Initiate a vulnerability scan of a specified target on Shodan.      | `..shodanscan <IP Address>`                          |
| `..shodanscanstatus`     | Retrieve the current status of a previously initiated Shodan scan.       | `..shodanscanstatus <scan_id>`                          | 
| `..shodanscanresults` | Retrieve the results of a completed Shodan scan.   | `..shodanscanresults <scan_id>`                     |
| `..shodanhelp` | Displays help for the available Shodan commands.   | `..shodanhelp`                     |

### I. Censys Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `..censyshost`     | View detailed information about a specific host on Censys.       | `..censyshost <IP Address>`                          |
| `..censyssearch`    | Conduct a search on Censys using a custom query. | `..censyssearch <query>`                         |
| `..ask`    | Ask Censys GPT for a search query suggestion. | `..ask <question>`                         |

### J. Exploit-DB Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `..categories`     | Display the available exploit categories on Exploit-DB.       | `..categories`                          |
| `..exploits`    | Search for exploits based on a specific keyword. | `..exploits <keyword>`                         |
| `..download`     | Download an exploit using its ID.      | `..download <exploit_id>`                          |

### K. Fullz Commands

| Command     | Description                                   | Usage                                 |
| :---------- | :-------------------------------------------- | :------------------------------------ |
| `..fullz`      | Generates a random set of realistic person data.               | `..fullz`                                | 

### L. Other Commands

| Command             | Description                                             | Usage                                     |
| :------------------ | :------------------------------------------------------ | :---------------------------------------- |
| `..obfuscate`     | Obfuscates provided code.      | `..obfuscate <file>`                          |
| `..proxy`    | Retrieves proxies from the proxyscrape API. | `..proxy`                         |

## IV. Development & Support

### A. To-Do List

* **[High Priority]** Enhance PortLords AI's capabilities for static code analysis, identifying potential vulnerabilities in user-submitted code.
* **[Medium Priority]** Expand the scope of interactive tutorials to include advanced topics such as cryptography, network security, and penetration testing.
* **[Low Priority]** Develop a web-based dashboard for centralized bot management, log visualization, and remote control functionality.

**Note:** Priorities are subject to change based on user feedback and development progress.

### B. Support

For questions, support, or to report issues, please join the [PortLords Discord Server](https://discord.gg/portlords)

### C. Disclaimer

This Discord bot is provided "as is" for educational and research purposes only. By using this bot, you acknowledge that you are solely responsible for your actions and that you will comply with all applicable laws and regulations.
