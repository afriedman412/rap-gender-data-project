import requests
import cloudscraper
import pandas as pd
from collections import OrderedDict
from bs4 import BeautifulSoup
import regex as re
import time
from datetime import datetime as dt
import os
import spacy
from CONFIG import genius_token

model = spacy.load("./verse_header_model/")

class SongDataPuller:
    """
    Queries the Genius API and creates a CSV of song data for the queried artist.
    """
    def __init__(self):
        """
        Instantiates a text log path, the cloudscraper object, an empty data bucket path to collect results, and a list of excluded terms for filtering.
        """
        t = dt.strftime(dt.now(), "%Y%m%d%H%M")
        self.loggy = f"logger_{t}.txt"
        self.scraper = cloudscraper.create_scraper()
        self.data_bucket_path = None

        self.exclude = [
                'Traduction', 'ChopNotSlop Remix', '(Instrumental)', 'Chopped & Screwed'
                '(Skit)', '(Acapella)', "a capella", 'Interview', '[Script]', "(Interlude)",
                'Originally Performed By',
                "Genius Russian Translations", "Traducciones", "Traductions Françaises",
                "Genius Traductions Françaises", "Genius Türkçe Çeviri",
                "Traduções", "Fresh Finds", "(Commentary)", "Genius 中文翻譯", "Genius Türkçe Çeviri",
                "Genius Srpski Prevodi", "Genius Swedish Translations",
                "Genius Farsi Translations", "Polskie tłumaczenia", "Genius Deutsche Übersetzungen",
                "Genius English Translations", "Outside the Lines With Rap Genius", "[Album Art]",
            ]

        self.exclude = [e.lower() for e in self.exclude]

    def intake_query(self, query_entry):
        """
        Formats the query_entry to allow for flexible searching.

        Accounts for genius id, multiple artist names and the exclusion of problematic results.
        """
        self.query = query_entry.get("query", None) 
        self.artist = query_entry.get("artist") or query_entry.get("query", None)
        self.rg_id = query_entry.get("rg_id", None)
        self.artist_names = query_entry.get("alts", []) + [self.artist]
        self.artist_names = [a.lower() for a in self.artist_names]
        self.artist_excludes = query_entry.get("excludes", [])
        self.artist_excludes = [a.lower() for a in self.artist_excludes]

    def pull_all_song_data(self, query_entry, dir_=None):
        """
        Highest order function for querying.
        """
        self.intake_query(query_entry)
        if not dir_:
            dir_ = "_".join(self.artist.split())

        self.dir_ = dir_.lower()

        print("**** starting:", self.query, dir_)

        if not os.path.exists(f"./{self.dir_}"):
            os.mkdir(f"./{self.dir_}")

        self.data_bucket_path = os.path.join(f"./{self.dir_}", f"{self.dir_}_data.csv")

        self.make_headers()
        if self.rg_id:
            artists = [(self.artist, f"/artists/{str(self.rg_id)}")]
        else:
            query_response = self.query_search(self.query)
            artists = self.filter_artists(query_response)
        for a in artists:
            print(f"========{self.query} ... next artist:", a[0])
            page=1
            self.data_bucket = []
            while page:
                songs_json = self.songs_query(a[1],page)
                page = songs_json.get("next_page")
                for n, song in enumerate(songs_json['songs']):
                    self.load_song(song)
                    if not n % 10:
                        pd.DataFrame(
                            self.data_bucket).to_csv(
                            self.data_bucket_path, mode="a", header=False, index=False)
                        self.data_bucket = []
                        time.sleep(1)
            if self.data_bucket: # writes remaining song data if not % 10
                pd.DataFrame(
                    self.data_bucket).to_csv(
                    self.data_bucket_path, mode="a", header=False, index=False)
        print(f'****{self.query} done')
        with open(self.loggy, "a+") as f:
                f.write(f'****{self.query} done\n')

    def make_headers(self):
        """
        Formats API token for use in queries.

        This is its own function (rather than something done once on instantiation) because previous scrapes involved further manipulation of the headers.
        """
        token = 'Bearer {}'.format(genius_token)
        self.headers = {'Authorization': token}

    def query_search(self, query):
        """
        Queries the search endpoint of the API.
        """
        params={"q":query}
        r = self.scraper.get("https://api.genius.com/search/", headers=self.headers, params=params)
        time.sleep(2)
        return r.json()['response']['hits']

    def songs_query(self, api_path, page=1):
        """
        Queries the songs endpoint of the API, with pagination.
        """
        url = "https://api.genius.com" + api_path + "/songs"
        r = self.scraper.get(url, headers=self.headers, params={"page":page, "per_page":50})
        time.sleep(2)
        return r.json()['response']

    def extract_song_data(self, song_json):
        """
        Formats the query response for a song into song_data.
        """
        song_data = {
            'title': song_json.get('title') or "",
            'artist':  song_json['primary_artist'].get("name") or "",
            'features': " / ".join([a['name'] for a in song_json.get('featured_artists') or ""]),
            'release_date': self.extract_date(song_json),
            'lyrics_url': song_json.get('url') or "",
            'api_path': song_json['primary_artist'].get('api_path') or "", 
            'query': self.query.title()
            }

        song_data['data_title'] = "-".join([song_data[k] for k in ['query', 'artist', 'title']])
        return song_data

    def load_song(self, song_json):
        """
        Extracts, filters, logs and saves song_data from a song query response.
        """
        song_data = self.extract_song_data(song_json)
        if not self.exclusion_filter(song_data):
            with open(self.loggy, "a+") as f:
                f.write(f"{song_data['data_title']}: excluded\n")
            return

        with open(self.loggy, "a+") as f:
            f.write(song_data['data_title'] + "\n")
        
        print(song_data['data_title'])
        song_data.pop('api_path')
        self.data_bucket.append(song_data)

    def filter_artists(self, query_response):
        """
        Filters search API results and returns unique, relevant artists.
        """
        artists=[]
        for a in query_response:
            song_data = self.extract_song_data(a['result'])
            if self.exclusion_filter(song_data):
                artists.append((
                        song_data['artist'],
                        song_data['api_path'] 
                        ))
        return set(artists)

    def extract_date(self, song_json):
        """
        Extracts date from date_json, based on which date variables are present.
        """
        if song_json.get('relase_date'):
            return song_json['release_date']

        elif song_json.get("release_date_components"):
            j = song_json['release_date_components']
            return "-".join([str(j.get(k) or "00") for k in ['year', 'month', 'day']])

        elif song_json.get("release_date_for_display"):
            return dt.strptime(song_json['release_date_for_display'], "%B %d, %Y").strftime("%Y-%m-%d")

        else:
            return "NO DATE"

    def exclusion_filter(self, song_data):
        """
        Filters out songs with excluded strings (from instantiation) in song_data.

        Filters out songs without relevant artists, accounting for alternate names and intentionally excluded strings.
        """
        for e in self.exclude:
            for k in ['title', 'artist', 'features']:
                if e in song_data[k].lower():
                    print(f"excluding {self.query}:  {k} {song_data[k]} doesn't match: {e}")
                    return False

        song_artists_set = set(
                song_data['artist'].lower().split(" & ") + [f.lower() for f in song_data['features'].split(" / ")]
            )
        artist_included = set(self.artist_names).intersection(song_artists_set)
        artist_excluded = set(self.artist_excludes).intersection(song_artists_set)
        artist_overlaps = [s for s in self.artist_names for s_ in song_artists_set if s in s_]

        if not artist_included and not artist_overlaps or artist_excluded:
            e = "--".join([song_data['artist'], song_data['features'], song_data['title']])
            print(f"excluding: query {self.query} not in: {e}")
            return False

        else:
            return True


