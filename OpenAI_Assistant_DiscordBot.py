from email.policy import default
from importlib.resources import read_text
import discord
from discord.ext import commands
import asyncio
import re
import openai
import aiohttp
from openai import OpenAI
import os
from io import BytesIO
from dotenv import load_dotenv

from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
import fitz  # PyMuPDF

# Initialize bot and OpenAI client
load_dotenv()

#Setup your assistant here
#https://platform.openai.com/assistants

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_ASSISTANT = os.getenv("DEFAULT_ASSISTANT")
DISCORD_KEY = os.getenv("DISCORD_KEY")

MAX_TOKENS = int(os.getenv("MAX_TOKENS"))

PROCESS_IMAGE = os.getenv("PROCESS_IMAGE") == 'True'
PROCESS_TEXT_ATTACHMENTS = os.getenv("PROCESS_TEXT_ATTACHMENTS") == 'True'
PROCESS_URL = os.getenv("PROCESS_URL") == 'True'
PROCESS_YOUTUBE_URLS = os.getenv("PROCESS_YOUTUBE_URLS") == 'True'

user_threads = {}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

bot = commands.Bot(command_prefix='!', description="Assistant bot", intents=intents)

@bot.event
async def on_ready():
    print('----------------------------------------------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f"Image processing {PROCESS_IMAGE}" )
    print(f"Text Attachment processing {PROCESS_TEXT_ATTACHMENTS}" )
    print(f"URL scraping {PROCESS_URL}" )
    print(f"Youtube Processing {PROCESS_YOUTUBE_URLS}" )
    print(f"Loaded with Assistant: {get_assistant_name()}")
    print("Assistant bot is ready!")
    print('----------------------------------------------')


def manage_thread(user_id, clear=False):
    if clear or user_id not in user_threads:
        thread = client.beta.threads.create()
        user_threads[user_id] = thread.id
        return thread.id
    return user_threads[user_id]

def get_assistant_name():
    assistants = client.beta.assistants.list()
    assistant_name = "Assistant Not Found"
    for assistant in assistants.data:
        if assistant.id == DEFAULT_ASSISTANT:
            return assistant.name
            break
    return assistant_name

#To do later add that this takes an array of images and files for upload should be simple just loop

async def get_gpt_assistant(user_input,thread_id,image_attachment = None , file_attachment = None):
    output_easy = ""
    try:
        #Image Attachment Do this!
        if image_attachment != None:
                print("Image Attachment Uploaded")    
                client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": user_input
                        },
                        #try this later because discords are urls     
                        {
                          "type": "image_url",
                          "image_url": {
                            "url": image_attachment.url,
                            "detail": "high"
                        }
                    }
                    ]
                )
                #needs testing!
        elif file_attachment != None:
                print("File Attachment Uploaded")        
                file_bytes = await file_attachment.read()
                file = BytesIO(file_bytes)
                file.name = file_attachment.filename  # This is necessary for the OpenAI API

                upload_response = client.files.create(
                    purpose='assistants',
                    file=file
                )
                print(f"file.name Uploaded ID is now {upload_response}")
                # Attach file to thread
                client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": user_input
                        },
                        {
                            "type": "file_search",
                            "file_search": {
                                "file_id": upload_response.id,
                                "tools": [{"type": "file_search"}]
                            }
                        }
                    ]
                )
        else:
        # User just sent text that's it!
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
            )

        # Start the assistant and stream the response
        with client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=DEFAULT_ASSISTANT,
            #instructions=system_prompt
            max_completion_tokens=MAX_TOKENS
        ) as stream:
            for text in stream.text_deltas:
                output_easy += text

        return output_easy
    except Exception as e:
        # If an error occurs, return the error message
        return f"✖️ An error occurred: {str(e)}"

@bot.event
async def on_message(message):
    if message.author == bot.user or message.mention_everyone:
        return

    if message.guild is None:
        asyncio.create_task(process_message(message))
        

#---------------------- Message Async        
async def process_message(message):
    async with message.channel.typing():
        message_str = message.content
        message_str = clean_discord_message(message_str)
        if message_str == "CLEAR" or message_str == "RESET" or message_str == "CLEAN":
            manage_thread(message.author.id, True)
            await message.channel.send("🧼 You now have a clean thread 🧼")
            return
        if message_str == "CREATE":
            print("Got Create Add image gen later")
        thread_id = manage_thread(message.author.id)
        if message.attachments:

            await process_attachments(message, message_str, thread_id)
        else:
            await process_text_message(message, message_str, thread_id)

