![](https://i.imgur.com/5mp2Siz.png)

# PortLords Community Discord Bot

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

- **Help Command**: Displays information about the bot and its commands.
- **Verification Command**: Starts the verification process for new users.
- **Reload Command**: Reloads the bot's code (development only).
- **Clear Command**: Deletes a specified number of messages.
- **Automatic Role Assignment**: Automatically assigns an initial role to new users.
- **Rotating Status**: Cycles through a list of status messages.

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
        "token": "",
        "botVersion": "1.0.0",
        "prefix": "..",
        "owner_id": "",
        "verified_role_name": "",
        "verified_channel_name": "",
        "verification_channel_id": "",
        "server_id": "",
        "gif_url": "",
        "global_footer": "",
        "cooldown_duration": "",
        "spotify_client_token": "",
        "spotify_client_id": "",
        "presence": {
            "activity": "watching",
            "name": "custom status here"
        },
        "cooldowns": {
            "default": 5
        },
        "logging": {
            "level": "DEBUG"
        }
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
  - **level**: The logging level (e.g., DEBUG, INFO, ERROR).
- **server_id**: The ID of the server where the bot is used.
- **verified_role_name**: The name of the role assigned to verified users.
- **verified_channel_name**: The name of the channel where verification takes place.
- **verification_channel_id**: The ID of the verification channel.
- **botVersion**: The version of the bot.
- **restricted_role_id**: The ID of the role required to use restricted commands.
- **initial_role_id**: The ID of the role assigned to new users.
- **cooldown_duration**: The duration you want for the website command.
- **global_footer**: The message you want at the end of the embeds.
- **gif_url**: The gif you want to display in the embeds.
- **spotify_client_token**: The token from Spotify to use their api.
- **spotify_client_id**: Your Spotify client id.

## Commands

- **help**: Displays information about the bot and its commands.
- **verification**: Starts the verification process.
- **reload**: Reloads the bot's code (development only).
- **clear**: Deletes a specified number of messages.
- **music**: Plays music from spotify.
- **website**: Gives information about a given website.
- **log_invite**: Logs invites to the server.
- **jvctocreate**: Creates a voice channel with VC commands for owner control.
- **lock**: Locks the current voice channel.
- **unlock**: Unlocks the current voice channel.
- **muteall**: Mutes all users in the current voice channel.
- **unmuteall**: Unmutes all users in the current voice channel.
- **kickall**: Kicks all users from the current voice channel.
- **mute**: Mutes a specific user in the current voice channel.
- **unmute**: Unmutes a specific user in the current voice channel.
- **kick**: Kicks a specific user from the current voice channel.

## Cogs

- **help.py**: Contains the help command.
- **reload.py**: Contains the reload command.
- **verification.py**: Contains the verification command.
- **clear.py**: Contains the clear command.
- **ping.py**: Contains the ping command.
- **website.py**: Contains the website command.
- **jvctocreate.py**: Contains VC related commands.
- **music.py**: Contrains the Muisic commands.
- **invitetrk.py**: Contrains the invite tracking command.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
