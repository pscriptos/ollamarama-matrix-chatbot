"""
# Beschreibung:     ollamarama-matrix: An AI chatbot for the Matrix chat protocol with infinite personalities.
# Autor:            Dustin Whyte (https://github.com/h1ddenpr0cess20/ollamarama-matrix)
# Erstellt am:      December 2023
# Modifiziert von:  Patrick Asmus
# Web:              https://www.techniverse.net
# Git-Reposit.:     https://git.techniverse.net/scriptos/ollamarama-matrix.git
# Version:          2.0
# Datum:            27.11.2024
# Modifikation:     Logging eingebaut
#####################################################
"""

from nio import AsyncClient, MatrixRoom, RoomMessageText
import json
import datetime
import asyncio
import requests
import markdown


class ollamarama:
    def __init__(self):
        # Load config file
        self.config_file = "config.json"
        with open(self.config_file, "r") as f:
            config = json.load(f)

        self.server, self.username, self.password, self.channels, self.admins = config["matrix"].values()

        self.client = AsyncClient(self.server, self.username)

        # Time program started and joined channels
        self.join_time = datetime.datetime.now()

        # Store chat history
        self.messages = {}

        # API URL
        self.api_url = config["ollama"]["api_base"] + "/api/chat"
        print(f"API URL: {self.api_url}")

        # Model configuration
        self.models = config["ollama"]["models"]
        self.default_model = self.models[config["ollama"]["default_model"]]
        self.model = self.default_model
        print(f"Default model: {self.model}")

        # Options
        self.temperature, self.top_p, self.repeat_penalty = config["ollama"]["options"].values()
        self.defaults = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty
        }

        self.default_personality = config["ollama"]["personality"]
        self.personality = self.default_personality
        self.prompt = config["ollama"]["prompt"]

    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            print(f"Error fetching display name: {e}")
            return user

    async def send_message(self, channel, message):
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message,
                "format": "org.matrix.custom.html",
                "formatted_body": markdown.markdown(message, extensions=["fenced_code", "nl2br"]),
            },
        )

    async def add_history(self, role, channel, sender, message):
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = [
                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}
            ]
        self.messages[channel][sender].append({"role": role, "content": message})

        # Trim history
        if len(self.messages[channel][sender]) > 24:
            if self.messages[channel][sender][0]["role"] == "system":
                del self.messages[channel][sender][1:3]
            else:
                del self.messages[channel][sender][0:2]

    async def respond(self, channel, sender, message, sender2=None):
        try:
            data = {
                "model": self.model,
                "messages": message,
                "stream": False,
                "options": {
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "repeat_penalty": self.repeat_penalty,
                },
            }

            # Log the data being sent
            print(f"Sending data to API: {json.dumps(data, indent=2)}")

            response = requests.post(self.api_url, json=data, timeout=300)
            response.raise_for_status()
            data = response.json()

            # Log the API response
            print(f"API response: {json.dumps(data, indent=2)}")

        except Exception as e:
            error_message = f"Error communicating with Ollama API: {e}"
            await self.send_message(channel, error_message)
            print(error_message)
        else:
            response_text = data["message"]["content"]
            await self.add_history("assistant", channel, sender, response_text)

            display_name = await self.display_name(sender2 if sender2 else sender)
            response_text = f"**{display_name}**:\n{response_text.strip()}"

            try:
                await self.send_message(channel, response_text)
            except Exception as e:
                print(f"Error sending message: {e}")

    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        try:
            self.messages[channel][sender].clear()
        except KeyError:
            pass

        if persona:
            prompt = self.prompt[0] + persona + self.prompt[1]
        elif custom:
            prompt = custom

        await self.add_history("system", channel, sender, prompt)

        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            await self.respond(channel, sender, self.messages[channel][sender])

    async def ai(self, channel, message, sender, x=False):
        try:
            if x and len(message) > 2:
                name = message[1]
                message = message[2:]
                if channel in self.messages:
                    for user in self.messages[channel]:
                        try:
                            username = await self.display_name(user)
                            if name == username:
                                name_id = user
                        except Exception as e:
                            print(f"Error in .x command: {e}")
                            name_id = name

                    await self.add_history("user", channel, name_id, " ".join(message))
                    await self.respond(channel, name_id, self.messages[channel][name_id], sender)
            else:
                await self.add_history("user", channel, sender, " ".join(message[1:]))
                await self.respond(channel, sender, self.messages[channel][sender])
        except Exception as e:
            print(f"Error in .ai command: {e}")

    async def handle_message(self, message, sender, sender_display, channel):
        user_commands = {
            ".ai": lambda: self.ai(channel, message, sender),
            ".reset": lambda: self.set_prompt(channel, sender, persona=self.personality, respond=False),
        }

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            await action()

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        if isinstance(event, RoomMessageText):
            message_time = datetime.datetime.fromtimestamp(event.server_timestamp / 1000)
            message = event.body.split(" ")
            sender = event.sender
            sender_display = await self.display_name(sender)
            channel = room.room_id

            if message_time > self.join_time and sender != self.username:
                try:
                    await self.handle_message(message, sender, sender_display, channel)
                except Exception as e:
                    print(f"Error handling message: {e}")

    async def main(self):
        print(await self.client.login(self.password))
        self.bot_id = await self.display_name(self.username)

        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
            except Exception as e:
                print(f"Couldn't join {channel}: {e}")

        self.client.add_event_callback(self.message_callback, RoomMessageText)
        await self.client.sync_forever(timeout=30000, full_state=True)


if __name__ == "__main__":
    ollamarama = ollamarama()
    asyncio.run(ollamarama.main())
