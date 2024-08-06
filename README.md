![](https://i.imgur.com/5mp2Siz.png)

# PortLords Community Discord Bot

![Discord Bot](https://i.imgur.com/KUk1lpR.png)

A multi-purpose Discord bot with various commands and functionalities.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
- [Cogs](#cogs)
- [Contributing](#contributing)
- [License](#license)

## Features

- Help command to list all available commands.
- Verification command to start the verification process.
- Reload command to reload the bot's code (development only).
- Clear command to delete a specified number of messages.

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/discord-bot.git
    cd discord-bot
    ```

2. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Create a `config.json` file:**

    ```json
    {
        "prefix": "!",
        "token": "YOUR_DISCORD_BOT_TOKEN",
        "owner_id": "YOUR_DISCORD_USER_ID",
        "logging": {
            "level": "DEBUG"
        },
        "server_id": "YOUR_SERVER_ID",
        "verified_role_name": "Verified",
        "verified_channel_name": "verification",
        "verification_channel_id": "YOUR_VERIFICATION_CHANNEL_ID",
        "botVersion": "1.0.0",
        "restricted_role_id": "YOUR_RESTRICTED_ROLE_ID"
    }
    ```

4. **Run the bot:**

    ```sh
    python bot.py
    ```

## Configuration

- **prefix**: The command prefix for the bot.
- **token**: The bot token from the Discord Developer Portal.
- **owner_id**: The Discord ID of the bot owner.
- **logging**: Configuration for logging.
- **server_id**: The ID of the server where the bot is used.
- **verified_role_name**: The name of the role assigned to verified users.
- **verified_channel_name**: The name of the channel where verification takes place.
- **verification_channel_id**: The ID of the verification channel.
- **botVersion**: The version of the bot.
- **restricted_role_id**: The ID of the role required to use restricted commands.

## Commands

- **help**: Displays information about the bot and its commands.
- **verification**: Starts the verification process.
- **reload**: Reloads the bot's code (development only).
- **clear**: Deletes a specified number of messages.

## Cogs

- **help.py**: Contains the help command.
- **reload.py**: Contains the reload command.
- **verification.py**: Contains the verification command.
- **clear.py**: Contains the clear command.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

