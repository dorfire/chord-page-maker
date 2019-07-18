import sys
from os import path
from PIL import Image
from models import ChordDesc
from chords import get_chord_image_lists
from cache import get_urls_as_local_paths
import logging


A4_SIZE = (595, 842) # A4 at 72dpi

APP_DIR = path.dirname(path.abspath(__file__))
CACHE_DIR = path.join(APP_DIR, 'chord_cache')

MARGIN_X = -6
MARGIN_Y = 0


def parse_chord_description(desc: str):
	parts = desc.split('~')
	return ChordDesc(parts[0], None if len(parts) == 1 else int(parts[1]))


def parse_fret(fret: str):
	return int(fret) if fret != 'x' else None


def _select_chord_path(image_paths: list, chord_desc: ChordDesc):
	if not chord_desc.minfret:
		return image_paths[0]

	# Example path: bla/A-Minor-Fsharp-2%2C3%2C2%2C5%2C5%2C5.png
	for img_path in image_paths:
		file_name_without_ext = path.splitext(path.basename(img_path))[0]
		logging.info('Parsing file name "%s"', file_name_without_ext)

		path_parts = file_name_without_ext.split('-')
		fret_part = [part for part in path_parts if part[0].isdigit() or part.startswith('x')][0]

		# Example fret_part: 2%2C3%2C2%2C5%2C5%2C5
		frets = [parse_fret(f) for f in fret_part.split('%2C')]
		base_fret = min(filter(lambda f: f is not None, frets))
		logging.info('Frets for fingering: %r; base=%d', frets, base_fret)

		if base_fret >= chord_desc.minfret:
			return img_path
	
	logging.warning('Could not find a match for name="%s", minfret="%d"',
		chord_desc.name, chord_desc.minfret)
	return image_paths[0]


def main(args) -> int:
	if len(args) != 3:
		print('Required args: <comma separated chords> <output path> <rtl or ltr>')
		print('Example:')
		print('  Em,Am/F#~4,Em/G,Bsus4,Em,Am/F#~4,E/G#~4,Am,Em7/C,Em/C#~11,G/D~10,Dm7~10 ./out1.png rtl')
		print('  Em,Am/F#~4,Em/G,Bsus4,Em,Am/F#~4,E/G#~4,Am,Em7/C,Em/C#~11,G/D~10,Dm7~10 ./out2.png rtl')
		return 1

	chords_raw, out_path, rtl_or_ltr = args
	chords = list(map(parse_chord_description, chords_raw.split(',')))

	logging.info('Making a page for chord sequence: %r', chords)

	# Get chord image URLs
	chord_image_urls  = get_chord_image_lists(chords)
	# Get cached paths for URLs
	chord_image_paths = get_urls_as_local_paths(chord_image_urls, CACHE_DIR)
	logging.debug(chord_image_paths)
	
	page = Image.new('RGBA', A4_SIZE, (255, 255, 255, 0))

	# Assume RTL for now
	# TODO: support LTR
	x_cursor, y_cursor = page.size[0], 0 # Right to left, top to bottom
	for chord, image_paths in zip(chords, chord_image_paths):
		if not image_paths:
			logging.error('No image paths for %s', chord.name)
			continue

		image_path = _select_chord_path(image_paths, chord)

		chord_img = Image.open(image_path)
		chord_img = chord_img.convert('RGBA')

		x_displacement = chord_img.size[0] + MARGIN_X
		x_cursor -= x_displacement
		if x_cursor < 0:
			x_cursor = page.size[0] - x_displacement
			y_cursor += chord_img.size[1]

		if y_cursor > page.size[1] - chord_img.size[1]:
			raise RuntimeError('Vertical page overflow')

		bbox = (x_cursor, y_cursor)
		page.paste(chord_img, bbox)
		logging.info('Pasted %s @ %r', chord, bbox)

	page.save(out_path, 'PNG', quality=100)
	return 0


if __name__ == '__main__':
	logging.basicConfig(format='%(asctime)s\t%(levelname)s:\t%(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)
	sys.exit(main(sys.argv[1:]))
