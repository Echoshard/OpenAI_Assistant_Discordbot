
# OpenAI Assistant Discordbot

 Discord bot that leverages the power of OpenAI's Assistants API to interact with users in both text and image formats. It processes messages and images sent to it, generating creative and engaging responses. 

This bot is similar to the Gemini Discord bot https://github.com/Echoshard/Gemini_Discordbot

## Advantages
- **Conversation Threads:** OpenAI threads are very long allowing users to have long converations and ask followup information about images
- **Knowledge Base:** When setting up an assistant you can add a knowledge base to them having the reference custom data allowing for RAG like intergration

## Disavantages
- **Slower response time:** Assistants are slower to respond then Gemini. 
- **Expense:** OpenAI does not offer a free API unlike Gemini

## Features

- **AI-Driven Text Responses:** OpenAI Bot can generate text responses.
- **Image Processing:** The bot can also respond to images, combining text and visual inputs for a more engaging interaction. (Images should be under 2.5 Megs)
- **User Message History Management:** It maintains a thread of user interactions via discordIDs, allowing for context-aware conversations.
- **Customizable Settings:** Allows user to enable or disable features such as URL scraping, youtube, image or text attachments

## Setup

### Requirements

- aiohttp
- discord.py
- openai
- python-dotenv
- youtube-transcript-api (youtube transcript)
- PyMuPDF (PDF reading)
- requests
- beautifulsoup4 (scraping)


### Installation

1. Clone the repository to your local machine.
2. Install the required Python libraries:

   ```
   pip install -U -r requirements.txt
   ```
   Or one line install
   ```
   pip install discord.py openai aiohttp python-dotenv youtube-transcript-api PyMuPDF requests beautifulsoup4
   ```
   
The bot will start listening to messages in your Discord server. It only responds to direct messages

## Configuration

1. Create a `.env` file and copy the contents of `.env.example` into it

2. Fill in the following values:

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `OPENAI_API_KEY`: Your OpenAI API key. Google API Key can be acquired from https://platform.openai.com/assistants/
- `MAX_TOKENS`: max amount of tokens it can respond with
- `DEFAULT_ASSISTANT`:Default assistant it will speak with you setup your assistant here https://platform.openai.com/assistants/

Bot Settings:

These are flags that can be used to reduce the functionality of bot

- `PROCESS_IMAGE`: Process attached images
- `PROCESS_TEXT_ATTACHMENTS` Process PDF and txt attachments
- `PROCESS_URL` Scrape urls and process them
- `PROCESS_YOUTUBE_URLS` Scrape youtube transcripts and process them

3. Run `OpenAI_Assistant_DiscordBot.py`


## Commands

- **Mention or DM the bot to activate:** History only works on pure text input
- **Send an Image:** The bot will respond with an AI-generated interpretation or related content.
- **Type 'RESET' or CLEAN :** Clears the message history for the user.

## Additional Items 

- Youtube URLs - Read's the transcript from a youtube video.
- PDF / TXT - PDF or TXT will be added into your prompt
- Web URL - It will scrape the text off a URL (As well as it can)

When posting a URL or an attachment we recommend you give it context such as "Give me give bullets about"

Examples:
`Write me a tweet about {url}`
`What did they think of {youtube link}`

## Development

Feel free to fork the project and customize it according to your needs. Make sure to follow the guidelines set by Discord and OpenAI for bot development and API usage.

## Limitations

Web Urls: 
- Google docs URLs don't parse correctly
- Some URLs will not parse correctly 

Youtube Videos:

- Transcripts of age restricted or other block content cannot be read
- The youtube transcriber does work on some servers with static IP's they are blocked by youtube.
