import csv
import re
from time import sleep

from bs4 import BeautifulSoup
import requests

# Filler data from https://www.animefillerlist.com/ as of 4/20/22
# Episodes are considered canon if they are not pure filler or mixed filler

# fmt:off
NARUTO_FILLER = {
    26, 97, 101, 102, 103, 104, 105, 106, 136, 137, 138, 139, 140, 143, 144,
    145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
    160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174,
    175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189,
    190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204,
    205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219
    }

NARUTO_MIXED = {
    7, 9, 14, 15, 16, 18, 19, 20, 21, 23, 24, 27, 28, 29, 30, 37, 38, 39, 40,
    41, 43, 44, 45, 46, 47, 49, 52, 53, 54, 55, 56, 57, 58, 59, 60, 63, 66,
    69, 70, 71, 72, 74, 83, 98, 100, 112, 113, 114, 126, 127, 130, 131, 141,
    142, 220
    }

SHIPPUDEN_FILLER = {
    57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 91, 92, 93, 94,
    95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
    111, 144, 145, 146, 147, 148, 149, 150, 151, 170, 171, 176, 177, 178, 179,
    180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194,
    195, 196, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235,
    236, 237, 238, 239, 240, 241, 242, 257, 258, 259, 260, 271, 279, 280, 281,
    284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 303, 304, 305,
    306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320,
    347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361,
    376, 377, 388, 389, 390, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403,
    404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 416, 417, 422, 423, 427,
    428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442,
    443, 444, 445, 446, 447, 448, 449, 450, 464, 465, 466, 467, 468, 480, 481,
    482, 483
    }

SHIPPUDEN_MIXED = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25,
    45, 49, 50, 54, 56, 71, 89, 90, 112, 115, 127, 128, 213, 254, 296, 324,
    327, 328, 330, 331, 338, 346, 362, 385, 386, 415, 419, 426, 451, 452, 453,
    454, 455, 456, 457, 458, 460, 461, 462, 469, 471, 472, 478, 479
    }

BORUTO_FILLER = {
    16, 17, 40, 41, 48, 49, 50, 67, 68, 69, 96, 97, 104, 105, 112, 113, 114,
    115, 116, 117, 118, 119, 138, 139, 140, 152, 153, 154, 156
    }

BORUTO_MIXED = {18, 93, 94, 95, 106, 107, 108, 109, 110, 111, 127, 192}
# fmt:on


