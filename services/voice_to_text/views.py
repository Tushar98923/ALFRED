import pyttsx3 as p
import speech_recognition as sr

# Initialize pyttsx3 for text-to-speech
engine = p.init()

# Set voice properties
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Choose the first voice in the list (default)
engine.setProperty('rate', 180)  # Speed of speech

def speak(text):
    """
    Function to speak the given text using pyttsx3.
    """
    engine.say(text)
    engine.runAndWait()

# Initialize recognizer
r = sr.Recognizer()

def listen_and_recognize():
    """
    Function to listen to the user's voice input and convert it to text using Google API.
    """
    with sr.Microphone() as source:
        # Adjusting for ambient noise and setting energy threshold
        r.energy_threshold = 10000
        r.adjust_for_ambient_noise(source, duration=1.2)
        
        speak('Hello. I am Alfred, your personal assistant. How may I help you?')
        print('Listening...')
        
        # Listen to the input
        audio = r.listen(source)
        
        try:
            # Convert audio to text using Google Web Speech API
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            speak("Sorry, I could not understand what you said.")
            return "Error: Could not understand audio"
        except sr.RequestError:
            speak("Sorry, I am having trouble connecting to the speech service.")
            return "Error: Could not request results"

# Call the function to start listening and converting speech to text
recognized_text = listen_and_recognize()

