```python
from genius_scrape import LyricsPuller, SongDataPuller, SongFileProcessor, model
import pandas as pd
import regex as re
```

# Data Acquisition <a name="index"></a>
This notebook will walk through the process of getting the raw data from Genius. You can see the code for the bespoke classes in the external "genius_scrape" file.

1. <a href="#1">Introduction</a>
2. <a href="#2">Search</a>
3. <a href="#3">Filter</a>
4. <a href="#4">Refilter with alternate names</a>
5. <a href="#5">Dates</a>
6. <a href="#6">Output</a>
7. <a href="#7">Lyrics</a>
8. <a href="#8">Verses</a>
9. <a href="#9">Additional cleaning and standardization</a>
10. <a href="#10">Add metrics</a>

### 1. Introduction <a name="1"></a>
<a href="#index">Top</a>

For demonstration, we will get all the songs by Vallejo, California rap veteran [Suga-T](https://suga-t.com/). Suga is Bay Area godfather E-40's brother, is probably best known outside the Bay for her verses on 40 hits like ["Sprinkle Me"](https://www.youtube.com/watch?v=byuQVTdlfos&ab_channel=E40VEVO) and ["Captain Save A Hoe"](https://www.youtube.com/watch?v=_7vQSPBtwyc&ab_channel=E40VEVO). But she is an accomplished artist with a long career in her own right, both solo and as a member of The Click (with 40, cousin B-Legit, and other brother D-Shot).

Here she is in 2019 with E-40.

![Suga-T and E-40](./img/suga_t.jpg)
<center><em>Image courtesy of <a href="https://www.thehypemagazine.com/2019/09/legendary-hip-hop-artist-suga-t-agrees-with-jermaine-dupris-comments-about-female-rappers-releases-w-o-r-k-it-soundtrack/">The Hype Magazine</a></em></center>

### 2. Search <a name="2"></a>
<a href="#index">Top</a>

Getting all of an artist's songs from the Genius API takes a little bit of work. There is an Artists endpoint, but it cannot be queried with a string, only an artist ID.

You can use the API's Search endpoint to get the artist ID, but doing so involves sifting through all the matches in Genius's extensive database. This is no big deal on a small scale, but automating searches for several hundred artists took some work.

To demonstrate this challenge, look at what you get when you search for "Suga-T" on Genius. The API returns 10 songs, but only two of them are by Suga-T.


```python
sdp = SongDataPuller()
sdp.make_headers()
sdp.intake_query({"query": "suga-t"})
query_response = sdp.query_search(sdp.query)

for r in query_response:
    print(f"{r['result']['primary_artist']['name']} - {r['result']['title_with_featured']}")
```

    Star Cast - Suga (Ft. Brittany O'Grady, Jude Demorest & Ryan Destiny)
    Ben&Ben - Sugat (Ft. Munimuni)
    The Fatback Band & With You - (Are You Ready) Do the Bus Stop / Suga (Ft. Sarah Ruba)
    Genius Traducciones al Español - IU - 에잇 (eight) ft. SUGA (Traducción al Español)
    Suga-T - Billy Bad Ass
    須田景凪 (Keina Suda) - 風の姿 (Kaze no Sugata/The Appearance Of The Wind)
    Suga-T - Suga Daddy
    ナナヲアカリ (Nanawoakari) - 一生奇跡に縋ってろ (Isshou Kiseki Ni Sugattero)
    Genius Romanizations - 須田景凪 (Keina Suda) - 風の姿 (Kaze no Sugata) (Romanized)
    Genius English Translations - Ben&Ben - Sugat ft. Munimuni (English Translation)


### 3. Filter <a name="3"></a>
<a href="#index">Top</a>

The filtering step removes any songs in which the target artist (Suga-T) does not appear in the song title, primary artist or featured artist. It also takes out songs with certain recurring problematic phrases in their metadata, most prominently any non-English translations.

What remains are, ideally (artist, API path) tuples for our target artist. The artist ID is in the API path.


```python
artists = sdp.filter_artists(query_response)
print("\nArtists to search:", artists)
print("\nArtist ID:", list(artists)[0][-1].split("/")[-1])
```

    excluding: query suga-t not in: Star Cast--Ryan Destiny / Brittany O’Grady / Jude Demorest--Suga
    excluding: query suga-t not in: Ben&Ben--Munimuni--Sugat
    excluding: query suga-t not in: The Fatback Band & With You--Sarah Ruba--(Are You Ready) Do the Bus Stop / Suga
    excluding suga-t:  artist Genius Traducciones al Español doesn't match: traducciones
    excluding: query suga-t not in: 須田景凪 (Keina Suda)----風の姿 (Kaze no Sugata/The Appearance Of The Wind)
    excluding: query suga-t not in: ナナヲアカリ (Nanawoakari)----一生奇跡に縋ってろ (Isshou Kiseki Ni Sugattero)
    excluding: query suga-t not in: Genius Romanizations----須田景凪 (Keina Suda) - 風の姿 (Kaze no Sugata) (Romanized)
    excluding suga-t:  artist Genius English Translations doesn't match: genius english translations
    
    Artists to search: {('Suga-T', '/artists/5681')}
    
    Artist ID: 5681


### 4. Refilter with alternate names <a name="4"></a>
<a href="#index">Top</a>

Now that we have the artist ID, we can query the artist endpoint to get songs by the target artist.


```python
artist_id = next(a for a in artists)[1]

songs_json = sdp.songs_query(artist_id, 1)

for n, s in enumerate(songs_json['songs'][:10]):
    print(f'{s["artist_names"]} - "{s["title"]}"')
```

    Suga-T - "Billy Bad Ass"
    E-40 & B-Legit (Ft. The Click) - "Blame It"
    E-40 - "Bootsee"
    Mia X (Ft. Suga-T) - "Can’t Trust A Man"
    Mia X (Ft. Suga-T) - "Can’t Trust No Man"
    E-40 (Ft. The Click) - "Captain Save A Hoe"
    E-40 (Ft. The Click) - "Captain Save a Hoe (Remix)"
    Pimp C (Ft. Mannie Fresh & Suga-T) - "Cheat on Yo Man"
    UGK - "Choppin’ Blades"
    E-40 (Ft. Bosko, The Click & Harm) - "Click About It"


Notice that Suga-T is the main artist on only one of these songs. She shows up in 4 of the tracks as a member of The Click, and as a feature on another 3. Genius's API is sophisticated enough to return songs featuring the target artist and songs where the target artist does not appear by name.

The API also return songs that involve the target artist in more tangential ways, which need to be removed. Suga-T does not rap on "Bootsee" or "Choppin' Blades". She contributes backing vocals to "Bootsee" and is credited accordingly, but doesn't actually rap. The beat and hook for "Choppin' Blades" credits Suga-T because its beat and hook are interpolations of The Click's "Captain Save A Hoe", but she does not appear on the song.

To handle these considerations, the code contains an additional filter for songs that do not explicitly feature lyrics from the target artist, and takes an "alts" parameter in the original query to allow other names through the filters. 


```python
sdp.intake_query({"query": "suga-t", "alts": ["the click"]}) # including "alts"

songs_json = sdp.songs_query(next(a for a in artists)[1], 1)

songs = [] # collect results here
for n, s in enumerate(songs_json['songs'][:10]):
    song_data_temp = sdp.extract_song_data(s)
    include = sdp.exclusion_filter(song_data_temp) # filtering step
    if include:
        songs.append(s)
print('')
for s in songs:        
    print(f'{s["artist_names"]} - "{s["title"]}"')
```

    excluding: query suga-t not in: E-40----Bootsee
    excluding: query suga-t not in: UGK----Choppin’ Blades
    
    Suga-T - "Billy Bad Ass"
    E-40 & B-Legit (Ft. The Click) - "Blame It"
    Mia X (Ft. Suga-T) - "Can’t Trust A Man"
    Mia X (Ft. Suga-T) - "Can’t Trust No Man"
    E-40 (Ft. The Click) - "Captain Save A Hoe"
    E-40 (Ft. The Click) - "Captain Save a Hoe (Remix)"
    Pimp C (Ft. Mannie Fresh & Suga-T) - "Cheat on Yo Man"
    E-40 (Ft. Bosko, The Click & Harm) - "Click About It"


(You can see the limitations of crowdsourced data here, as ["Can't Trust No Man"](https://genius.com/Mia-x-cant-trust-no-man-lyrics) and ["Can't Trust A Man"](https://genius.com/Mia-x-cant-trust-a-man-lyrics) are actually the same song. However, given the size of the data set, it makes more sense to consider duplications in the entire data set than to worry about them at this point.)

### 5. Dates <a name="5"></a>
<a href="#index">Top</a>

There are three date fields in the API response, and any or none of them may be present. The code contains logic to decide which field to use and how to extract the date.

You can see the some of the possible variation in date fields in the data below.


```python
date_df = pd.DataFrame(
    [{
        k:s.get(k) for k in [
            'artist_names', 
            'title', 
            'release_date', 
            'release_date_components', 
            'release_date_for_display'
        ]
    } for s in songs_json['songs'][10:17]]
)

date_df
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>artist_names</th>
      <th>title</th>
      <th>release_date</th>
      <th>release_date_components</th>
      <th>release_date_for_display</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>E-40 (Ft. Busta Rhymes)</td>
      <td>Do It To Me</td>
      <td>None</td>
      <td>{'year': 1998, 'month': 8, 'day': 11}</td>
      <td>August 11, 1998</td>
    </tr>
    <tr>
      <th>1</th>
      <td>E-40</td>
      <td>Duckin’ &amp; Dodgin’</td>
      <td>None</td>
      <td>{'year': 1999, 'month': 11, 'day': 9}</td>
      <td>November 9, 1999</td>
    </tr>
    <tr>
      <th>2</th>
      <td>E-40 (Ft. 2Pac, Mac Mall &amp; Spice 1)</td>
      <td>Dusted ‘n’ Disgusted</td>
      <td>None</td>
      <td>{'year': 1995, 'month': 3, 'day': 14}</td>
      <td>March 14, 1995</td>
    </tr>
    <tr>
      <th>3</th>
      <td>The Click</td>
      <td>Family</td>
      <td>None</td>
      <td>{'year': 2001, 'month': 9, 'day': 25}</td>
      <td>September 25, 2001</td>
    </tr>
    <tr>
      <th>4</th>
      <td>E-40 (Ft. Suga-T)</td>
      <td>Fed</td>
      <td>None</td>
      <td>{'year': 1995, 'month': 3, 'day': 14}</td>
      <td>March 14, 1995</td>
    </tr>
    <tr>
      <th>5</th>
      <td>E-40 (Ft. The Click)</td>
      <td>Fuckin’ They Nose</td>
      <td>None</td>
      <td>{'year': 1999, 'month': 11, 'day': 9}</td>
      <td>November 9, 1999</td>
    </tr>
    <tr>
      <th>6</th>
      <td>E-40 (Ft. Suga-T)</td>
      <td>Ghetto Celebrity</td>
      <td>None</td>
      <td>{'year': 1999, 'month': 11, 'day': 9}</td>
      <td>November 9, 1999</td>
    </tr>
  </tbody>
</table>
</div>



### 6. Output <a name="6"></a>
<a href="#index">Top</a>

The end result is a CSV file with relevant data for songs for each artist, including the URL for the lyrics to each song.


```python
suga_t_df = pd.read_csv("./lyrics/suga-t/suga-t_data.csv", header=None)[[r for r in range(5)]]
suga_t_df.columns = ['title', 'artist', 'features', 'date', 'url']
suga_t_df.head(10)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>title</th>
      <th>artist</th>
      <th>features</th>
      <th>date</th>
      <th>url</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Billy Bad Ass</td>
      <td>Suga-T</td>
      <td>NaN</td>
      <td>NO DATE</td>
      <td>https://genius.com/Suga-t-billy-bad-ass-lyrics</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Blame It</td>
      <td>E-40 &amp; B-Legit</td>
      <td>The Click</td>
      <td>2018-4-6</td>
      <td>https://genius.com/E-40-and-b-legit-blame-it-l...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Can’t Trust A Man</td>
      <td>Mia X</td>
      <td>Suga-T</td>
      <td>NO DATE</td>
      <td>https://genius.com/Mia-x-cant-trust-a-man-lyrics</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Can’t Trust No Man</td>
      <td>Mia X</td>
      <td>Suga-T</td>
      <td>NO DATE</td>
      <td>https://genius.com/Mia-x-cant-trust-no-man-lyrics</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Captain Save A Hoe</td>
      <td>E-40</td>
      <td>The Click</td>
      <td>1993-9-28</td>
      <td>https://genius.com/E-40-captain-save-a-hoe-lyrics</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Captain Save a Hoe (Remix)</td>
      <td>E-40</td>
      <td>The Click</td>
      <td>1993-9-23</td>
      <td>https://genius.com/E-40-captain-save-a-hoe-rem...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Cheat on Yo Man</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>NO DATE</td>
      <td>https://genius.com/Pimp-c-cheat-on-yo-man-lyrics</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Click About It</td>
      <td>E-40</td>
      <td>Bosko / Harm / The Click</td>
      <td>2011-3-29</td>
      <td>https://genius.com/E-40-click-about-it-lyrics</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Family</td>
      <td>The Click</td>
      <td>NaN</td>
      <td>2001-9-25</td>
      <td>https://genius.com/The-click-family-lyrics</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Fed</td>
      <td>E-40</td>
      <td>Suga-T</td>
      <td>1995-3-14</td>
      <td>https://genius.com/E-40-fed-lyrics</td>
    </tr>
  </tbody>
</table>
</div>



### 7. Lyrics <a name="7"></a>
<a href="#index">Top</a>

The Genius API has no special endpoint for lyrics, presumably because the lyrics are all available on the web through plain HTTP queries. However, despite observing standard best practices to avoid rate-limiting, Cloudflare (Genius's hosting service) did not like the volume of lyrics queries and began giving me 503 errors.

I tried several approaches to evade Cloudflare. I replaced Requestes with [Cloudscraper](https://pypi.org/project/cloudscraper/), added [Fake Useragent](https://pypi.org/project/fake-useragent/) to create random user agents for each query, and even considered brute force scraping using Selenium and [undetected chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver). (What finally worked was a specific combination of user agent parameters and the use of an [ordered dictionary](https://realpython.com/python-ordereddict/) for the Request header.)

The code takes a CSV file as returned in the first phase of the scrape and gets the lyrics for all the listed songs using the provided address.


```python
lp = LyricsPuller("suga-t")
lp.load_df() # load song data

for r in lp.df.loc[0:2,:].iterrows():
    lp.process_entry(r)
```

    0 Suga-T Billy Bad Ass https://genius.com/Suga-t-billy-bad-ass-lyrics
    1 E-40 & B-Legit Blame It https://genius.com/E-40-and-b-legit-blame-it-lyrics
    2 Mia X Can’t Trust A Man https://genius.com/Mia-x-cant-trust-a-man-lyrics


The code also adds a header with relevant metadata to each file.


```python
print("\nAn example of the metadata header...\n")
with open("./lyrics/suga-t/Suga-T-Billy Bad Ass.txt") as f:
    print(f.read()[:114]) 
```

    
    An example of the metadata header...
    
    SONG TITLE: Billy Bad Ass
    RELEASE DATE: NO DATE
    PRIMARY ARTIST: Suga-T
    FEATURED ARTISTS: nan
    SONG ID: 59441
    ======


### 8. Verses <a name="8"></a>
<a href="#index">Top</a>

To maximize the data, I broke every song down into its constituent verses. This allowed me to extract and appropriately gender collaborations between male and female artists, and to label verse types (chorus, bridge, outro, etc), for further downstream analysis.

Additionally, I am expecting to use a modeling framework which has a maximum sentence length of 512 tokens. Anything past that will be truncated and ignored as actual training data. Breaking songs into verses mostly solves this problem with a strategy that is informed by the actual context of the data.

We will look at this process using Pimp C, Suga-T and Mannie Fresh's ["Cheat On Yo Man"](https://www.youtube.com/watch?v=LvzJJiOLprg&ab_channel=626bigSGV) from Pimp C's 2006 album _The Pimpilation_.


```python
file_ = 'Pimp C-Cheat on Yo Man.txt'
artist = 'suga-t'

sfp = SongFileProcessor(artist)
text_ = open("./lyrics/suga-t/Pimp C-Cheat on Yo Man.txt").read()

# these steps are automated deeper in the code, but done manually here for demonstration
text_ = sfp.preprocess_text(text_)
song_info = text_.split("======")[0]
song_lyrics = text_.split("======")[1]
verses = re.split(r"\n\n", song_lyrics)
```

First we fix some recurring quirks in the data with a preprocessing step, then we split off the song info and split the lyrics into verses on double line-breaks. 

This is not a perfect approach to parsing out verses, but any song that is not split remains in the data as one long verse by the song's artist (which is fine for our purposes). 


```python
print(song_info)
print("number of verses:", len(verses), "\n")
print("first verse:\n", verses[1])
```

    SONG TITLE: Cheat on Yo Man
    RELEASE DATE: NO DATE
    PRIMARY ARTIST: Pimp C
    FEATURED ARTISTS: Suga-T / Mannie Fresh
    SONG ID: 761361
    
    number of verses: 6 
    
    first verse:
     \[Hook: Mannie Fresh]
    If you wanna get ahead baby
    Stick to the plan, if you wanna get ahead baby, cheat on yo man
    If you wanna get ahead baby
    Stick to the plan, if you wanna get ahead, hey, i'll show you


Genius lyrics are neither clean nor standardized. However, its contributors do follow loose annotation conventions, in which sections of songs are demarcated with "headers" consisting of the section type ("verse", "chorus", "bridge" etc) and sometimes the artist, in brackets or parentheses. 

While these headers are inconsistent, they were sufficiently robust for me to build a Named Entity Recognition model with [SpaCy](https://spacy.io/api/entityrecognizer/) from a sample of lyrics. This allowed me to efficiently label verses with their type and artist.

The model accurately identifies all the parts of our song. ("Hook Verse" is a verse preceded by an implied hook. This will be fixed later.)


```python
for v in verses[1:]:
    print(sfp.process_header(sfp.extract_header(v)))
```

    ('Hook', 'Mannie Fresh')
    ('Verse', 'Pimp C')
    ('Hook Verse', 'Suga')
    ('Hook Verse', 'Mannie Fresh')
    ('Hook x4', None)


Here is all the data parsed out of "Cheat on Yo Man".


```python
suga_t_verses_df = pd.read_csv("./lyrics/suga-t/suga-t_verses.csv")
suga_t_verses_df.query("song_title=='Cheat on Yo Man'")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>song_title</th>
      <th>release_date</th>
      <th>song_artist</th>
      <th>features</th>
      <th>song_id</th>
      <th>verse_text</th>
      <th>verse_index</th>
      <th>verse_header</th>
      <th>verse_type</th>
      <th>verse_artist</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>4</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>NaN</td>
      <td>0</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NO HEADER</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>If you wanna get ahead baby\nStick to the plan...</td>
      <td>1</td>
      <td>Hook: Mannie Fresh</td>
      <td>Hook</td>
      <td>Mannie Fresh</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>I ain't really tryin to break you and yo nigga...</td>
      <td>2</td>
      <td>Verse 1: Pimp C</td>
      <td>Verse</td>
      <td>Pimp C</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>Now i dont really care what you talkin about, ...</td>
      <td>3</td>
      <td>Hook Verse 2: Suga</td>
      <td>Hook Verse</td>
      <td>Suga</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>Love ain't nothin but a four letter word, got ...</td>
      <td>4</td>
      <td>Hook Verse 3: Mannie Fresh</td>
      <td>Hook Verse</td>
      <td>Mannie Fresh</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361</td>
      <td>\</td>
      <td>5</td>
      <td>Hook x4</td>
      <td>Hook x4</td>
      <td>Pimp C</td>
    </tr>
  </tbody>
</table>
</div>



### 9. Additional cleaning and standardization <a name="9"></a>
<a href="#index">Top</a>

Cleaning and standardization steps to correct some recurring issues in the data (some of which are visible above):

* Use the song artist as the verse artist if the verse artist is missing
* Remove "produced by" from any verse artists
* Correct for hyphenation (change verse type like "pre chorus" to "pre-chorus")
* Correct basic typos by comparing ordered letters in verse types (ie "chrous" has the same letters as "chorus")
* Replace "hook" with "chorus" (these are functionally interchangable)
* Replace "chorus verse" with "verse" (this is usually a verse which follows an implied chorus)
* Filter out any verse with < 10 characters


```python
# all_verses = pd.read_csv('cleaning_project_data.csv')
```


```python
def standardize_verse_type(v):
    v = re.sub(r"\sx?[\d\(]", "", v).replace("pre ", "pre-").replace("post ", "post-")
    v = v.replace("hook", "chorus").replace("chorus verse", "verse")
    
    def simpler(s):
        return "".join(sorted([l for l in s.strip()]))
    
    for v_ in ['chorus', 'hook', 'intro', 'verse', 'bridge', 'outro', 'refrain']:
        if simpler(v_) == simpler(v):
            return v_
    return v

def filter_verse_artist(r):
    v = r['verse_artist'].lower()
    if v == 'no header':
        return r['song_artist']
    
    elif r['song_artist'].lower() != v and r['song_artist'].lower() in v:
        return r['song_artist']
    
    elif v.startswith('produced by'):
        return r['song_artist']
    
    else:
        return v

def filter_data(df):
    return df.query("~verse_text.isnull()").query(
        "gender.isin(['m', 'f', 'Male', 'Female'])"
    ).query("verse_text.str.len() > 10")
```


```python
all_verses['verse_artist'] = all_verses.apply(filter_verse_artist, 1)
all_verses['verse_type'] = all_verses['verse_type'].str.lower().fillna("null").map(standardize_verse_type)
```

### 10. Add metrics <a name="10"></a>
<a href="#index">Top</a>

Finally, we add some basic metrics about each verse to inform downstream cleaning and optimization.

As previously mentioned, the modeling framework only accomidates inputs of a maximum of 512 tokens. We need to adjust token metrics accordingly.

We also add the gender of each artist -- our target variable! -- using previously compiled data.


```python
all_verses['verse_len'] = all_verses['verse_text'].fillna("").str.len()
all_verses['token_len'] = all_verses['verse_text'].fillna("").map(lambda v: len(v.split()[:512]))
all_verses['unique_token_len'] = all_verses['verse_text'].fillna("").map(lambda v: len(set(v.split()[:512])))
all_verses['unique_token_pct'] = all_verses['unique_token_len']/all_verses['token_len']
```


```python
gender_key_df = pd.read_csv('gender_key.csv')
gender_key_df.columns = ['verse_artist', 'gender']
gender_key_df['gender'] = gender_key_df['gender'].str.lower()

gender_dict = dict(zip(gender_key_df.verse_artist, gender_key_df.gender))
all_verses['gender'] = all_verses[
    'verse_artist'].str.lower().map(gender_dict).replace({"m": "Male", "f": "Female"}).str.title()
```


```python
df = filter_data(all_verses)
```

Here is the final, cleaned data for "Cheat on Yo Man".


```python
df.query("song_title=='Cheat on Yo Man'")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>song_title</th>
      <th>release_date</th>
      <th>song_artist</th>
      <th>features</th>
      <th>song_id</th>
      <th>verse_text</th>
      <th>verse_index</th>
      <th>verse_header</th>
      <th>verse_type</th>
      <th>verse_artist</th>
      <th>verse_len</th>
      <th>token_len</th>
      <th>unique_token_len</th>
      <th>unique_token_pct</th>
      <th>gender</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>369185</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361.0</td>
      <td>If you wanna get ahead baby\nStick to the plan...</td>
      <td>1</td>
      <td>Hook: Mannie Fresh</td>
      <td>chorus</td>
      <td>mannie fresh</td>
      <td>181</td>
      <td>39</td>
      <td>20</td>
      <td>0.512821</td>
      <td>Male</td>
    </tr>
    <tr>
      <th>369186</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361.0</td>
      <td>I ain't really tryin to break you and yo nigga...</td>
      <td>2</td>
      <td>Verse 1: Pimp C</td>
      <td>verse</td>
      <td>pimp c</td>
      <td>786</td>
      <td>161</td>
      <td>116</td>
      <td>0.720497</td>
      <td>Male</td>
    </tr>
    <tr>
      <th>369187</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361.0</td>
      <td>Now i dont really care what you talkin about, ...</td>
      <td>3</td>
      <td>Hook Verse 2: Suga</td>
      <td>verse</td>
      <td>suga</td>
      <td>737</td>
      <td>159</td>
      <td>93</td>
      <td>0.584906</td>
      <td>Female</td>
    </tr>
    <tr>
      <th>369188</th>
      <td>Cheat on Yo Man</td>
      <td>NO DATE</td>
      <td>Pimp C</td>
      <td>Suga-T / Mannie Fresh</td>
      <td>761361.0</td>
      <td>Love ain't nothin but a four letter word, got ...</td>
      <td>4</td>
      <td>Hook Verse 3: Mannie Fresh</td>
      <td>verse</td>
      <td>mannie fresh</td>
      <td>755</td>
      <td>150</td>
      <td>107</td>
      <td>0.713333</td>
      <td>Male</td>
    </tr>
  </tbody>
</table>
</div>