class LyricsPuller:
    """
    Scrapes lyrics from Genius website for a given artist, saving the lyrics for each song to a text file.
    """
    def __init__(self, artist, base_path="./lyrics"):
        """
        Sets artist and path for saving lyrics, and initiates a requests session to persist throughout the scrape.
        """
        self.artist = artist
        self.initiate_session()
        self.base_path = base_path

    def process_entry(self, row):
        print(row[0], row[1]['artist'], row[1]['title'], row[1]['url'])
        r = self.s.get(row[1]['url'])
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'lxml')
            song_id = soup.find("meta", attrs={"property": "twitter:app:url:iphone"})['content'].split('/')[-1]
            lyrics=soup.find("div", attrs={"data-lyrics-container":"true"})
            if lyrics:
                lyrics = lyrics.get_text(strip=True, separator='\n')
                lyrics = re.sub(r"(\[.+)\n(.+\])", r"\1" + r" \2", lyrics)
                lyrics = re.sub(r"\n,\n", r",\n", lyrics)
                lyrics_header = "\n".join([f"{k}: {row[1][k_]}" for k,k_ in zip(
                    ['SONG TITLE', 'RELEASE DATE', 'PRIMARY ARTIST', 'FEATURED ARTISTS'],
                    ['title', 'release_date', 'artist', 'features']
                    )])
                lyrics_header += f"\nSONG ID: {song_id}"
                lyrics = "\n======\n".join([lyrics_header, lyrics])
                with open(f"./lyrics/{self.artist}/{row[1]['file_name']}", "w+") as f:
                    f.write(lyrics)
        if not row[0] % 10:
            time.sleep(2)

    def initiate_session(self):
        self.s = requests.Session()
        headers = OrderedDict({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
        })

        self.s.headers = headers

    def load_df(self):
        df = pd.read_csv(f'{self.base_path}/{self.artist}/{self.artist}_data.csv', header=None)
        if len(df.columns) == 8:
            df = df.loc[:,1:]
        df.columns = ["title", 'artist', 'features', 'release_date', 'url', 'query', 'data_title']
        df['file_name'] = df[["artist", "title"]].agg('-'.join, axis=1).map(lambda t: t.replace("/", ".") + ".txt")
        self.df = df

    def process_df(self):
        for row in self.df.iterrows():
            self.process_entry(row)

