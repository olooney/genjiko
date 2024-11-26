"""
Utilities for generating, working with, and drawing genji-ko (源氏香),
traditional Japanese patterns representing partitions of sets of five
elements.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import List, Set, Tuple, Iterator, Optional
from pydantic import validate_call
import itertools
import math
import pandas as pd
from math import comb
import importlib.resources as resources

__all__ = [ 
    "GENJIKO_CHARS",
    "ENGLISH_TITLES",
    "GenjikoType",
    "intervals_overlap",
    "validate_genjiko",
    "draw_genjiko",
    "partitions",
    "is_nested_within",
    "optimal_genjiko_for_partition",
    "generate_all_genjiko_patterns",
    "draw_genjiko_grid",
    "parse_genjiko_file",
    "check_dataframe_partitions",
    "load_genjiko",
    "draw_annotated_genjiko_grid",
    "draw_genjiko_font_grid",
    "generate_html_table",
]

# Genjiko character used by genjiko.ttf
GENJIKO_CHARS = "BCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1"

ENGLISH_TITLES = [
    "The Broom Tree",
    "Utsusemi",
    "Yūgao",
    "Young Murasaki",
    "The Saffron Flower",
    "The Festival of Red Leaves",
    "The Flower Feast",
    "Aoi",
    "The Sacred Tree",
    "The Village of Falling Flowers",
    "Exile at Suma",
    "Akashi",
    "The Flood Gauge",
    "The Palace in the Tangled Woods",
    "A Meeting at the Frontier",
    "The Picture Competition",
    "The Wind in the Pine Trees",
    "A Wreath of Cloud",
    "Asagao",
    "The Maiden",
    "Tamakatsura",
    "The First Song of the Year",
    "The Butterflies",
    "The Glow-Worm",
    "A Bed of Carnations",
    "The Flares",
    "The Typhoon",
    "The Royal Visit",
    "Blue Trousers",
    "Makibashira",
    "The Spray of Plum Blossom",
    "Fuji no Uraba",
    "Wakana, Part I",
    "Wakana, Part II",
    "Kashiwagi",
    "The Flute",
    "The Bell Cricket",
    "Yūgiri",
    "The Law",
    "Mirage",
    "Niou",
    "Kōbai",
    "Bamboo River",
    "The Bridge Maiden",
    "At the Foot of the Oak Tree",
    "Agemaki",
    "Fern Shoots",
    "The Mistletoe",
    "The Eastern House",
    "Ukifune",
    "The Gossamer Fly",
    "Writing Practice"
]

RED = "red"

GenjikoType = List[Tuple[float, Set[int]]]


def intervals_overlap(group1: Set[int], group2: Set[int]) -> bool:
    """
    Checks if the intervals defined by two groups overlap.
    Returns True if they overlap, False otherwise.
    """
    min1, max1 = min(group1), max(group1)
    min2, max2 = min(group2), max(group2)
    return not (max1 < min2 or max2 < min1)


@validate_call
def validate_genjiko(genjiko: GenjikoType):
    """
    Validates that no two groups with the same height overlap.
    Returns True if valid, False otherwise.
    """
    for i, (height1, group1) in enumerate(genjiko):
        for height2, group2 in genjiko[i + 1:]:
            if height1 == height2 and intervals_overlap(group1, group2):
                return False
    return True


@validate_call
def draw_genjiko(
    img,
    x: int,
    y: int,
    height: int,
    width: int,
    line_width: int,
    genjiko: GenjikoType, 
    color: str = "black",
    rubricate: bool = False,
):
    """
    Draws a single genji-ko pattern on an existing image at a specified
    position.
    """
    if not validate_genjiko(genjiko):
        raise ValueError(f"Genjiko pattern {genjiko!r} is invalid.")
    
    draw = ImageDraw.Draw(img)

    max_index = max([ max(p) for h, p in genjiko ])

    # positions of the vertical lines.
    line_positions = [
        x + (i * (width - line_width) // 4) + line_width // 2
        for i in range(max_index)
    ]

    # Draw each group
    for height_ratio, group in genjiko:
        group_height = y + (1 - height_ratio) * height  
        left_index = min(group) - 1 
        right_index = max(group) - 1

        group_color = color
        if rubricate and (1 in group):
            group_color = RED

        # Draw vertical lines for each element in the group
        for element in group:
            x = line_positions[element - 1]  
            draw.line(
                [(x, y + height-1), (x, group_height)],
                fill=group_color,
                width=line_width
            )

        if len(group) > 1:
            # Draw horizontal connector line across the group
            cap_width = line_width // 2 - 1

            left_x = line_positions[left_index] - line_width // 2

            right_x = line_positions[right_index] + \
                      line_width // 2 - ((line_width+1) % 2)

            draw.line([
                (left_x, group_height + cap_width), 
                (right_x, group_height + cap_width)
            ], fill=group_color, width=line_width)


@validate_call
def partitions(s: Set[int]) -> Iterator[List[Set[int]]]:
    """Yield all partitions of a set as they are generated."""
    if not s:
        yield []
        return
    first = min(s) # use the least element for a more natural order
    rest = s - {first}
    for partition in partitions(rest):
        yield [{first}] + partition
        for i in range(len(partition)):
            new_partition = partition[:i] + \
                            [partition[i] | {first}] + partition[i+1:]
            yield new_partition


@validate_call
def is_nested_within(group1: Set[int], group2: Set[int]) -> bool:
    """
    Checks if group1 is nested within group2 based on interval overlap.
    Returns True if group1 is strictly inside group2, False otherwise.
    """
    return min(group1) > min(group2) and max(group1) < max(group2)


@validate_call
def optimal_genjiko_for_partition(
    partition: List[Set[int]]
) -> List[Tuple[float, Set[int]]]:
    """
    Given a partition, find the optimal genji-ko layout by minimizing a cost
    function.

    I was originally hoping to get to 100% algorithmic generation, but this
    simple rule captures all but 4 of layouts, and the remaining four cannot be
    expressed in any rule which is shorter and simpler than just simply listing
    the special cases.
    """
    best_cost = math.inf
    best_genjiko = None
    HEIGHTS = [1.0, 0.8, 0.6]
    
    # Generate all combinations of heights for each group in the partition
    for height_combo in itertools.product(HEIGHTS, repeat=len(partition)):
        genjiko_candidate = [
            (height, group) 
            for height, group 
            in zip(height_combo, partition)
        ]
        
        # Skip invalid configurations
        if not validate_genjiko(genjiko_candidate):
            continue
        
        # Encourage larger heights
        cost = -sum(height for height, _ in genjiko_candidate)  
        
        # Encourage groups nested inside of other groups to be lower.
        for height1, group1 in genjiko_candidate:
            for height2, group2 in genjiko_candidate:
                if is_nested_within(group1, group2) and height1 > height2:
                    cost += 1
        
        # keep track of the best solution so far
        if cost < best_cost:
            best_cost = cost
            best_genjiko = genjiko_candidate

    return best_genjiko


@validate_call
def generate_all_genjiko_patterns(
    n: int = 5
) -> Iterator[List[Tuple[float, Set[int]]]]:
    """
    Generate optimal genji-ko patterns for all partitions of a set of `n`
    elements.
    """
    for partition in partitions(set(range(1, n+1))):
        optimal_genjiko = optimal_genjiko_for_partition(partition)
        if optimal_genjiko:
            yield optimal_genjiko


@validate_call
def draw_genjiko_grid(
    genjiko_patterns: List[GenjikoType],
    cell_size: int = 100,
    padding: int = 50,
    grid_width: int = 4,
    grid_height: int = 13,
    grid_indent: int = 0,
    line_width: int = 14,
    rubricate: bool = False,
) -> Image:
    """
    A simple utility to draw a list of genjiko patterns in an arbitrary grid.
    """
    
    # Setup grid parameters
    image_width = grid_width * (cell_size + padding) - padding + 100
    image_height = grid_height * (cell_size + padding) - padding + 100
    
    # Create a new image with a white background
    img = Image.new("RGB", (image_width, image_height), "white")
    
    # Draw each Genjiko in the grid
    for i, genjiko in enumerate(genjiko_patterns):
        i += grid_indent
        row, col = divmod(i, grid_width)
        x = col * (cell_size + padding) + padding // 2
        y = row * (cell_size + padding) + padding // 2
        
        # Draw the Genjiko pattern at the specified position
        draw_genjiko(
            img, 
            x=x, 
            y=y, 
            height=cell_size, 
            width=cell_size, 
            line_width=line_width, 
            genjiko=genjiko,
            rubricate=rubricate,
        )
    
    return img


@validate_call
def parse_genjiko_file() -> Iterator[Tuple[str, str, List[Set[int]]]]:
    """
    Reads the genji-ko text file, which is in this line-delimited format:
    
        "Kanji - Romaji - Permutation"

    with  no column headers. Be sure to use utf-8 so that Kanji load!
    """
    
    #with open(filename, 'r', encoding='utf-8') as file:
    resource = resources.files("genjiko").joinpath("data/genjiko.txt")
    with resource.open("r", encoding="utf-8") as file:
        for line in file:
            kanji, romaji, partition_json = line.strip().split(" - ")
            partition = eval(partition_json)
            yield (kanji, romaji, partition)


def check_dataframe_partitions(df: pd.DataFrame):
    """
    Interactive function to verify the partitions of the data frame
    exactly match the set of all partitions of a set of 5 elements.
    Only needed when making changes to `genjiko.txt`.
    """
    # check for duplicates in the data frame
    dupes = df[df["Partition"].duplicated(keep=False)]
    if len(dupes):
        print(dupes)

    # we need hashable types to put things into sets
    def freeze(items):
        return frozenset(
            frozenset(s) for s in items
        )
    # the set of partitions of 5 things.
    p5 = set(freeze(p) for p in partitions({1, 2, 3, 4, 5}))
    
    # check for extra patterns in the data frame
    for partition in df['Partition']:
        frozen_partition = freeze(partition)
        if frozen_partition not in p5:
            print(partition)
    
    # check for patterns missing from the data frame
    dfp5 = set(freeze(p) for p in df["Partition"])
    for frozen_partition in p5:
        if frozen_partition not in dfp5:
            print(frozen_partition)
            

def load_genjiko() -> pd.DataFrame:
    """
    Loads the file containing the traditional name, order, and permutation of
    each genji-ko, validates it, calculates an optimal layout, and handles
    special cases where the optimal layout does not match the traditional
    layout.
    """
    df = pd.DataFrame(
        list(parse_genjiko_file()),
        columns=["Kanji", "Romaji", "Partition"]
    )

    df['Icon'] = list(GENJIKO_CHARS)
    df.insert(0, "Chapter", 2 + pd.Series(range(len(df))))
    df.insert(3, "English", ENGLISH_TITLES)

    # calculate optimal layouts
    df["Layout"] = df["Partition"].apply(optimal_genjiko_for_partition)

    # default color is black.
    df["Color"] = "black"
    
    # special cases. flag these in red for review.
    
    # Suma: {1, 3, 4} should be lower than {2, 5}
    df.at[10, "Layout"] = [ (0.8, {1, 3, 4}), (1.0, {2, 5}) ]
    df.at[10, "Color"] = "red"
    
    # Hatsune: {1, 3} should be lower than {2, 4}
    df.at[21, "Layout"] = [ (0.8, {1, 3}), (1.0, {2, 4}), (1.0, {5}) ]
    df.at[21, "Color"] = "red"
    
    # Yuguri: {1, 4} should be lower than {3, 5}, and {2} even lower.
    df.at[37, "Layout"] = [ (0.8, {1, 4}), (0.6, {2}), (1.0, {3, 5}) ]
    df.at[37, "Color"] = "red"
    
    # Nioumiya: {1, 2, 4} should be lower than {3, 5}
    df.at[40, "Layout"] = [ (0.8, {1, 2, 4}), (1.0, {3, 5}) ]
    df.at[40, "Color"] = "red"

    return df
    

def draw_annotated_genjiko_grid(
    df: pd.DataFrame,
    grid_width: int = 4,
    grid_height: int = 13,
    cell_size: int = 100,
    padding: int = 50,
    text_height: int = 20,
    include_index_label: bool = True,
    include_kanji_label: bool = True,
    include_romaji_label: bool = True,
    kanji_font: str = "msgothic.ttc",
    kanji_font_size: int = 18,
    kanji_text_offset: int = 14,
    romaji_text_offset: int = 20,
    romaji_font: str = "arial.ttf",
    romaji_font_size: int = 14,
    line_width: int = 14,
    grid_indent: int = 0,
):
    """
    A more specialized function to draw genji-ko, this time using the data
    frame as the source of truth for order and genji-ko pattern; this pattern
    will be the algorithmically determined optimal pattern, or the special 
    case if overridden. Can also print the index, kanji, and romaji.
    """
    # grid calculations
    cell_width = cell_size + padding
    cell_height = cell_size + padding + text_height

    image_width = grid_width * cell_width - padding + cell_size
    image_height = grid_height * cell_height - padding + cell_size
    
    # Create a new image with a white background
    img = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(img)

    # font setup
    font_kanji = ImageFont.truetype(kanji_font, kanji_font_size)
    font_romaji = ImageFont.truetype(romaji_font, romaji_font_size)

    # Draw each Genjiko in the grid
    for i, row in df.iterrows():
        i += grid_indent
        row_num, col_num = divmod(i, grid_width)
        x = col_num * cell_width + padding
        y = row_num * cell_height + padding
        
        # Draw the Genjiko pattern at the specified position
        draw_genjiko(
            img,
            x=x,
            y=y,
            height=cell_size,
            width=cell_size,
            line_width=line_width,
            genjiko=row["Layout"],
            color=row.get("Color", "black"),
        )
        
        # Calculate vertical text positions
        kanji_text_y = y + cell_size + kanji_text_offset
        romaji_text_y = kanji_text_y + romaji_text_offset

        # Draw Kanji and Romaji text
        if include_index_label:
            draw.text(
                (x, kanji_text_y), 
                f"{i+1}.", 
                font=font_romaji, 
                fill="black", 
                anchor="lm",
            )

        if include_kanji_label:
            draw.text(
                (x + cell_size / 2, kanji_text_y), 
                row["Kanji"], 
                font=font_kanji, 
                fill="black", 
                anchor="mm",
            )

        if include_romaji_label:
            draw.text(
                (x + cell_size / 2, romaji_text_y), 
                row["Romaji"], 
                font=font_romaji, 
                fill="black", 
                anchor="mm",
            )

    # Display or save the final image
    return img


def draw_genjiko_font_grid():
    """
    Draws the genji-ko from genjiko.ttf in the same grid pattern, so
    it can be compared to my algorithmically generated version.
    This font comes from here:

        https://www.illllli.com/font/symbol/genjiko/

    It seems to be 100% correct in terms of the names and order, so
    is a high-quality reference point. 
    """
    # Load the genjiko font from the local directory
    font_genjiko = ImageFont.truetype("genjiko.ttf", 80)

    # Grid parameters
    grid_width, grid_height = 7, 8
    cell_size = 100
    padding = 20
    image_width = grid_width * (cell_size + padding) - padding
    image_height = grid_height * (cell_size + padding) - padding

    # Create a new image with a white background
    img = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(img)

    # Draw each Genjiko pattern in the grid
    for i, char in enumerate(GENJIKO_CHARS):
        row, col = divmod(i+1, grid_width)
        x = col * (cell_size + padding)
        y = row * (cell_size + padding)

        # Draw the Genjiko character in the center of each cell
        draw.text(
            (x + cell_size / 2, y + cell_size / 2), 
            char, 
            font=font_genjiko, 
            fill="black", 
            anchor="mm",
        )

    # Display or save the final image
    return img

def generate_html_table(genjiko_df):
    # local imports to avoid requiring optional dependencies
    from jinja2 import Template
    from IPython.core.display import HTML

    # clean up the set notation
    df = genjiko_df[["Chapter", "Kanji", "Romaji", "English", "Partition", "Icon"]].copy()
    if "Color" in genjiko_df.columns:
        df["Color"] = genjiko_df["Color"]
    df["Partition"] = [ repr(p)[1:-1] for p in df["Partition"] ]
    
    template = """
