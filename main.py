"""Main file for the Jarvis project"""
import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
import openai
import pygame
from pygame import mixer

from record import speech_to_text

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# mixer is a pygame module for playing audio
mixer.init()

# Change the context if you want to change Jarvis' personality
context = "You are Jarvis, a human assistant. You are witty and full of personality. Your answers should be limited to 3-5 short sentences. Stick to the language used by the user unless requested otherwise."
conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"

# User name handling
user_name = None

def request_gpt(prompt: str, user_name: str = None) -> str:
    """
    Send a prompt to the GPT-4 API and return the response.

    Args:
        - prompt: The prompt to send to the API.
        - user_name: The name of the user to personalize the conversation.

    Returns:
        The response from the API.
    """
    messages = [
        {
            "role": "user",
            "content": f"{prompt}",
        }
    ]
    if user_name:
        messages.insert(0, {"role": "system", "content": f"You are speaking with {user_name}."})

    response = openai_client.chat.completions.create(
        messages=messages,
        model="gpt-4-0125-preview",
    )
    return response.choices[0].message.content

async def transcribe(file_name: str) -> str:
    with open(file_name, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    # Access the transcription text. Adjust this line based on the correct attribute.
    return transcript.text  # Or the correct attribute/method as per SDK documentation

def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


if __name__ == "__main__":
    while True:
        # Record audio
        log("Listening...")
        speech_to_text()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        transcription = loop.run_until_complete(transcribe(RECORDING_PATH))
        with open("conv.txt", "a") as f:
            f.write(f"{transcription}\n")
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

        # Get response from GPT-3
        current_time = time()
        if user_name:
            context += f"\n{user_name}: {transcription}\nJarvis: "
        else:
            context += f"\nUser: {transcription}\nJarvis: "
        response = request_gpt(context, user_name)
        context += response
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio
        current_time = time()
        audio_response = openai_client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=response
        )
        audio_response.stream_to_file("audio/response.mp3")
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        # Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.mp3")
        # Add response as a new line to conv.txt
        with open("conv.txt", "a") as f:
            f.write(f"{response}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        if user_name:
            print(f"\n --- {user_name}: {transcription}\n --- JARVIS: {response}\n")
        else:
            print(f"\n --- USER: {transcription}\n --- JARVIS: {response}\n")