def scrape_and_write_narutopedia_to_csvs() -> None:
    """
    Extract data from narutopedia on naruto episodes and
    characters and write each to separate csv files.
    """

    with open("data/naruto_episodes.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "number",
                "title",
                "arc",
                "series",
                "japanese_air_date",
                "english_air_date",
                "filler_status",
                "characters",
            ]
        )

    with open("data/naruto_characters.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "name",
                "sex",
                "birth_month",
                "birth_day",
                "blood_type",
                "astrological_sign",
                "nature_types",
                "affiliations",
            ]
        )

    characters_already_added = set()
    blood_type_regex = re.compile("Blood type")
    affiliation_regex = re.compile("Affiliation")

    ROOT = "https://naruto.fandom.com"
    response = requests.get("https://naruto.fandom.com/wiki/List_of_Animated_Media")
    soup = BeautifulSoup(response.text, "html.parser")

    # Naruto (first table) is original, Shippuden is its sequel, Boruto is Shippuden's sequel
    NARUTO, SHIPPUDEN, BORUTO = soup.select(".table")[:3]
    for series_number, series_soup in enumerate((NARUTO, SHIPPUDEN, BORUTO), start=1):

        for episode_number, episode in enumerate(series_soup.select("a"), start=1):
            episode_name = episode["title"]
            episode_response = requests.get(f"{ROOT}{episode['href']}")
            episode_soup = BeautifulSoup(episode_response.text, "html.parser")
            info_table = episode_soup.select(".portable-infobox")[0]

            arc = ""
            if arc_results := info_table.select("[data-source='arc'] a"):
                arc = arc_results[0]["title"]

            japanese_airdate = info_table.select("[data-source^='japanese'] > div")[
                0
            ].text
            # Some English airings have not come out, so check for existence
            english_airdate = ""
            if english_airdate_results := info_table.select(
                "[data-source^='english'] > div"
            ):
                english_airdate = english_airdate_results[0].text

            if series_number == 1:
                series = "Naruto"
            elif series_number == 2:
                series = "Shippuden"
            elif series_number == 3:
                series = "Boruto"
            else:
                raise ValueError(
                    "series_number must be 1, 2, or 3 for Naruto, Shippuden, or Boruto"
                )

            if series_soup == NARUTO:
                if episode_number in NARUTO_FILLER:
                    filler_status = "Filler"
                elif episode_number in NARUTO_MIXED:
                    filler_status = "Mixed"
                else:
                    filler_status = "Canon"

            elif series_soup == SHIPPUDEN:
                if episode_number in SHIPPUDEN_FILLER:
                    filler_status = "Filler"
                elif episode_number in SHIPPUDEN_MIXED:
                    filler_status = "Mixed"
                else:
                    filler_status = "Canon"

            elif series_soup == BORUTO:
                if episode_number in BORUTO_FILLER:
                    filler_status = "Filler"
                elif episode_number in BORUTO_MIXED:
                    filler_status = "Mixed"
                else:
                    filler_status = "Canon"

            else:
                raise ValueError("series_soup must be NARUTO, SHIPPUDEN, or BORUTO")

            credits_table = episode_soup.select(".wikitable")[0]
            # Get all anchor tags with href pointing to an internal wiki site.
            # This removes unnamed characters who have no wiki & voice actors
            # whose link goes to imdb, leaving only notable Naruto characters.
            episode_characters = []
            for character in credits_table.select("a[href^='/wiki/']"):
                name = character["title"]
                episode_characters.append(name)

                # Get character information
                if name not in characters_already_added:
                    characters_already_added.add(name)
                    sex = ""
                    birth_month = ""
                    birth_day = ""
                    blood_type = ""
                    astrological_sign = ""
                    affiliations = []
                    nature_types = []

                    character_response = requests.get(f"{ROOT}{character['href']}")
                    character_soup = BeautifulSoup(
                        character_response.text, "html.parser"
                    )
                    if info_table := character_soup.select(".infobox"):
                        info_table = info_table[0]
                        if sex_results := info_table.select(
                            "[data-image-name^='Gender']"
                        ):
                            sex = sex_results[0].parent.text.strip() # type:ignore
                        
                        if birthday_results := info_table.select(
                            "[alt^='Astrological']"
                        ):
                            birth_month, birth_day = (
                                birthday_results[0].parent.text.strip().split() # type:ignore
                            )
                            # Slice out file extension of zodiac image name
                            astrological_sign = birthday_results[0]["alt"].split( # type:ignore
                                "Sign "
                            )[1][:-4]
                        if blood_type_results := info_table.find(
                            string=blood_type_regex
                        ):
                            blood_type = blood_type_results.find_next("td").text.strip() # type:ignore
                        if affiliations_html := info_table.find(
                            string=affiliation_regex
                        ):
                            # Get every second match because href tag is duplicated
                            affiliations = [
                                a["title"]
                                for a in affiliations_html.parent.parent.select( # type:ignore
                                    "a[href^='/wiki/']:nth-of-type(2n)"
                                )
                            ]
                        # Get every second match because href tag is duplicated
                        if nature_type_results := info_table.select(
                            "a[href$='_Release']:nth-of-type(2n)"
                        ):
                            nature_types = [
                                nt["title"].replace(" Release", "") # type:ignore
                                for nt in nature_type_results
                            ]
                    character_data = [
                        name,
                        sex,
                        birth_month,
                        birth_day,
                        blood_type,
                        astrological_sign,
                        nature_types,
                        affiliations,
                    ]
                    with open("data/naruto_characters.csv", "a") as file:
                        writer = csv.writer(file)
                        writer.writerow(character_data)

            episode_data = [
                episode_number,
                episode_name,
                arc,
                series,
                japanese_airdate,
                english_airdate,
                filler_status,
                episode_characters,
            ]
            with open("data/naruto_episodes.csv", "a") as file:
                writer = csv.writer(file)
                writer.writerow(episode_data)

        # Space out requests by 1 second
        sleep(1)


if __name__ == "__main__":
    scrape_and_write_narutopedia_to_csvs()
