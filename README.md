# Genjiko

Python utilities for working with [Genjiko][G] (源氏香) patterns.

## Install

Genjiko is Python package, but is not yet on PyPI. Checkout this git repo
and install it locally to use it:

```bash
git clone https://github.com/olooney/genjiko
cd genjiko
pip install .
```

## Usage

Load the annotated data as a `pandas.DataFrame`:
```python
genjiko_df = load_genjiko()
```

| Chapter | Kanji  | Romaji        | English            | Partition                       | Icon | Layout                                                       | Color |
|---------|--------|---------------|--------------------|---------------------------------|------|--------------------------------------------------------------|-------|
| 2       | 帚木   | Hōkigi        | The Broom Tree     | [{1}, {2}, {3}, {4}, {5}]       | B    | [(1.0, {1}), (1.0, {2}), (1.0, {3}), (1.0, {4}), (1.0, {5})] | black |
| 3       | 空蝉   | Utsusemi      | Utsusemi           | [{1}, {2}, {3}, {4, 5}]         | C    | [(1.0, {1}), (1.0, {2}), (1.0, {3}), (1.0, {4, 5})]          | black |
| 4       | 夕顔   | Yūgao         | Yūgao              | [{1}, {2}, {3, 4}, {5}]         | D    | [(1.0, {1}), (1.0, {2}), (1.0, {3, 4}), (1.0, {5})]          | black |
| 5       | 若紫   | Wakamurasaki  | Young Murasaki     | [{1}, {2, 3}, {4, 5}]           | E    | [(1.0, {1}), (1.0, {2, 3}), (1.0, {4, 5})]                   | black |
| ...     |
| 49      | 宿木   | Yadorigi      | The Mistletoe      | [{1, 2, 4, 5}, {3}]             | w    | [(1.0, {1, 2, 4, 5}), (0.8, {3})]                            | black |
| 50      | 東屋   | Azumaya       | The Eastern House  | [{1, 2, 5}, {3}, {4}]           | x    | [(1.0, {1, 2, 5}), (0.8, {3}), (0.8, {4})]                   | black |
| 51      | 浮舟   | Ukifune       | Ukifune            | [{1, 5}, {2, 3}, {4}]           | y    | [(1.0, {1, 5}), (0.8, {2, 3}), (0.8, {4})]                   | black |
| 52      | 蜻蛉   | Kagerō        | The Gossamer Fly   | [{1, 3, 5}, {2, 4}]             | z    | [(1.0, {1, 3, 5}), (0.8, {2, 4})]                            | black |
| 53      | 手習   | Tenarai       | Writing Practice   | [{1, 2, 3, 4, 5}]               | 1    | [(1.0, {1, 2, 3, 4, 5})]                                     | black |

Render the chart, with various graphical options:

```python
draw_annotated_genjiko_grid(
    genjiko_df,
    cell_size=82,
    grid_width=8,
    grid_height=7,
    line_width=14,
    padding=20,
    include_index_label=False,
    include_romaji_label=False,
    grid_indent=1,
)
```

The utility `draw_genjiko_font_grid()` depends on the `genjiko.ttf` font 
available from https://www.illllli.com/font/symbol/genjiko/.

[G]: https://www.oranlooney.com/post/genji-ko/
