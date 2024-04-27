"""
ollamarama-matrix: An AI chatbot for the Matrix chat protocol with infinite personalities.

Author: Dustin Whyte
Date: December 2023
"""

from nio import AsyncClient, MatrixRoom, RoomMessageText
from litellm import completion
import json
import datetime
import asyncio

class ollamarama:
    def __init__(self, server, username, password, channels, personality, admins):
        self.server = server
        self.username = username
        self.password = password
        self.channels = channels
        self.default_personality = personality
        self.personality = personality
        
        self.client = AsyncClient(server, username)
                
        # time program started and joined channels
        self.join_time = datetime.datetime.now()
        
        # store chat history
        self.messages = {}

        #prompt parts
        self.prompt = ("you are ", ". roleplay and speak in the first person and never break character.")

        #open config.json
        with open("config.json", "r") as f:
            self.models = json.load(f)[0]
            f.close()
        #set model
        self.default_model = self.models['llama3']
        self.model = self.default_model

        #no idea if optimal, change if necessary
        self.temperature = .9
        self.top_p = .7
        self.repeat_penalty = 1.5

        #authorized users for changing models
        self.admins = admins

        #load help menu
        with open("help.txt", "r") as f:
            self.help, self.help_admin = f.read().split("~~~")
            f.close()
 
        
    # get the display name for a user
    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            print(e)

    # simplifies sending messages to the channel            
    async def send_message(self, channel, message):
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )

    # add messages to the history dictionary
    async def add_history(self, role, channel, sender, message):
        #check if channel is in the history yet
        if channel in self.messages:
            #check if user is in channel history
            if sender in self.messages[channel]: 
                self.messages[channel][sender].append({"role": role, "content": message})
                
            else:
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]
        else:
            #set up channel in history
            self.messages[channel]= {}
            self.messages[channel][sender] = {}
            if role == "system":
                self.messages[channel][sender] = [{"role": role, "content": message}]
            else: 
                #add personality to the new user entry
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]

    #generate Ollama model response
    async def respond(self, channel, sender, message, sender2=None):
        try:
            #Generate response
            response = completion(
                api_base="http://localhost:11434",
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                messages=message,
                timeout=60
                ) 
        except Exception as e:
            await self.send_message(channel, "Something went wrong")
            print(e)
        else:
            #Extract response text
            response_text = response.choices[0].message.content
            
            #check for unwanted quotation marks around response and remove them
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text.strip('"')

            #add to history
            await self.add_history("assistant", channel, sender, response_text)
            # .x function was used
            if sender2:
                display_name = await self.display_name(sender2)
            # .ai was used
            else:
                display_name = await self.display_name(sender)
            response_text = display_name + ":\n" + response_text.strip()
            #Send response to channel
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)
            #Shrink history list for token size management 
            if len(self.messages[channel][sender]) > 24:
                del self.messages[channel][sender][1:3]  #delete the first set of question and answers 

    # change the personality of the bot
    async def persona(self, channel, sender, persona):
        #clear existing history
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        personality = self.prompt[0] + persona + self.prompt[1]
        #set system prompt
        await self.add_history("system", channel, sender, personality)
        
    # use a custom prompt
    async def custom(self, channel, sender, prompt):
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        await self.add_history("system", channel, sender, prompt)  

    # tracks the messages in channels
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        # Main bot functionality
        if isinstance(event, RoomMessageText):
            # convert timestamp
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            # assign parts of event to variables
            message = event.body
            sender = event.sender
            sender_display = await self.display_name(sender)
            room_id = room.room_id
            user = await self.display_name(event.sender)

            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:

                #admin commands
                if message == ".admins":
                    await self.send_message(room_id, f"Bot admins: {', '.join(self.admins)}")
                if sender_display in self.admins:
                    #model switching 
                    if message.startswith(".model"):
                        if message == ".models":
                            current_model = f"Current model: {self.model.removeprefix('ollama/')}\nAvailable models: {', '.join(sorted(list(self.models)))}"
                            await self.send_message(room_id, current_model)
                            
                        if message.startswith(".model "):
                            m = message.split(" ", 1)[1]
                            if m != None:
                                if m in self.models:
                                    self.model = self.models[m]
                                elif m == 'reset':
                                    self.model = self.default_model
                                await self.send_message(room_id, f"Model set to {self.model.removeprefix('ollama/')}")
                    
                    #bot owner commands
                    if sender_display == self.admins[0]:
                        #add admins
                        if message.startswith(".auth "):
                            nick = message.split(" ", 1)[1].strip()
                            if nick != None:
                                self.admins.append(nick)
                                await self.send_message(room_id, f"{nick} added to admins")
                        
                        #remove admins
                        if message.startswith(".deauth "):
                            nick = message.split(" ", 1)[1].strip()
                            if nick != None:
                                self.admins.remove(nick)
                                await self.send_message(room_id, f"{nick} removed from admins")

                        #set new global personality
                        if message.startswith(".gpersona "):
                            m = message.split(" ", 1)[1]
                            if m != None:
                                if m == 'reset':
                                    self.personality = self.default_personality
                                else:
                                    self.personality = m.strip()
                                await self.send_message(room_id, f"Global personality set to {self.personality}")
                        
                        #remove personality globally
                        if message == ".gstock":
                            pass #i'll figure this out later

                        #reset history for all users                
                        if message == ".clear":
                            self.messages.clear()
                            self.model = self.default_model
                            self.temperature = .9
                            self.top_p = .7
                            self.repeat_penalty = 1.5
                            await self.send_message(room_id, "Bot has been reset for everyone")
                        
                        #temperature setting
                        if message.startswith(".temperature "):
                            if message == ".temperature reset":
                                self.temperature = .9
                                await self.send_message(room_id, f"Temperature set to {self.temperature}")
                            else:
                                try:
                                    temp = float(message.split(" ", 1)[1])
                                    if 0 <= temp <=1:
                                        self.temperature = temp
                                        await self.send_message(room_id, f"Temperature set to {self.temperature}")
                                    else:
                                        await self.send_message(room_id, f"Invalid input, temperature is still {self.temperature}")
                                except:
                                    await self.send_message(room_id, f"Invalid input, temperature is still {self.temperature}")

                        #top_p setting
                        if message.startswith(".top_p "):
                            if message == ".top_p reset":
                                self.top_p = .7
                                await self.send_message(room_id, f"Top_p set to {self.top_p}")
                            else:
                                try:
                                    top_p = float(message.split(" ", 1)[1])
                                    if 0 <= top_p <=1:
                                        self.top_p = top_p
                                        await self.send_message(room_id, f"Top_p set to {self.top_p}")
                                    else:
                                        await self.send_message(room_id, f"Invalid input, top_p is still {self.top_p}")
                                except:
                                    await self.send_message(room_id, f"Invalid input, top_p is still {self.top_p}")                                                      

                        #repeat_penalty setting
                        if message.startswith(".repeat_penalty "):
                            if message == ".repeat_penalty reset":
                                self.repeat_penalty = 1.5
                                await self.send_message(room_id, f"Repeat_penalty set to {self.repeat_penalty}")
                            else:
                                try:
                                    repeat_penalty = float(message.split(" ", 1)[1])
                                    if 0 <= repeat_penalty <=2:
                                        self.repeat_penalty = repeat_penalty
                                        await self.send_message(room_id, f"Repeat_penalty set to {self.repeat_penalty}")
                                    else:
                                        await self.send_message(room_id, f"Invalid input, repeat_penalty is still {self.repeat_penalty}")
                                except:
                                    await self.send_message(room_id, f"Invalid input, repeat_penalty is still {self.repeat_penalty}")

                # main AI response functionality
                if message.startswith(".ai ") or message.startswith(self.bot_id):
                    if message != ".ai reset":
                        m = message.split(" ", 1)
                        try:
                            m = m[1]  + " [your response must be one paragraph or less]"
                            await self.add_history("user", room_id, sender, m)
                            await self.respond(room_id, sender, self.messages[room_id][sender])
                        except:
                            pass
                # collaborative functionality
                if message.startswith(".x "):
                    m = message.split(" ", 2)
                    m.pop(0)
                    if len(m) > 1:
                        disp_name = m[0]
                        name_id = ""
                        m = m[1] + " [your response must be one paragraph or less]"
                        if room_id in self.messages:
                            for user in self.messages[room_id]:
                                try:
                                    username = await self.display_name(user)
                                    if disp_name == username:
                                        name_id = user
                                except:
                                    name_id = disp_name
                        
                            await self.add_history("user", room_id, name_id, m)
                            await self.respond(room_id, name_id, self.messages[room_id][name_id], sender)

                #change personality    
                if message.startswith(".persona "):
                    m = message.split(" ", 1)
                    m = m[1] + " [your response must be one paragraph or less]"
                
                    await self.persona(room_id, sender, m)
                    await self.respond(room_id, sender, self.messages[room_id][sender])

                #custom prompt use   
                if message.startswith(".custom "):
                    m = message.split(" ", 1)
                    m = m[1]
                    await self.custom(room_id, sender, m)
                    await self.respond(room_id, sender, self.messages[room_id][sender])

                # reset bot to default personality
                if message.startswith(".reset") or message == ".ai reset": #some users keep forgetting the correct command
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                            await self.persona(room_id, sender, self.personality)
                            
                    try:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender_display}")
                    except:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender}")

                # Stock settings, no personality        
                if message.startswith(".stock"):
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                    else:
                        self.messages[room_id] = {}
                        self.messages[room_id][sender] = []
                    try:
                        await self.send_message(room_id, f"Stock settings applied for {sender_display}")
                    except:
                        await self.send_message(room_id, f"Stock settings applied for {sender}")
                
                # help menu
                if message.startswith(".help"):
                    await self.send_message(room_id, self.help)
                    if sender_display in self.admins:
                        await self.send_message(room_id, self.help_admin)

    # main loop
    async def main(self):
        # Login, print "Logged in as @alice:example.org device id: RANDOMDID"
        print(await self.client.login(self.password))

        # get account display name
        self.bot_id = await self.display_name(self.username)
        
        # join channels
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")
        
        # start listening for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        await self.client.sync_forever(timeout=30000) 

if __name__ == "__main__":
    #load config file
    with open("config.json", "r") as f:
        config = json.load(f)
        f.close()
    
    server, username, password, channels, personality, admins = config[1].values()

    # create bot instance
    bot = ollamarama(server, username, password, channels, personality, admins)
    
    # run main function loop
    asyncio.get_event_loop().run_until_complete(bot.main())

