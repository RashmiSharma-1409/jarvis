
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import speech_recognition as sr
import pyttsx3
import openai
from config import apikey
import datetime
import os
import webbrowser
import random
import pickle
import threading
import re
from tkinter import Tk, Label
from PIL import Image, ImageTk  # For image handling
import pygame  # For music handling

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("volume", 0.9)

# Set OpenAI API key
openai.api_key = apikey

chat_history = []  # To maintain conversation history with ChatGPT

# File to store tasks
TASKS_FILE = "tasks.pkl"

# Initialize pygame mixer
pygame.mixer.init()

# Function for text-to-speech
def say(text):
    engine.say(text)
    engine.runAndWait()

# Function to display the Jarvis logo
def display_logo():
    window = Tk()
    window.title("Jarvis Activated")
    window.geometry("400x400")
    window.configure(bg="black")

    try:
        image = Image.open("image.png.png")  # Replace with your image filename
        image = image.resize((300, 300), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(image)
        label = Label(window, image=img, bg="black")
        label.pack(expand=True)

        # Keep the window open until explicitly destroyed
        window.mainloop()
    except Exception as e:
        print(f"Error loading the image: {e}")

# Function for OpenAI chat
def chat_with_gpt(query):
    global chat_history
    try:
        chat_history.append({"role": "user", "content": query})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_history,
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        reply = response.choices[0].message["content"].strip()
        say(reply)
        chat_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        say("Sorry, I encountered an error while processing your request.")
        print(f"Error in chat_with_gpt: {e}")
        return "Error"

# Function for recognizing voice commands
def takeCommand():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return ""

# Task Management Functions
def load_tasks():
    try:
        with open(TASKS_FILE, "rb") as file:
            tasks = pickle.load(file)
    except (FileNotFoundError, EOFError):
        tasks = []
    return tasks

def save_tasks(tasks):
    with open(TASKS_FILE, "wb") as file:
        pickle.dump(tasks, file)

def add_task(task):
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    say(f"Task added: {task}")
    print(f"Task added: {task}")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        say("Your to-do list is empty.")
        print("To-do list is empty.")
    else:
        say("Here are your tasks:")
        for i, task in enumerate(tasks, start=1):
            say(f"Task {i}: {task}")
            print(f"{i}. {task}")

def remove_task(task_number):
    tasks = load_tasks()
    try:
        removed_task = tasks.pop(task_number - 1)
        save_tasks(tasks)
        say(f"Task removed: {removed_task}")
        print(f"Task removed: {removed_task}")
    except IndexError:
        say("Invalid task number.")
        print("Invalid task number.")

# Reminder Function
def set_reminder(task, time):
    current_time = datetime.datetime.now()
    reminder_time = current_time + datetime.timedelta(minutes=time)
    say(f" set Reminder for task: {task} in {time} minutes.")
    print(f"Reminder set for {task} at {reminder_time.strftime('%H:%M')}")

    def reminder():
        while True:
            if datetime.datetime.now() >= reminder_time:
                say(f"Reminder: {task}")
                print(f"Reminder: {task}")
                break

    threading.Thread(target=reminder, daemon=True).start()

# Volume Control Function
def set_volume(delta):
    """
    Adjust the system volume.

    Parameters:
        delta (float): The amount to increase or decrease the volume.
                      Positive values increase volume, negative values decrease it.
    """
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None
    )
    volume = interface.QueryInterface(IAudioEndpointVolume)

    # Get the current volume level (range: 0.0 to 1.0)
    current_volume = volume.GetMasterVolumeLevelScalar()

    # Calculate the new volume level
    new_volume = current_volume + delta

    # Clamp the volume level between 0.0 and 1.0
    new_volume = max(0.0, min(1.0, new_volume))

    # Set the new volume level
    volume.SetMasterVolumeLevelScalar(new_volume, None)

    say(f"Volume set to {new_volume * 100:.0f}%")
    print(f"Volume set to {new_volume * 100:.0f}%")

