# DFTwitchBot
An interface between Twitch chat and DeFRaG.

## Usage
* Step 1: Retrieve a tmi token and client id from the twitch developer portal, paste these into their respective fields
in env.py
* Step 2: Copy the provided .cfg files to your `/defrag/` folder
* Step 3: Change the field "DF_DIR" in env.py to the full path to your `/defrag/` folder
* Step 4: Change the field "DF_EXE_P" in env.py to the name of your defrag engine executable
* step 5: Change the field "CHANNEL" in env.py to the name of twitch channel you wish to connect the bot to
* Step 6: Run `python bot.py`
* Step 7: Launch iDFe.exe, or let the bot run it for you. execute the twitch configs 
