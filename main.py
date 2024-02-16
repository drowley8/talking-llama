'''basic module for sending messages to a live ollama server, voice synthesizing
and playing back the responses. The driver code is interactive'''

import threading  # allow some processes to run asynchonously
from piper import PiperVoice  # TTS engine
import pygame  # multi-platform audio output
import ollama  # ollama API and related

OLLAMA_SERVER = "localhost"
OLLAMA_PORT = 11434

OLLAMA_MODEL = "dolphin-mistral"

SAMPLE_RATE = 20000
CHANNELS = 1

PIPER_MODEL = "en_US-libritts_r-medium.onnx"
PIPER_MODEL_JSON = PIPER_MODEL + ".json"
PIPER_VOICE = 0

client = ollama.Client(f"http://{OLLAMA_SERVER}:{OLLAMA_PORT}/")

pygame.mixer.init(frequency=SAMPLE_RATE, channels=CHANNELS)

piper_voice = PiperVoice.load(PIPER_MODEL, PIPER_MODEL_JSON)

sentence_queue = []

running = True  # global running state for threads to know when to quit


def play_sound_queue():
    '''threaded out loop. checks for sentences in sentece queue, sends them to
    piper to be converted to audio, which is then appended to sound_queue.
    checks for sentences in sound queue, sends them to pygame to play on
    speakers if they're not already busy. violates single-responsibiliry rule'''
    sound_queue = []
    while running:
        if sentence_queue:
            if len(sentence_queue[0]) > 1:
                sound_data = b"".join(
                    piper_voice.synthesize_stream_raw(
                        sentence_queue.pop(0).strip(), PIPER_VOICE
                    )
                )
                sound = pygame.mixer.Sound(buffer=sound_data)
                sound_queue.append(sound)
            else:
                sentence_queue.pop(0)
        if sound_queue:
            if not pygame.mixer.get_busy():
                pygame.time.wait(750)  # a delay to space out sentences a bit
                sound_queue.pop(0).play()


def process_lines(stream):
    """takes an ollama stream as imput, prints new tokens to the screen, and
    attempts to reform the tokens into complete sentences. returns complete
    sentences"""
    buffer = []
    for chunk in stream:
        word: str = chunk["message"]["content"]
        print(word, end="", flush=True)
        buffer.append(word)
        if word.endswith((".", "!", "?", ":", ";", '."\n', '?"\n', '!"\n')):
            yield "".join(buffer)
            buffer = []
    if buffer:
        if len(buffer) > 1:
            yield "".join(buffer)


def construct_message(role, text):
    """contstructs a message, which is the form of data that ollama expects to
    receive"""
    if not text:
        return []
    message = [{"role": role, "content": text}]
    return message


def main():
    """driver code. also main loop"""
    global running
    thread = threading.Thread(target=play_sound_queue)
    thread.start()

    messages = []

    try:
        while running:
            user_input = input("\n>>> ")
            print()
            user_message = construct_message("user", user_input)
            messages += user_message  # append user message to message chain
            stream = client.chat(model=OLLAMA_MODEL,
                                 stream=True,
                                 messages=messages)
            machine_response_text = []
            for line in process_lines(stream):
                sentence_queue.append(line)
                machine_response_text.append(line)
            assistant_message = construct_message(
                "assistant", "".join(machine_response_text)
            )
            messages += assistant_message  # append assistant message to message chain
    except (KeyboardInterrupt, EOFError):
        print("\nquiting...")
        running = False

    while pygame.mixer.get_busy():
        pass  # to allow piper to finish speaking before quitting
    thread.join()


if __name__ == "__main__":
    main()