# Music Playback Functions
def play_music(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    say("Music playing.")


def pause_music():
    pygame.mixer.music.pause()
    say("Music paused.")


def unpause_music():
    pygame.mixer.music.unpause()
    say("Music resumed.")


def stop_music():
    pygame.mixer.music.stop()
    say("Music stopped.")

# Stone, Paper, Scissors Game
def play_stone_paper_scissors():
    choices = ["stone", "paper", "scissors"]
    assistant_choice = random.choice(choices)

    say("Let's play Stone, Paper, Scissors. Say your choice.")
    user_choice = takeCommand()

    if user_choice not in choices:
        say("Invalid choice. Please say stone, paper, or scissors.")
        return

    say(f"I chose {assistant_choice}.")

    if user_choice == assistant_choice:
        say("It's a tie!")
    elif (user_choice == "stone" and assistant_choice == "scissors") or \
         (user_choice == "paper" and assistant_choice == "stone") or \
         (user_choice == "scissors" and assistant_choice == "paper"):
        say("Congratulations! You win!")
    else:
        say("I win! Better luck next time.")

# Function to execute commands
def executeCommand(query):
    if "add task" in query:
        task = query.replace("add task", "").strip()
        add_task(task)

    elif "show tasks" in query or "to-do list" in query:
        show_tasks()

    elif "remove task" in query:
        try:
            task_number = int(query.split()[-1])
            remove_task(task_number)
        except ValueError:
            say("Please specify the task number to remove.")
            print("Please specify the task number to remove.")

    elif "set reminder" in query:
        match = re.search(r"set reminder(?: for)? (.+?) in (\d+) minutes", query)
        if match:
            task = match.group(1).strip()
            time = int(match.group(2).strip())
            set_reminder(task, time)
        else:
            say("Sorry, I couldn't understand the reminder format. Please say something like 'set reminder for meeting in 10 minutes'.")
            print("Reminder format not recognized.")

    elif "increase volume" in query:
        set_volume(0.1)  # Increase volume by 10%

    elif "decrease volume" in query:
        set_volume(-0.1)  # Decrease volume by 10%

    elif "play music" in query:
        file_path = query.replace("play music", "").strip()
        if os.path.exists(file_path):
            play_music(file_path)
        else:
            say("Music file not found.")

    elif "pause music" in query:
        pause_music()

    elif "resume music" in query:
        unpause_music()

    elif "stop music" in query:
        stop_music()

    elif "play stone paper scissors" in query:
        play_stone_paper_scissors()

    elif "who is the most beautiful girl in the world" in query:
        say("Shital is the most beautiful girl in the world!")

    elif "who is the most beautiful teacher in the world" in query:
        say("UPASANA MADAM is the most beautiful teacher in the world!")

    elif "who is the most beautiful boy in the world" in query:
        say("Sai Prakash is the most beautiful boy in the world!")

    elif ".com" in query:
        website = query.split()[-1]
        if not website.startswith("http://") and not website.startswith("https://"):
            website = "https://" + website
        say(f"Opening {website} in browser.")
        webbrowser.open(website)

    elif "open" in query:
        app_name = query.replace("open", "").strip().lower()
        say(f"Opening {app_name}")
        try:
            if app_name == "calculator":
                os.system("start calc")
            elif app_name == "notepad":
                os.system("start notepad")
            elif app_name == "paint":
                os.system("start mspaint")
            else:
                os.system(f"start {app_name}")
        except Exception as e:
            say(f"Sorry, I couldn't open {app_name}.")
            print(f"Error: {e}")

    elif "the time" in query:
        current_time = datetime.datetime.now().strftime("%H:%M")
        say(f"The time is {current_time}")

    elif "the date" in query:
        current_date = datetime.datetime.now().strftime("%A, %d %B %Y")
        say(f"Today's date is {current_date}")

    elif "tell me a joke" in query:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call fake spaghetti? An impasta!",
            "Why don’t skeletons fight each other? They don’t have the guts!",
        ]
        joke = random.choice(jokes)
        say(joke)

    elif "shutdown laptop" in query:
        say("Shutting down the laptop. Goodbye!")
        os.system("shutdown /s /t 1")

    elif "restart laptop" in query:
        say("Restarting the laptop. Goodbye!")
        os.system("shutdown /r /t 1")

    elif "lock laptop" in query:
        say("Locking the laptop.")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif "quit" in query or "exit" in query:
        say("Goodbye!")
        # Close the logo window
        import ctypes
        ctypes.windll.user32.PostMessageW(0xffff, 0x0010, 0, 0)
        exit()

    else:
        chat_with_gpt(query)

# Main driver function
if __name__ == "__main__":
    say("Welcome to Jarvis.AI")
    print("Welcome to Jarvis.AI")

    # Start the logo display in a separate thread
    logo_thread = threading.Thread(target=display_logo, daemon=True)
    logo_thread.start()

    while True:
        print("Waiting for 'Hi Jarvis' to activate...")
        query = takeCommand()

        if "hi jarvis" in query:
            # Get the current hour
            current_hour = datetime.datetime.now().hour

            # Determine the greeting based on the time of day
            if 5 <= current_hour < 12:
                greeting = "Good Morning!"
            elif 12 <= current_hour < 18:
                greeting = "Good Afternoon!"
            else:
                greeting = "Good Evening!"

            # Respond with the appropriate greeting
            say(f"{greeting} Jarvis is now active and listening for commands...")
            print(f"{greeting} Jarvis is now active and listening for commands...")

            while True:
                query = takeCommand()
                if query:
                    executeCommand(query)
                if "bye jarvis" in query or "deactivate" in query:
                    say("Goodbye! Call me if you need help again.")
                    # Close the logo window
                    import ctypes
                    ctypes.windll.user32.PostMessageW(0xffff, 0x0010, 0, 0)
                    break