<div class="genjiko-wrapper">
    <style>
        html .article table.genjiko-table td {
            font-size: 100%;
            line-height: 1;
        }
        html .article table.genjiko-table th {
            font-size: 100%;
        }
       html .article table.genjiko-table td.genjiko-chapter {
        text-align: center;
       }
       html .article table.genjiko-table td.genjiko-kanji {
            font-size: 125%;
            text-align: center;
        }
        html .article table.genjiko-table td.genjiko-icon {
            font-size: 200%;
            font-family: 'GenjiKo', sans-serif;
            text-align: center;
            padding: 0px;
            margin: 0px;
        }
        html .article table.genjiko-table td..genjiko-partition {
            text-align: center;
        }
        @font-face {
            font-family: 'GenjiKo';
            src: url('/post/genji-ko_files/genjiko.ttf') format('truetype');
        }
    </style>
    <table class="genjiko-table">
        <thead>
            <tr>
                <th>Chapter</th>
                <th>Kanji</th>
                <th style="text-align: left;">Romaji</th>
                <th style="text-align: left;">English</th>
                <th style="text-align: left;">Partition</th>
                <th>Genji-mon</th>
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr>
                <td class="genjiko-chapter">{{ row.Chapter }}</td>
                <td class="genjiko-kanji">{{ row.Kanji }}</td>
                <td class="genjiko-romaji">{{ row.Romaji }}</td>
                <td class="genjiko-english">{{ row.English }}</td>
                <td class="genjiko-partition">{{ row.Partition }}</td>
                <td class="genjiko-icon"{% if row.Color %} style="color: {{row.Color}};"{% endif %}>{{ row.Icon }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
    """

    # Convert DataFrame to a list of dicts for Jinja2
    rows = df.to_dict(orient="records")

    # Render the template with the data
    rendered_html = Template(template).render(rows=rows)

    # Return as HTML object for Jupyter Notebook
    return HTML(rendered_html)


def bell_number(n: int) -> int:
    """Calculate Bell's number $B_n$ for any integer `n`."""
    if n < 0:
        raise ValueError("The Bell number is not defined for n < 0.")
    elif n < 2:
        return 1
    else:
        return sum(
            comb(n-1, k) * bell_number(k)
            for k in range(0, n)
        )
