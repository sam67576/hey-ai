import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import tkinter as tk
import threading
import cv2
import winsound
import nltk
from nltk.tokenize import word_tokenize
import mysql.connector


db_connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="hey"
)

cursor = db_connection.cursor()


# Initialize speech engine
listener = sr.Recognizer()
engine = pyttsx3.init()
speaking = False  # Flag to prevent multiple runAndWait calls

# Create the root window
root = tk.Tk()
root.title("AI Face")
root.geometry("600x600")

# Create a canvas to draw the face
canvas = tk.Canvas(root, width=600, height=600)
canvas.pack()

# Draw the rectangular eyes with a gap between them
canvas.create_rectangle(80, 150, 280, 250, outline="cyan", fill="black", width=4)
canvas.create_rectangle(320, 150, 520, 250, outline="lightgreen", fill="black", width=4)

# Draw pupils inside the rectangular eyes
canvas.create_oval(150, 190, 210, 230, outline="white", fill="white")  # Left pupil
canvas.create_oval(370, 190, 430, 230, outline="white", fill="white")  # Right pupil

# Draw an open mouth
canvas.create_oval(200, 350, 400, 450, outline="white", fill="black", width=4)

# Text area to show recognized commands
command_label = tk.Label(root, text="Listening...", font=("Arial", 16), bg="black", fg="white")
command_label.pack(pady=20)

# Initial greeting
def initial_greeting():
    talk("Hi, I am hey! How can I help you?")

root.after(1000, initial_greeting)  # Wait for GUI to load, then greet




# Function to handle talking
def talk(text):
    global speaking
    if speaking:  # If already speaking, skip
        return
    speaking = True
    engine.say(text)
    engine.runAndWait()
    speaking = False  # Reset the flag after speech completes

# Function to take command
def take_command():
    try:
        with sr.Microphone() as source:
            talk("Listening")
            print("Listening...")
            listener.adjust_for_ambient_noise(source)
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'hey' in command:
                command = command.replace('hey', '')
                print(f"Command: {command}")
                command_label.config(text=f"Command: {command}")
                return command
            else:
                engine.stop()
    except sr.UnknownValueError:
        talk("Sorry, I didn't catch that. Please say the command again.")
    except sr.RequestError as e:
        talk(f"Could not request results; {e}")
    return ""

# Function to run virtual assistant
def run_vu():
    command = take_command()
    tokens = word_tokenize(command)
    print(tokens)
    
    if "stop" in command:
        talk("Stopping the assistant")
        return True
    if "play" in command:
        song = command.replace("play", "")
        talk("Playing " + song)
        pywhatkit.playonyt(song)
    elif 'time' in command:
        time = datetime.datetime.now().strftime('%I:%M %p')
        talk("Current time is " + time)
    elif 'who' in command:
        person = command.replace('who', '')
        info = wikipedia.summary(person, 2)
        talk(info)
    elif 'joke' in command:
        joke = pyjokes.get_joke()
        talk(joke)
    elif 'scan' in command:
        talk("Opening camera for scanning")
        cam = cv2.VideoCapture(0)
        while cam.isOpened():
            ret, frame1 = cam.read()
            ret, frame2 = cam.read()
            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) < 5000:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
                winsound.PlaySound('alert.wav', winsound.SND_ASYNC)
            if cv2.waitKey(1) == ord('q'):
                break
               
            else:
                cv2.imshow('heys pov', frame1)
    else:
        talk("Please say the command again")
    return False

insert_query = "INSERT INTO memory ( input_text,response_text,interaction_date,model_version,interaction_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
cursor.execute(insert_query,(take_command,talk))
db_connection.commit()

# Main loop to keep the assistant running (runs in a separate thread to avoid freezing the GUI)
def start_assistant():
    while True:
        if run_vu():
            break

# Run the assistant in a separate thread
assistant_thread = threading.Thread(target=start_assistant)
assistant_thread.start()

# Run the Tkinter main loop
root.mainloop()