import asyncio
import logging
import os


URL_PLACEHOLDER = '{url}'


class YT2DL():


    def __init__(self, download_command):
        self.downloads = {}
        self.command = download_command

    def add(self, url, save_path, on_failure=lambda: None):
        if save_path is not None:
            if not os.path.exists(save_path):
                logging.warning('download directory {} does not exist, creating'.format(save_path))
                os.makedirs(save_path)
        if self.downloads.get(url) is None:
            self.downloads[url] = asyncio.get_event_loop().create_task(self.start_downloader(url, save_path, on_failure))
        else:
            logging.debug('downloader for {} was called already'.format(url))

    async def start_downloader(self, url, save_path=None, on_failure=lambda: None):
        args = self.command.replace(URL_PLACEHOLDER, url).split()
        logging.info('starting download subprocess for {}'.format(url))
        process = await asyncio.create_subprocess_exec(*args, cwd=save_path)
        await process.wait()
        logging.debug('download subprocess for {} finished with exit code {}'.format(url, process.returncode))
        self.downloads.pop(url)
        if process.returncode != 0:
            on_failure()
