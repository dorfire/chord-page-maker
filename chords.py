from models import ChordDesc
import asyncio, aiohttp
from urllib.parse import quote
from lxml import html
import logging


HTTP_OK = 200
JGUITAR_BASE_URL = 'https://jguitar.com'
JGUITAR_SEARCH_URL_FMT = JGUITAR_BASE_URL + '/chordsearch?chordsearch={}'


async def _get_chord_image_urls(client: aiohttp.ClientSession, chord: ChordDesc):
	url = JGUITAR_SEARCH_URL_FMT.format(quote(chord.name))
	logging.debug('GET "%s"', url)
	async with client.get(url) as res:
		if res.status != HTTP_OK:
			logging.error('Request to "%s" failed with status=%d', url, res.status)
			return []

		page = html.document_fromstring(await res.text())
		return [
			JGUITAR_BASE_URL + img.attrib['src']
			for img in page.xpath('//img')
			if 'chordshape' in img.attrib['src']
		]


async def _gather_chord_image_url_lists(chords: list):
	# Schedule requests concurrently
	async with aiohttp.ClientSession() as client:
		getters = [_get_chord_image_urls(client, chord) for chord in chords]
		return await asyncio.gather(*getters)


def get_chord_image_lists(chords: list):
	request_results = asyncio.run(_gather_chord_image_url_lists(chords))
	logging.info('Gathered results from %d requests', len(request_results))
	return request_results
