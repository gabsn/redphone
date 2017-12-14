
import requests
import os
import time
import io
import slackclient
import pyaudio
import wave

class TextToSpeech:
    def __init__(self):
        self.url = "https://stream.watsonplatform.net/text-to-speech/api"
        self.username = os.environ.get('WATSON_USERNAME')
        self.password = os.environ.get('WATSON_PASSWORD')
        self.voices = {
            'portuguese': 'pt-BR_IsabelaVoice',             # female
            'castilian_spanish_m': 'es-ES_EnriqueVoice',    # male
            'castilian_spanish_f': 'es-ES_LauraVoice',      # female
            'latin_spanish': 'es-LA_SofiaVoice',            # female
            'na_spanish': 'es-US_SofiaVoice',               # female
            'french': 'fr-FR_ReneeVoice',                   # female
            'german_f': 'de-DE_BirgitVoice',                # female
            'german_m': 'de-DE_DieterVoice',                # male
            'italian': 'it-IT_FrancescaVoice',              # female
            'japanese': 'ja-JP_EmiVoice',                   # female
            'british': 'en-GB_KateVoice',                   # female
            'american_f_1': 'en-US_LisaVoice',              # female
            'american_f_2': 'en-US_AllisonVoice',           # female
            'american_m': 'en-US_MichaelVoice'              # male
        }

    def synthesize(self, text, voice):
        return requests.get(self.url + "/v1/synthesize",
            auth=(self.username, self.password),
            params={'text': text, 'voice': self.voices[voice], 'accept': 'audio/wav'},
            stream=True, verify=False
        )

class AudioPlayer:
    def say(self, data_bytes):
        #define stream chunk
        chunk = 1024

        #open a wav format music
        f = wave.open(io.BytesIO(data_bytes),"rb")

        #instantiate PyAudio
        p = pyaudio.PyAudio()
        #open stream
        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                        channels = f.getnchannels(),
                        rate = f.getframerate(),
                        output = True)
        #read data
        data = f.readframes(chunk)

        #play stream
        while data:
            stream.write(data)
            data = f.readframes(chunk)

        #stop stream
        stream.stop_stream()
        stream.close()

        #close PyAudio
        p.terminate()


class SlackListener:
    def __init__(self):
        self.token = os.environ.get('SLACK_BOT_TOKEN')
        self.channel = 'outage'

        # initialize slack client
        self.sc = slackclient.SlackClient(self.token)

        # check if everything is alright
        is_ok = self.sc.api_call("users.list").get('ok')
        print(is_ok)

    def get_voice(self, user):
        name = self.get_user_name(user)
        if name == 'Vlad':
            return 'german_m'
        elif name == 'Isabelle Sauve':
            return 'american_f_1'
        elif name == 'Gabin Marignier':
            return 'french'
        elif name == 'Léo Cavaillé':
            return 'italian'
        elif name == 'Capitaine Vélo':
            return 'japanese'
        elif name == 'Youpinadi':
            return 'latin_spanish'
        elif name == 'Stefano':
            return 'portuguese'
        else:
            return 'american_m'

    def get_channel_name(self, channel_id):
        channel_info = self.sc.api_call("channels.info", channel=channel_id)
        return channel_info.get("channel", {}).get('name', '')

    def get_user_name(self, user_id):
        user_info = self.sc.api_call("users.info", user=user_id)
        return user_info.get("user", {}).get("profile", {}).get("real_name", '')

    def write_to_chan(self, msg):
        self.sc.api_call(
                "chat.postMessage",
                channel="#"+self.channel,
                text=msg)

    def handle_event(self, event):
        if event.get('type') == 'message' and self.get_channel_name(event.get('channel')) == self.channel:
            msg = event.get('text')
            print(msg)

            watson = TextToSpeech()
            voice = self.get_voice(event.get('user'))
            response = watson.synthesize(msg, voice)
            response.raise_for_status()

            speaker = AudioPlayer()
            speaker.say(response.content)

    def listen_to_chan(self):
        if self.sc.rtm_connect():
            print('Slack client connected...')
            while True:
                events = self.sc.rtm_read()
                for event in events:
                    self.handle_event(event)
                time.sleep(0.1)
        else:
            print('Connection to Slack failed.')


if __name__=='__main__':
    slack_listener = SlackListener()
    slack_listener.write_to_chan("Ready to call an outage :red_circle:")
    slack_listener.listen_to_chan()
