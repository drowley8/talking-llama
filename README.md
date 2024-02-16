# Talking Llama

## Introduction
The purpose of this code is to allow a client to connect to an Ollama server, chat with the llm, and then locally synthesize the response as speech using Piper TTS. The faster the Ollama server, the smoother the response.

## Prerequisites
You will need access to an Ollama server. This can be hosted on another machine, or locally. If hosted on another machine, you will need the IP address of that machine.

Piper requires voice model files in order to synthesize. A list of Piper voice models can be found on Piper's [GitHub page](https://github.com/rhasspy/piper).

Pygame is relied on to provide an interface for playing audio without the need to first save out as a temporary `.wav` file.

This project requires Python 3.

To get the rest of the project dependencies, run
```sh
pip install -r requirements.txt
```

## Configuration
There is no configuration file yet. Look for these constants in `main.py` to change some important settings:
- `OLLAMA_SERVER` - the IP address of the server running Ollama. If running Ollama locally, set this to `"localhost"`
- `OLLAMA_PORT` - The port that Ollama is listening on. By default, Ollama listens on port `11434`.
- `OLLAMA_MODEL` - Make sure the model you set here is installed on the Ollama server. I have no idea what happens if it's not installed.
- `SAMPLE_RATE` - The sample rate for the vocal output. This can vary between Piper voice models, so make sure to reference the model card for your particular Piper model.
- `PIPER_MODEL` - The filename of the Piper model. You should have an accompanying config file with your model called `<piper-model-name>.json`.
- `PIPER_VOICE` - Some Piper models have more than one voice available to use. Be familiar with the model you have chosen. When in doubt, leave this at `0`.

## Usage notes
```sh
python3 main.py
```

To end your conversation, press ctrl-c or ctrl-d.

There is currently not an implementation in this code to set the system message. To set a custom system message, instead create a modelfile as per the Ollama documentation, create a new model directly through Ollama, and then use the name of your new mode as `OLLAMA_MODEL`.

## Implementation notes
This project uses multi-threading in order to allow Piper and Pygame to speak complete sentences as they arrive while the main thread continues to stream in new tokens from the Ollama connection and immediately print them to screen.

### **Regarding the way Ollama works:** 
Ollama expects to receive a list of message objects, each message having this format:
```json
{
    'role' : <role>,
    'content' : <message-text>
}
```
`role` can only be one of `'assistant'`, `'user'`, or `'system'`.

The llm receives and processes this entire list *every* time a new message is appended. The consequence of this is increasingly longer response times due to more and more data needing to be processed.

Future implementation of this code will likely provide some configuration to allow for trimming this message list down to an arbitrary length to keep response times feeling snappy. The consequence of this is that converations will inherently have a short term memory.