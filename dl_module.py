import asyncio
import logging
import os
import shlex


URL_PLACEHOLDER = '{url}'


class YT2DL():

    def __init__(self, download_command, url_placeholder=URL_PLACEHOLDER):
        self.downloads = {}
        self.url_placeholder = url_placeholder
        self.command = download_command
        try:
            self.args = shlex.split(self.command)
        except ValueError as e:
            logging.error(f'Error parsing "download_command" string {self.command}: {e}')
            raise

    def args_for(self, url):
        # need a copy of template arguments list anyway, since it gets changed
        return [url if arg == self.url_placeholder else arg for arg in self.args]

    def add(self, url, save_path, on_failure=lambda: None, on_success=lambda: None):
        if save_path is not None:
            if not os.path.exists(save_path):
                logging.warning('download directory {} does not exist, creating'.format(save_path))
                os.makedirs(save_path)
        if self.downloads.get(url) is None:
            self.downloads[url] = asyncio.get_event_loop().create_task(self.start_downloader(url, save_path, on_failure))
        else:
            logging.debug('downloader for {} was called already'.format(url))

    async def start_downloader(self, url, save_path=None, on_failure=lambda: None, on_success=lambda: None):
        args = self.args_for(url)
        logging.info('starting download subprocess for {}'.format(url))
        process = await asyncio.create_subprocess_exec(*args, cwd=save_path)
        await process.wait()
        logging.debug('download subprocess for {} finished with exit code {}'.format(url, process.returncode))
        self.downloads.pop(url)
        if process.returncode == 0:
            on_success()
        else:
            on_failure()
