from dataclasses import dataclass
message = "@badge-info=;badges=broadcaster/1;client-nonce=28e05b1c83f1e916ca1710c44b014515;color=#0000FF;display-name=foofoo;emotes=62835:0-10;first-msg=0;flags=;id=f80a19d6-e35a-4273-82d0-cd87f614e767;mod=0;room-id=713936733;subscriber=0;tmi-sent-ts=1642696567751;turbo=0;user-id=713936733;user-type= :foofoo!foofoo@foofoo.tmi.twitch.tv PRIVMSG #bar :bleedPurple"

@dataclass
class PrivateMessage:
    tags: dict[str, str]
    channel: str
    user: str
    message: str

    def __init__(self, message: str):
        message_without_at = message[1:] if message.startswith("@") else message

        # Separate on first instance of a space. First part is tags_str, and second part is command_str
        tags_str, command_str = message_without_at.split(" ", 1)

        # tags_list = tags_str split by semi-colon
        tags_list: list[str] = tags_str.split(";")

        tags_dict: dict[str, str] = dict()
        # tags_dict = tags_list where each tag is formatted like "key=value"
        for tag in tags_list:
            if "=" in tag:
                key, value = tag.split("=", 1)
                tags_dict[key] = value

        # Retrieve channel, name, and message from command. Example above. Format is the following: :<user>!<user>@<user>.tmi.twitch.tv PRIVMSG #<channel> :<message>
        user_part, channel_message_part = command_str.split(" PRIVMSG ", 1)
        user = user_part[1:].split("!")[0]  # Remove leading ":" and extract username before "!"

        channel_part, message_part = channel_message_part.split(" :", 1)
        channel = channel_part[1:]  # Remove "#" prefix from channel

        self.tags = tags_dict
        self.channel = channel
        self.user = user
        self.message = message


t: dict[str, str] = dict()

# Cut off @
message_without_at = message[1:] if message.startswith("@") else message

# Separate on first instance of a space. First part is tags_str, and second part is command_str
tags_str, command_str = message_without_at.split(" ", 1)

# tags_list = tags_str split by semi-colon
tags_list = tags_str.split(";")

# t = tags_list where each tag is formatted like "key=value"
for tag in tags_list:
    if "=" in tag:
        key, value = tag.split("=", 1)
        t[key] = value

print("Tags dictionary:", t)

# :foofoo!foofoo@foofoo.tmi.twitch.tv PRIVMSG #bar :bleedPurple

# Retrieve channel, name, and message from command. Example above. Format is the following: :<user>!<user>@<user>.tmi.twitch.tv PRIVMSG #<channel> :<message>
user_part, channel_message_part = command_str.split(" PRIVMSG ", 1)
user = user_part[1:].split("!")[0]  # Remove leading ":" and extract username before "!"

channel_part, message_part = channel_message_part.split(" :", 1)
channel = channel_part[1:]  # Remove "#" prefix from channel

print("User:", user)
print("Channel:", channel)
print("Message:", message_part)