#---------------------- Process Attachements | Only handles one attachment at a time   
async def process_attachments(message, message_str, thread_id):
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            if(PROCESS_IMAGE == False):
                result = await get_gpt_assistant(message_str, thread_id)
                await send_messages(message, split_string(result, 1700)) 
                return
            print(f"Image attaching to thread: {attachment.filename}")
            await message.add_reaction('🎨')
            result = await get_gpt_assistant(message_str, thread_id, attachment)
            await send_messages(message, split_string(result, 1700))
            return
        else:
            if(PROCESS_TEXT_ATTACHMENTS == False):
                result = await get_gpt_assistant(message_str, thread_id)
                await send_messages(message, split_string(result, 1700)) 
                return
            await message.add_reaction('📄')
            processed_text = await process_text_attachments(attachment)
            #print(f"TEXT PROCESSED DEBUG {processed_text}")
            result = await get_gpt_assistant(message_str + " " + processed_text, thread_id)
            await send_messages(message, split_string(result, 1700))
            return

#------------------------ Process URL        
async def process_urls(message_str, message):
    if PROCESS_URL == False:
        return message_str
    urls = re.findall(r'(https?://\S+)', message_str)
    processed_prompt = message_str
    for url in urls:
        transcript = await get_transcript_from_url(url, message)
        processed_prompt = processed_prompt.replace(url, transcript)
    return processed_prompt

#-------------------------- Process Text Message
async def process_text_message(message, message_str, thread_id):
    print(f"New Text Message from :{message.author.display_name}|{thread_id}: {message_str}")
    processed_prompt = await process_urls(message_str, message)
    result = await get_gpt_assistant(processed_prompt, thread_id)
    await send_messages(message, split_string(result, 1700))

def clean_discord_message(input_string):
    bracket_pattern = re.compile(r'<[^>]+>')
    cleaned_content = bracket_pattern.sub('', input_string)
    return cleaned_content

def split_string(string, max_length=1700):
    messages = []
    start = 0

    while start < len(string):
        # Find the endpoint within max_length or to the end of string
        end = min(start + max_length, len(string))

        # If end isn't at the end of the string, backtrack to the last space
        if end < len(string) and string[end] != ' ':
            end = string.rfind(' ', start, end)
            if end == -1:
                end = min(start + max_length, len(string))  # Fallback in case there's no space

        # Append the substring to messages and update the start position
        messages.append(string[start:end].strip())
        start = end

    return messages

async def send_messages(message_system, output):
    for index, string in enumerate(output):
        await message_system.channel.send(string)
    
#-------------------------- TExt PROCESSING ----------------------------------------
async def process_text_attachments(attachment):
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status != 200:
                return "❌ Unable to download the attachment"
            if attachment.filename.lower().endswith('.pdf'):
                print("Processing PDF")
                try:
                    pdf_data = await resp.read()
                    text_data = await get_text_from_pdf(pdf_data)
                    return text_data
                except Exception as e:
                    print(f"❌ CANNOT PROCESS ATTACHMENT{attachment.filename} : {e}")
                    return "❌ CANNOT PROCESS ATTACHMENT "
            else:
                try:
                    text_data = await resp.text()
                    return text_data
                except Exception as e:
                    print(f"❌ CANNOT PROCESS ATTACHMENT{attachment.filename} : {e}")
                    return "❌ CANNOT PROCESS ATTACHMENT"
            
async def get_text_from_pdf(pdf_data):
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
    text = ""
    for page in pdf_document:
        text += page.get_text()
    pdf_document.close()
    return text

#------------------------- Youtube and Links ----------------------------------------------------

async def get_transcript_from_url(url,message):
    
    if "youtube.com" in url or "youtu.be" in url:
        await message.add_reaction('📺')
        return get_youtube_transcript(url)
    else:
        await message.add_reaction('🔗')
        return scrape_website(url)

# Function to get YouTube transcript
def get_youtube_transcript(url):
    if PROCESS_YOUTUBE_URLS == False:
        print("I AM FALSE")
        return "❌ Youtube scraping is disabled"
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return "❌ Invalid YouTube URL"
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        return f"❌ Error retrieving YouTube transcript: {e}"

# Function to extract video ID from YouTube URL
def extract_youtube_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.match(pattern, url)
    return match.group(1) if match else None

# Function to scrape website content
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text content from the website
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"❌ Error scraping website: {e}"


#--------------------------------------- Run Bot --------------------------------------------
bot.run(DISCORD_KEY)
