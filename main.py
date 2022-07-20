import sys
import json
import numpy

OUTPUT_STYLE ='''
  <style>
    body { background-color: white }
    * {
      font-family: monospace;
      font-size: 16px;
    }
    .chip {
      border-style: solid;
      border-color: black;
    }
    .cell {
      text-align: center;
      width: 25px;
      height: 25px;
      padding: 0px;
    }
    .grid {
      white-space: nowrap;
      border-collapse: collapse;
      table-layout: fixed;
      max-width: 500px;
      width: 100%;
    }
  </style>
'''

def lab_to_rgb(L, a, b):
  sRGB = [[3.2404542, -1.5371385, -0.4985314],
          [-0.9692660, 1.8760108,  0.0415560],
          [0.0556434, -0.2040259,  1.0572252]]
  e = 0.008856
  k = 903.3
  Y = (L + 16) / 116
  xyz = numpy.array([a / 500 + Y, Y, Y - b / 200])
  xyz = numpy.where(xyz**3 > 0.008856, xyz**3, (xyz - 16/116)/7.787)
  xyz = xyz * [95.047, 100.0, 108.883] / 100
  rgb = numpy.clip(numpy.array(sRGB).dot(xyz), 0, None)
  rgb = 255 * numpy.where(rgb > 0.0031308, 1.055*rgb**(1/2.4) - 0.055, 12.92*rgb)
  return list(map(int, rgb))

CHIP_NUM_TO_RGB = {}
CHIP_XY_TO_RGB = {}
CHIP_XY_TO_CHIP_NUM = {}
LANGUAGE_INFO = {}
TERMS = {}
SPEAKER_INFO = {}
COLOR_DICTIONARY = {}

def chip_pos(x, y):
  return chr(y + ord('A')) + str(x)

def chip_xy(row, col):
  return (int(col), ord(row) - ord('A'))

with open('data/cnum-vhcm-lab.txt', 'r') as f:
  header, *lines = f.read().splitlines()
  for line in lines:
    cnum, row, col, _, _, _, *lab = line.split()
    lab = list(map(float, lab))
    rgb = lab_to_rgb(*lab)
    CHIP_NUM_TO_RGB[cnum] = rgb
    CHIP_XY_TO_RGB[chip_xy(row, col)] = rgb
    CHIP_XY_TO_CHIP_NUM[chip_xy(row, col)] = cnum


def chip_pos_iter():
  yield (0, 0)
  yield '\n'
  for row in range(1, 9):
    for col in range(0, 41):
      yield (col, row)
    yield '\n'
  yield (0, 9)

def render_grid(language_id, speaker_id):
  print(OUTPUT_STYLE)
  print('<table class="grid">')
  print(f'<tr><td class="cell"> </td>')
  for col in range(0, 41):
    print(f'<td class="cell">{col}</td>')
  print('</tr>')

  print(f'<tr><td class="cell">A</td>')
  row = 1
  for pos in chip_pos_iter():
    if pos == '\n':
      print(f'</tr><tr><td class="cell">{chr(ord("A")+row)}</td>')
      row += 1
      continue

    x, y = pos
    num = CHIP_XY_TO_CHIP_NUM[(x,y)]
    speaker = TERMS[language_id]['speakers'][speaker_id]
    terms = speaker['terms']
    term = terms[num]
    R, G, B = CHIP_XY_TO_RGB[(x,y)]

    border_b = 2 if (x, y) == (0,9) or (x>=1 and y==8) else 0
    border_l = 2 if x==0 else 0
    border_t = 2 if y==0 or (x>=1 and y==1) or terms[CHIP_XY_TO_CHIP_NUM[(x, y-1)]] != term else 0
    border_r = 2 if x==40 or (x==0 and y in [0,9]) or terms[CHIP_XY_TO_CHIP_NUM[(x+1, y)]] != term else 0

    border = f"border-width: {border_t} {border_r} {border_b} {border_l}px"
    print(f'<td class="chip cell" style="{border}; background-color:rgb({R},{G},{B})">{term}</td>')

  print('</tr></table>')

  language_info = [TERMS[language_id]['info'][key] for key in ['name', 'family', 'location']]
  age, sex = [speaker['info'][key] for key in ['age', 'sex']]
  sex = 'female' if sex == 'F' else 'male'
  fields = [age, sex, *language_info]
  fields = [f'<b>{field}</b>' for field in fields]
  print("Identification by a {} year old {} speaker of {}, a language of the family {}, from {}".format(*fields))
  print("<br>")

  for abbreviation, word in COLOR_DICTIONARY[language_id].items():
    print(abbreviation, word, "<br>")

with open('data/spkr.txt', 'r') as f:
  header, *lines = f.read().splitlines()
  for line in lines:
    language_id, speaker, age, sex = line.split('\t')
    if language_id not in SPEAKER_INFO:
      SPEAKER_INFO[language_id] = {}

    SPEAKER_INFO[language_id][speaker] = {'age': age, 'sex': sex}

with open('data/dict.txt', 'r') as f:
  header, *lines = f.read().splitlines()
  for line in lines:
    language_id, _, term, abbreviation = line.split('\t')
    if language_id not in COLOR_DICTIONARY:
      COLOR_DICTIONARY[language_id] = {}

    COLOR_DICTIONARY[language_id][abbreviation] = term

with open('data/lang2.txt', 'r') as f:
  header, *lines = f.read().splitlines()
  for line in lines:
    index, name, code, family, location = line.split('\t')
    LANGUAGE_INFO[index] = {
      'name': name,
      'code': code,
      'family': family,
      'location': location
    }

with open('data/term.txt', 'r') as f:
  header, *lines = f.read().splitlines()
  for line in lines:
    language_id, speaker, chip, abbreviation = line.split()
    language_info = LANGUAGE_INFO[language_id]
    if language_id not in TERMS:
      TERMS[language_id] = {
        'info': language_info,
        'speakers': {}
      }

    if speaker not in TERMS[language_id]['speakers']:
      TERMS[language_id]['speakers'][speaker] = {'info': SPEAKER_INFO[language_id][speaker], 'terms': {}}

    TERMS[language_id]['speakers'][speaker]['terms'][chip] = abbreviation

#print(json.dumps(TERMS))

for language_id in map(str, range(1, 111)):
  render_grid(language_id, '1')
