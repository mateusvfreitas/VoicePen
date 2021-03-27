import speech_recognition as sr
mic = sr.Recognizer()
save_keyword = "house"

to_print = []

# check if 'save_keyword' is in user's speech
def check_save_keyword(phrase):
    # keyword must be in phrase and be the last or second to last position
    if((save_keyword in phrase) and (phrase.split()[-1] == save_keyword or phrase.split()[-2] == save_keyword)):
        final_str = phrase.replace(save_keyword, "")
        to_print.append(final_str)
    
for i in range(2): # TODO: change loop for an infinite loop
    with sr.Microphone() as source:
        mic.adjust_for_ambient_noise(source)
        print(mic.energy_threshold)
        print("Say something: ")

        audio = mic.listen(source, timeout=5, phrase_time_limit=5) # TODO: mess around to find best timeout and phrase_time_limit

    try:
        phrase = mic.recognize_google(audio)
        check_save_keyword(phrase)
        print("You said: {0}".format(phrase)) # TODO: remove print (only useful for testing)
    except sr.UnknownValueError:
        print("Oops, sorry... Didn't catch that :(")

for item in to_print:
    print(item)