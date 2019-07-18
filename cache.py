import os, asyncio, aiohttp
from urllib.parse import urlparse, quote
import logging


HTTP_OK = 200


async def _download_url(client, url: str, local_path: str):
	if os.path.isfile(local_path):
		logging.debug('EXISTS "%s"', url)
		return local_path

	logging.debug('GET "%s"', url)
	async with client.get(url) as res:
		if res.status != HTTP_OK:
			logging.error('Request to "%s" failed with status=%d', url, res.status)
			return None

		with(open(local_path, 'wb')) as fp:
			fp.write(await res.read())
		return local_path

async def _cache_url_list(client, urls: list, cache_dir: str):
	downloaders = []
	for url in urls:
		filename = os.path.basename(urlparse(url).path)
		filepath = os.path.join(cache_dir, filename)
		downloaders.append(_download_url(client, url, filepath))

	return await asyncio.gather(*downloaders)


async def _cache_url_lists(url_lists: list, cache_dir: str):
	# Schedule requests concurrently
	async with aiohttp.ClientSession() as client:
		downloaders = [_cache_url_list(client, url_list, cache_dir) for url_list in url_lists]
		return await asyncio.gather(*downloaders)


def get_urls_as_local_paths(urls: list, cache_dir: str):
	results = asyncio.run(_cache_url_lists(urls, cache_dir))
	logging.info('Cache %d file lists', len(results))
	return results
