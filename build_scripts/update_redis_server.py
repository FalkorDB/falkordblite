#!/usr/bin/env python3
""" Update the redis.submodule in the redislite repo to the latest stable version """
import os
import pathlib
import shutil
import urllib.request
import urllib.error
import urllib.parse
import tarfile
import tempfile
import time
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_version = os.environ.get('REDIS_VERSION', '8.2.2')
url = f'https://download.redis.io/releases/redis-{redis_version}.tar.gz'


def download_with_retry(url, max_retries=3, backoff_factor=2, token=None):
    """
    Download a file from a URL with retry logic and optional authentication.
    
    Args:
        url: URL to download from
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff between retries
        token: Optional GitHub token for authenticated requests
    
    Returns:
        File-like object from urllib.request.urlopen
    
    Raises:
        urllib.error.URLError: If all retry attempts fail
    """
    headers = {}
    if token:
        # GitHub accepts token in Authorization header
        headers['Authorization'] = f'token {token}'
    
    for attempt in range(max_retries):
        try:
            if headers:
                req = urllib.request.Request(url, headers=headers)
                return urllib.request.urlopen(req)
            else:
                return urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                logger.warning(f'HTTP 403 Forbidden on attempt {attempt + 1}/{max_retries} for {url}')
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.info(f'Retrying in {wait_time} seconds...')
                    time.sleep(wait_time)
                else:
                    logger.error(f'Failed to download {url} after {max_retries} attempts')
                    # Parse URL to check if it's from GitHub
                    parsed_url = urllib.parse.urlparse(url)
                    if parsed_url.netloc == 'github.com' or parsed_url.netloc.endswith('.github.com'):
                        logger.error('For GitHub downloads, consider setting GITHUB_TOKEN environment variable')
                    raise
            else:
                raise
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                logger.warning(f'Download failed on attempt {attempt + 1}/{max_retries}: {e}')
                logger.info(f'Retrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                logger.error(f'Failed to download {url} after {max_retries} attempts: {e}')
                raise


if __name__ == "__main__":
    if pathlib.Path('redis_submodule').exists():
        shutil.rmtree('redis.submodule')
    with tempfile.TemporaryDirectory() as tempdir:
        print(f'Downloading {url} to temp directory {tempdir}')
        # Use retry logic for more robust downloads
        ftpstream = download_with_retry(url)
        tf = tarfile.open(fileobj=ftpstream, mode="r|gz")
        directory = tf.next().name
        
        print(f'Extracting archive {directory}')
        tf.extractall(tempdir)
        
        print(f'Moving {os.path.join(tempdir, directory)} -> redis.submodule')
        shutil.move(os.path.join(tempdir, directory), 'redis.submodule')
        
        # print('Updating jemalloc')
        # os.system('(cd redis.submodule;./deps/update-jemalloc.sh 4.0.4)')
        
        # print('Adding new redis.submodule files to git')
        # os.system('git add redis.submodule')
