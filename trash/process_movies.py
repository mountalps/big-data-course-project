import json

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import udf

# The serial number of each genre
genresDic = {'Mystery': 14, 'Romance': 8, 'History': 15, 'Family': 6, 'Fantasy': 10, 'Horror': 16, 'Crime': 0,
             'Drama': 7, 'Science Fiction': 4, 'Animation': 5, 'Music': 9, 'Adventure': 2, 'Foreign': 18, 'Action': 3,
             'Comedy': 1, 'Documentary': 17, 'War': 12, 'Thriller': 11, 'Western': 13}
# The serial number of each language
languageDic = {'en': 0, 'zh': 3, 'cn': 17, 'af': 9, 'vi': 20, 'is': 25, 'it': 6, 'xx': 22, 'id': 23, 'es': 2, 'ru': 12,
               'nl': 16, 'pt': 7, 'no': 18, 'nb': 21, 'th': 15, 'ro': 11, 'pl': 24, 'fr': 5, 'de': 1, 'da': 10,
               'fa': 19, 'hi': 13, 'ja': 4, 'he': 14, 'te': 26, 'ko': 8}


# generate a standard id
def get_id(movie_id):
    return "%08d" % int(movie_id)


# Get the year of a date
# 2018-12-2 -> 2018
def get_year(date):
    return int(date.split("-")[0])


# transfer the language of the movie to an array
# for example:
# before: en
# after: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def get_language(language):
    language_array = [0] * len(languageDic)
    language_id = languageDic[language]
    language_array[language_id] = 1
    return language_array


# transfer the genre of the movie to an array
# for example:
# before: [{"id": 80, "name": "Crime"}, {"id": 35, "name": "Comedy"}]
# after: [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def get_genres(genres):
    genres_json = json.loads(genres)
    genres_array = [0] * len(genresDic)
    for genre in genres_json:
        genre_id = genresDic[genre['name']]
        genres_array[genre_id] = 1
    return genres_array


get_id_udf = udf(get_id, StringType())
get_year__udf = udf(get_year, StringType())
get_language_udf = udf(get_language, StringType())
get_genres_udf = udf(get_genres, StringType())


def get_casts(casts):
    casts_json = json.loads(casts)
    castids = []
    for cast in casts_json:
        castid = cast[['cast_id']]
        castids.append(castid)
    return castids

get_casts_udf = udf(get_casts, StringType())


if __name__ == '__main__':
    spark = SparkSession.builder.appName("project").getOrCreate()

    # Get all attributes we need from the original csv file
    # This uses local file
    # movieDataRaw1 = spark.read.format("csv").option("header", "true").option("inferSchema", "true").option('quote',
    #                                                                                                        '"').option(
    #     'escape', '"').load(
    #     "file:///Users/wesley/codes/bigdata/finalProject/big-data-course-project/data/tmdb_5000_movies.csv").select(
    #     "id", "original_language", "revenue", "title", "budget", "release_date", "genres")

    # Get all attributes we need from the original csv file
    # This uses file in hadoop in order to make it scalable
    movieDataRaw1 = spark.read.format("csv").option("header", "true").option("inferSchema", "true").option('quote',
                                                                                                           '"').option(
        'escape', '"').load(
        "/finalProjectData/tmdb_5000_movies.csv").select(
        "id", "original_language", "revenue", "title", "budget", "release_date", "genres")

    # Transfer each attribute to standard format
    movieDataRaw2 = movieDataRaw1.withColumn('mid', get_id_udf(movieDataRaw1['id']))
    movieDataRaw2 = movieDataRaw2.withColumn('mlanguage', get_language_udf(movieDataRaw2['original_language']))
    movieDataRaw2 = movieDataRaw2.withColumn('myear', get_year__udf(movieDataRaw2['release_date']))
    movieDataRaw2 = movieDataRaw2.withColumn('mgenres', get_genres_udf(movieDataRaw2['genres']))

    movieData = movieDataRaw2.select('mid', 'mlanguage', 'revenue', 'title', 'budget', 'myear', 'mgenres')
    movieData.show()

    castDataRaw1 = spark.read.format("csv").option("header", "true").option("inferSchema", "true").option('quote',
                                                                                                          '"').option(
        'escape', '"').load(
        "file:///Users/wesley/codes/RBDA_Project/Data/tmdb_5000_credits.csv").select(
        "movie_id", "cast")
    castDataRaw2 = castDataRaw1.withColumn('mid_new', get_id_udf())

    # castDataRaw1.show()

    spark.stop()