class SongFileProcessor:
    def __init__(self, artist, model=model, base_path="./lyrics"):
        self.artist = artist
        self.base_path = base_path
        self.model = model
        self.verse_dfs = []
        return

    def process_all_files(self):
        for file_ in os.listdir(os.path.join(self.base_path, self.artist)):
            if file_[-3:] == 'txt':
                self.process_one_file(file_)
            else:
                continue
        verses_df = pd.concat(self.verse_dfs)
        verses_df.to_csv(os.path.join(self.base_path, self.artist, f"{self.artist}_verses.csv"), index=False)

    def process_one_file(self, file_):
        self.process_song(file_)
        df = self.make_output_df()
        self.verse_dfs.append(df)
    
    def preprocess_text(self, text_):
        text_ = text_.replace("\n\n(?)", "\n(?)")
        text_ = text_.replace("[?]", "(?)")
        text_ = text_.replace("\[", "[")
        text_ = re.sub(r"\n([\]\)\,])", r"\1", text_)
        text_ = re.sub(r"([\[\(])\n", r"\1", text_)
        text_ = re.sub(r"([\,\&])\n", r" ", text_)
        text_ = re.sub(r"(?<=.)\n\[", "\n\n\[", text_)
        text_ = re.sub("\[", "[", text_)
        text_ = re.sub(r"(\[.+)\n(.+\])", r"\1" + r" \2", text_)
        text_ = re.sub(r"([,&\(\[])\n", r"\1", text_)
        text_ = re.sub(r"\n([,&\)\]])", r"\1", text_)
        return text_
    
    def extract_header(self, verse):
        header_rx = re.search(r"\[.{3,}\]", verse)
        if header_rx:
            return re.sub(r"[\[\]]", "", verse[header_rx.start():header_rx.end()])
        else:
            return
        
    def extract_ents(self, doc, classes=None):
        if classes:
            return [(d.text, d.label_, d.start, d.end) for d in doc.ents if d.label_ in classes]
        else:
            return [(d.text, d.label_, d.start, d.end) for d in doc.ents]
        
    def process_song_info(self, song_info):
        return dict(zip(
            ['song_title', 'release_date', 'song_artist', 'features', 'song_id'],
            [h.split(": ")[1] for h in song_info.split("\n") if h]
        ))

    def process_header(self, verse_header):
        ents = self.extract_ents(self.model(verse_header))
        verse_type = " ".join([e[0].replace(":", "") for e in ents if e[1]=="VERSE_TYPE"])
        verse_artist = next((e[0] for e in ents if e[1]=="ARTIST"), "")
        if verse_artist.startswith("produced by") or len(verse_artist) < 2:
            verse_artist = None
        return verse_type, verse_artist
    
    def process_song(self, file_):
        self.verse_dicts = []
        self.text_ = open(os.path.join(self.base_path, self.artist, file_)).read()
        text_ = self.preprocess_text(self.text_)
        song_info = text_.split("======")[0]
        song_lyrics = text_.split("======")[1]
        verses = re.split(r"\n\n", song_lyrics)
        
        for n, v in enumerate(verses):
            dicto = self.process_song_info(song_info)
            dicto['verse_text'] = re.sub(r"\[.{3,}\]", "", v)
            dicto['verse_index'] = n
            dicto['verse_header'] = self.extract_header(v)
            self.verse_dicts.append(dicto)
            
    def verse_dicts_to_df(self):
        return pd.DataFrame(self.verse_dicts)
        
    def make_header_df(self, verses_df):
        header_df = pd.DataFrame(
            verses_df['verse_header'].fillna("NO HEADER").map(self.process_header).to_list(),
            columns=['verse_type', 'verse_artist']
        )
        return header_df
    
    def make_output_df(self):
        verses_df = self.verse_dicts_to_df()
        if len(verses_df) > 0:
            header_df = self.make_header_df(verses_df)
            df = pd.concat([verses_df, header_df], axis=1)
            df['verse_artist'].fillna(df['song_artist'], inplace=True)
            df = df.query("verse_text != 'NO LYRICS'")
            for r in [r"^\n", r"^\\\n"]:
                df['verse_text'] = df['verse_text'].map(lambda v: re.sub(r, "", v))
            return df
        else:
            return pd.DataFrame()