import speech_recognition as sr
import text_to_image as tti

mic = sr.Recognizer()
save_keyword = "over"
write_keyword = "and out"

to_print = []

# check if 'save_keyword' is in user's speech
def check_save_keyword(phrase):
    # keyword must be in phrase and be the last or second to last position
    if(save_keyword in phrase):
        if(phrase.split()[-1] == save_keyword):
            final_str = phrase.replace(" " + save_keyword, "")    
            to_print.append(final_str)
        elif(phrase.split()[-3] == save_keyword):
            check_write_keyword(phrase)
            
# check if 'write_keyword' is in user's speech
def check_write_keyword(phrase):
    if((write_keyword in phrase) and (phrase.split()[-1] == write_keyword.split()[-1])):
        final_str = phrase.replace(" " + save_keyword, "").replace(" " + write_keyword, "")
        to_print.append(final_str)
    
def start():
    for i in range(2): # TODO: change loop for an infinite loop
        with sr.Microphone() as source:
            mic.adjust_for_ambient_noise(source)
            print("Say something: ")
            audio = mic.listen(source, timeout=5, phrase_time_limit=5) # TODO: mess around to find best timeout and phrase_time_limit

        try:
            phrase = mic.recognize_google(audio)
            check_save_keyword(phrase)
            print("You said: {0}".format(phrase)) # TODO: remove print (only useful for testing)
        except sr.UnknownValueError:
            print("Oops, sorry... Didn't catch that :(")

    # create a txt file with phrases listened (delete previous txt and generate new one)
    text_file = open("text_file.txt", "w")
    for item in to_print:
        text_file.write(item)
        text_file.write("\n")