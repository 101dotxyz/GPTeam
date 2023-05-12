# Setting up Discord integration
## Concepts
The way GPTeam maps to Discord, is by first associating each World with
a Discord server, known in their documentation as a *Guild*. Within each
World, if you're using the Discord integration, then each location must map
to a channel. Each agent maps to a different Discord bot (which must be a
separate Application within Discord). There is also an extra bot we call
the announcer bot that is used to announce agent movement between rooms.

## Configuring Locations
1. Set up your Discord server
2. Enable Discord developer mode  
    ![Screenshot of how to enable developer mode](https://101-public.s3.us-east-1.amazonaws.com/Screenshot%202023-05-11%20at%202.24.37%20PM.png)
3. Get channel ids for each channel (you should have one per location)  
    ![screenshot of how to get channel id](https://101-public.s3.us-east-1.amazonaws.com/Screenshot%202023-05-11%20at%202.25.11%20PM.png)
4. Add the channel ids to your `.env` file in the format `<LOCATION_NAME>_CHANNEL_ID` (i.e. as show below)
   ```
    WATER_COOLER_CHANNEL_ID=12345689102
    LOBBY_CHANNEL_ID=12345689103
    CONFERENCE_ROOM_CHANNEL_ID=12345689104
    ...
   ```

## Configuring Bots
This is the harder part and this will just give a basic guide. If you plan to
run these Discord bots in production, you're doing so at your own risk and
should optimize the permissions used below as needed.

### Creating Bot Applications
First you need to create a bot application for each of your agents and one
extra one for the announcer bot. For each, follow the steps below.

1. Go to the [Discord developer portal](https://discord.com/developers/applications) and create a new application
   ![screenshot of creating a new discord application](https://101-public.s3.amazonaws.com/Screenshot+2023-05-11+at+3.27.34+PM.png)
2. Go to the Bot tab in the application settings and click reset token. Write down this token for later
   ![screenshot of resetting bot token](https://101-public.s3.amazonaws.com/Screenshot+2023-05-11+at+3.30.32+PM.png)
3. **[Only for Announcer Bot]** Scroll down and check to make sure the "Message Content Intent" is enabled. Don't forget to click "Save Changes"!
   ![screenshot of configuring message content intent](https://101-public.s3.amazonaws.com/Screenshot+2023-05-11+at+3.44.25+PM.png)
4. Go to the Oauth - URL Generator subtab. For scopes select "Bot" and for bot permissions I selected "Administrator" (this isn't strictly necessary but makes things simpler). Copy the generated URL.
   ![screenshot of oauth url generation](https://101-public.s3.amazonaws.com/Screenshot+2023-05-11+at+3.35.32+PM.png)
5. Paste the URL into a new tab and add the bot to the server you're using. Make sure that the "Administrator" permission remains checked
   ![Screenshot of discord bot auth](https://101-public.s3.amazonaws.com/Screenshot+2023-05-11+at+3.35.57+PM.png)
6. Add the bot token to your `.env` file in the format `<BOT_FIRST_NAME>_DISCORD_TOKEN` (i.e. as show below)
    ```
    MARTY_DISCORD_TOKEN=rwfilbelihrfgbliehrwbfilaewhrbfilrbr
    ROBERTO_DISCORD_TOKEN=ewrkhlgbelirgbaleirhbvilaewrfliawrgfiyrwgf_ihdgfiyrg
    JESSICA_DISCORD_TOKEN=o9qfgreiagvbkdfzflafohiufvglaeiuhfu_fbhbvhie
    ...
   ```
