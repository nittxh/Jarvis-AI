from Frontend.GUI import (  
    GraphicalUserInterface,  
    SetAssistantStatus,  
    ShowTextToScreen,  
    TempDirectoryPath,  
    SetMicrophoneStatus,  
    AnswerModifier,  
    QueryModifier,  
    GetMicrophoneStatus,  
    GetAssistantStatus  
)  

from Backend.Model import FirstLayerDMM  
from Backend.RealtimeSearchEngine import RealtimeSearchEngine  
from Backend.Automation import Automation  
from Backend.SpeechToText import SpeechRecognition  
from Backend.Chatbot import ChatBot  
from Backend.TextToSpeech import TextToSpeech  
from dotenv import dotenv_values  
from asyncio import run  
from time import sleep  
import subprocess  
import threading
import json
import os

import os
from dotenv import load_dotenv

from dotenv import load_dotenv
import os

load_dotenv()
Assistantname = os.getenv("Assistantname", "Assistant")



env_vars = dotenv_values(".env")  
Username = env_vars.get("Username")  
Assistantname = env_vars.get("Assistantname")  
DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?  
{Assistantname}: I am doing well. How may I help you?'''  
subprocesses = []  
Functions = ['open', 'close', 'play', 'system', 'content', 'google search', 'youtube search']  

# Ensure required directories and files exist.
def ensure_directories_and_files():
    os.makedirs('Data', exist_ok=True)
    if not os.path.exists('Data/ChatLog.json'):
        with open('Data/ChatLog.json', 'w', encoding='utf-8') as file:
            json.dump([], file)


def ShowDefaultChatIfNoChats():  
    with open(r'Data/ChatLog.json', 'r', encoding='utf-8') as file:  
        if len(file.read().strip()) < 5:  
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:  
                db_file.write("")  
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as res_file:  
                res_file.write(DefaultMessage)  

def ReadChatLogJson():  
    with open(r'Data/ChatLog.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():  
    json_data = ReadChatLogJson()  
    formatted_chatlog = ""  
    for entry in json_data:  
        if entry['role'] == 'user':  
            formatted_chatlog += f"User: {entry['content']}\n"  
        elif entry['role'] == 'assistant':  
            formatted_chatlog += f"Assistant: {entry['content']}\n"  

            formatted_chatlog = formatted_chatlog.replace("User", f"{Username} ") if Username else formatted_chatlog
            formatted_chatlog = formatted_chatlog.replace("Assistant", f"{Assistantname} ") if Assistantname else formatted_chatlog


    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:  
        file.write(AnswerModifier(formatted_chatlog))  

def ShowChatsOnGUI():
    with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as file:  
        data = file.read()  
        if data.strip():  
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as res_file:  
                res_file.write(data)  

def InitialExecution():  
    SetMicrophoneStatus("False")  
    ShowTextToScreen("")  
    ensure_directories_and_files()
    ShowDefaultChatIfNoChats()  
    ChatLogIntegration()  
    ShowChatsOnGUI()  

InitialExecution()  

def MainExecution():  
    TaskExecution = False  
    ImageExecution = False  
    ImageGenerationQuery = ""   
    
    SetAssistantStatus("Listening....")
    Query = SpeechRecognition()  
    ShowTextToScreen(f"{Username} : {Query}!")  
    SetAssistantStatus("Thinking ...")  
    Decision = FirstLayerDMM(Query)  

    print("")  
    print(f"Decision : {Decision}")  
    print("")  

    G = any([i for i in Decision if i.startswith("general")])  
    R = any([i for i in Decision if i.startswith("realtime")])  

    Merged_query = " and ".join(  
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]  
    )

    for queries in Decision:  
        if 'generate' in queries:  
            ImageGenerationQuery = str(queries)  
            ImageExecution = True  

    for queries in Decision:  
        if not TaskExecution:  
            if any(queries.startswith(func) for func in Functions):  
                run(Automation(list(Decision)))  
                TaskExecution = True  

    if ImageExecution:  
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file:  
            file.write(f'{ImageGenerationQuery}')  
        
        try:
            p1 = subprocess.Popen(
            ['python', r'Backend\ImageGeneration.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=False
            )
            stdout, stderr = p1.communicate()
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())

        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if G and R or R:  
        SetAssistantStatus("Searching ...")  
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))  
        ShowTextToScreen(f"[{Assistantname}]: {Answer}")  
        SetAssistantStatus("Answering ...")  
        TextToSpeech(Answer)  
        return True  
    else:  
        for Queries in Decision:  
            if "general" in Queries:  
                SetAssistantStatus("Thinking ...")  
                QueryFinal = Queries.replace("general", "")  
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering.....")
                TextToSpeech(Answer)
                return True
            
            elif "realtime" in Queries:  
                SetAssistantStatus("Searching ...")  
                QueryFinal = Queries.replace("realtime", "*")  
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))  
                ShowTextToScreen(f"[{Assistantname}]: {Answer}")  
                SetAssistantStatus("Answering ...")  
                TextToSpeech(Answer)  
                return True  

            elif "exit" in Queries:  
                QueryFinal = "Okay, Bye!"  
                Answer = ChatBot(QueryModifier(QueryFinal))  
                ShowTextToScreen(f"[{Assistantname}]: {Answer}")  
                SetAssistantStatus("Answering ...")  
                TextToSpeech(Answer)  
                SetAssistantStatus("Exiting ...")  
                os._exit(0)

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()  

        if CurrentStatus == "True":  
            MainExecution()  
        else:  
            AIStatus = GetAssistantStatus()  
            if "Available..." in AIStatus:  
                sleep(0.1)  
            else:  
                SetAssistantStatus("Available...")  

def SecondThread():  
    GraphicalUserInterface()  

if __name__ == "__main__":  
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
