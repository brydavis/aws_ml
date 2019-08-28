import os, boto3
import requests
import json
from pprint import pprint
import re

def get_news(api_key):
    NEWS_URL = (
        'https://newsapi.org/v2/top-headlines?'
        'country=us&'
        'apiKey=' + api_key
    )
    response = requests.get(NEWS_URL)
    return response.json()



def analyze_text_sentiment(source_text, source_language):
    try:
        comprehend = boto3.client(
            'comprehend',
            region_name='us-east-1',
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )      
        return comprehend.detect_sentiment(
            Text=source_text, 
            LanguageCode=source_language
        )
    except Exception as e:
        print(e)



def text_to_speech(filename, text, format='mp3', voice='Matthew'):
    polly = boto3.client(
        'polly', 
        region_name='us-east-1',
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    # https://docs.aws.amazon.com/polly/latest/dg/voicelist.html
    resp = polly.synthesize_speech(OutputFormat=format, Text=text, VoiceId=voice)
    with open(f"tmp/{filename}.{format}", 'wb') as soundfile:
        soundBytes = resp['AudioStream'].read()
        soundfile.write(soundBytes)



def translate_text(source_text, source_language, target_language):
    try:
        translate = boto3.client(
            'translate',
            region_name='us-east-1',
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )    

        # https://docs.aws.amazon.com/translate/latest/dg/how-it-works.html#how-it-works-language-codes
        response = translate.translate_text (
            Text = source_text,
            SourceLanguageCode = source_language,
            TargetLanguageCode = target_language,
        )
        return response["TranslatedText"]
    
    except Exception as e:
        print(e)



def translate_and_transcribe_text(source_text, source_language, target_language, target_filename, voice):
    translation = translate_text(source_text, source_language, target_language)
    text_to_speech(
        target_filename,
        translation,
        voice
    )


def extract_text_from_image(filename):
    # Read document content
    with open(filename, 'rb') as document:
        imageBytes = bytearray(document.read())


    # Create a Amazon Textract client
    textract = boto3.client(
        'textract', 
        region_name='us-west-2',
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )  

    # Call Amazon Textract
    response = textract.detect_entities_from_image(Document={'Bytes': imageBytes})

    # Print detected text
    return [
        item["Text"]
        for item in response["Blocks"]
        if item["BlockType"] == "LINE"
    ]









def detect_things_from_image(filename):
    rekognition=boto3.client(
        'rekognition', 
        region_name='us-west-2',
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )  

    with open(filename, 'rb') as image:
        response = rekognition.detect_labels(Image={'Bytes': image.read()})

    return {
        label['Name']: str(label['Confidence'])
        for label in response['Labels']
    }



def compare_faces(source_filename, target_filename, threshold=0):
    rekognition = boto3.client(
        'rekognition', 
        region_name='us-west-2',
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )  
    
    imageSource=open(source_filename,'rb')
    imageTarget=open(target_filename,'rb')

    response = rekognition.compare_faces(
        SimilarityThreshold=threshold,
        SourceImage={'Bytes': imageSource.read()},
        TargetImage={'Bytes': imageTarget.read()}
    )

    imageSource.close()
    imageTarget.close()

    for faceMatch in response['FaceMatches']:
        position = faceMatch['Face']['BoundingBox']
        confidence = str(faceMatch['Face']['Confidence'])
        print('The face at ' +
                str(position['Left']) + ' ' +
                str(position['Top']) +
                ' matches with ' + confidence + '% confidence')




if __name__ == "__main__":
    # https://newsapi.org/docs/get-started
    NEWS_API_KEY = "4c078cc881a24c95b5d92ea5fa1f4b14"

    # Language Codes
    ENGLISH = 'en'
    JAPANESE = 'ja'
    FRENCH = 'fr'
    CHINESE =  'zh'

    # GET NEWS DATA
    news = get_news(NEWS_API_KEY)

    # LET'S COVERT THE FIRST FIVE
    # ARTICLES FROM TEXT TO SPEECH
    pprint(news["articles"][:5])

    for article in news["articles"][:5]:
        try:
            filename = re.sub(r"\W+", "_", article["title"]).lower()
            text = article["title"] + "... " + article["description"]

            # PART ONE
            text_to_speech(
                filename,
                text,
            )

            # PART TWO
            translate_and_transcribe_text(
                source_text=text,
                source_language=ENGLISH,
                target_language=CHINESE,
                target_filename=f"{filename}_chinese",
                voice="Zhiyu",
            )
        except Exception as e:
            print(e)


    lyrics = [
        # Nirvana
        "I wish I was like you. Easily amused. Find my nest of salt. Everything’s my fault.",
        # Nine Inch Nails
        "And you could have it all/ My empire of dirt/ I will let you down/ I will make you hurt.",
        # Justin Bieber
        "Every day. I bring the sun around. I sweep away the clouds. Smile for me.",
        # Kendrick Lamar
        "First you get a swimming pool full of liquor, then you dive in it/ Pool full of liquor, then you dive in it/ I wave a few bottles, then I watch ‘em all flock.",
        # Janet Jackson
        "Come on baby let's get away. Let's save your troubles for another day. Come go with me we've got it made. Let me take you on an escapade (let's go)",
        # Rick Astley
        "Never gonna give you up. Never gonna let you down. Never gonna run around and desert you.",
        # Michael Jackson
        "I want to rock with you... all night. Dance you into day... sunlight. I want to rock with you... all night. Rock the night away",
    ]

    for lyre in lyrics:
        print(
            lyre,
            analyze_text_sentiment(lyre, ENGLISH),
        )



    # IMAGE ANALYSIS
    source_filename = "inslee.png"
    
    # TEXT FROM IMAGE
    extracted_lines_text = extract_text_from_image(source_filename)
    pprint(extracted_lines_text)
    
    # THINGS IN IMAGE    
    things = detect_things_from_image(source_filename)
    pprint(things)

    target_filename='hickenlooper.png'
    compare_faces(source_filename, target_filename, 70)    

    target_filename='inslee2.png'
    compare_faces(source_filename, target_filename, 70)    






    # THINGS IN IMAGE    
    # print("Example: Los Angeles Skyline")
    # things = detect_things_from_image("lax.jpg")
    # pprint(things)

    # print("-"*25)

    # print("Example: Food Blog")
    # things = detect_things_from_image("food.jpg")
    # pprint(things)

    # print("-"*25)
    
    # print("Example: Homer Simpson")
    # things = detect_things_from_image("homer.png")
    # pprint(things)

    # print("Example: Idris Elba")
    # things = detect_things_from_image("idris.jpg")
    # pprint(things)

    # print("Example: Bedding")
    # things = detect_things_from_image("bed.jpg")
    # pprint(things)

