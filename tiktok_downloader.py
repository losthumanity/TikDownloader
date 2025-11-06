import aiohttp
import asyncio
import re
import json
import logging
from typing import Optional, Dict, List
import validators
from urllib.parse import urlparse, parse_qs

class TikTokDownloader:
    """
    TikTok video downloader with multiple API endpoints for reliability
    Supports HD quality downloads without watermarks
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None

        # Multiple API endpoints for reliability (ordered by quality preference)
        self.api_endpoints = [
            {
                'name': 'tikdownloader_io',  # New high-quality API
                'url': 'https://tikdownloader.io/api/ajaxSearch',
                'method': 'POST',
                'data_key': 'data'
            },
            {
                'name': 'tikwm',
                'url': 'https://www.tikwm.com/api/',
                'method': 'POST',
                'data_key': 'data'
            },
            {
                'name': 'musicaldown',
                'url': 'https://musicaldown.com/api/converter/index',
                'method': 'POST',
                'data_key': 'data'
            },
            {
                'name': 'ssstik',
                'url': 'https://ssstik.io/abc',
                'method': 'GET',
                'data_key': 'data'
            }
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract TikTok video ID from various URL formats"""
        # Clean the URL
        url = url.strip()

        # Remove any extra parameters and get the clean URL
        patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/(\d+)',
            r'https?://(?:vm|vt)\.tiktok\.com/([A-Za-z0-9]+)',
            r'https?://(?:www\.)?tiktok\.com/t/([A-Za-z0-9]+)',
            r'/video/(\d+)',
            r'(\d{19})',  # Direct video ID
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def validate_tiktok_url(self, url: str) -> bool:
        """Validate if the URL is a valid TikTok URL"""
        if not validators.url(url):
            return False

        tiktok_domains = [
            'tiktok.com',
            'vm.tiktok.com',
            'vt.tiktok.com',
            'www.tiktok.com'
        ]

        parsed_url = urlparse(url)
        return any(domain in parsed_url.netloc for domain in tiktok_domains)

    async def download_with_tikwm(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Download using tikwm.com API with quality selection"""
        try:
            data = {
                'url': url,
                'count': 12,
                'cursor': 0,
                'web': 1,
                'hd': 1
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://www.tikwm.com',
                'Referer': 'https://www.tikwm.com/'
            }

            self.logger.info(f"TikWM API: Requesting video info for {url} (quality: {quality})")

            async with self.session.post(
                'https://www.tikwm.com/api/',
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                self.logger.info(f"TikWM API response status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"TikWM API response: {result}")

                    if result.get('code') == 0 and result.get('data'):
                        data = result['data']

                        # Select video URL based on quality preference
                        if quality == 'standard' and data.get('play'):
                            # Use standard quality (SD)
                            video_url = data.get('play')
                            selected_quality = 'Standard'
                        else:
                            # Use HD quality (default) or fallback to SD
                            video_url = data.get('hdplay') or data.get('play')
                            selected_quality = 'HD' if data.get('hdplay') else 'SD'

                        if video_url:
                            # Fix relative URLs by prepending the base URL
                            if video_url.startswith('/'):
                                video_url = 'https://www.tikwm.com' + video_url

                            self.logger.info(f"TikWM API: Got {selected_quality} video URL: {video_url[:100]}...")
                            return {
                                'success': True,
                                'video_url': video_url,
                                'title': data.get('title', 'TikTok Video'),
                                'author': data.get('author', {}).get('nickname', 'Unknown'),
                                'duration': data.get('duration', 0),
                                'quality': selected_quality,
                                'thumbnail': data.get('cover'),
                                'source': 'tikwm'
                            }
                        else:
                            self.logger.error("TikWM API: No video URL in response")
                    else:
                        self.logger.error(f"TikWM API error: code={result.get('code')}, msg={result.get('msg')}")
                else:
                    response_text = await response.text()
                    self.logger.error(f"TikWM API HTTP error {response.status}: {response_text[:200]}")

        except Exception as e:
            self.logger.error(f"TikWM API error: {e}")
            self.logger.exception("Full exception:")

        return None

    async def download_with_tikdownloader_io(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Download using tikdownloader.io API (High Quality)"""
        try:
            search_url = "https://tikdownloader.io/api/ajaxSearch"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://tikdownloader.io',
                'Referer': 'https://tikdownloader.io/en',
                'X-Requested-With': 'XMLHttpRequest'
            }

            data = {
                'q': url,
                'lang': 'en'
            }

            self.logger.info(f"TikDownloader.io API: Requesting video info for {url}")

            async with self.session.post(search_url, data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()

                    if 'data' in result:
                        html_content = result['data']
                        return self._parse_tikdownloader_io_response(html_content, url)
                    else:
                        self.logger.error(f"TikDownloader.io API: No data in response: {result}")
                else:
                    self.logger.error(f"TikDownloader.io API HTTP error: {response.status}")

        except Exception as e:
            self.logger.error(f"TikDownloader.io API error: {e}")

        return None

    def _parse_tikdownloader_io_response(self, html_content: str, original_url: str) -> Optional[Dict]:
        """Parse HTML response from TikDownloader.io"""
        try:
            # Extract video title
            title_match = re.search(r'<h3[^>]*>(.*?)</h3>', html_content)
            title = title_match.group(1) if title_match else "TikTok Video"
            title = re.sub(r'<[^>]+>', '', title).strip()  # Remove HTML tags

            # Find download links - prioritize HD
            download_patterns = [
                r'href="([^"]*)" rel="nofollow"[^>]*><i class="icon icon-download"></i>\s*Download MP4\s*HD',  # HD first
                r'href="([^"]*)" rel="nofollow"[^>]*><i class="icon icon-download"></i>\s*Download MP4(?:\s*\[1\])?',  # Standard quality
            ]

            best_video_url = None
            quality = 'Unknown'

            # Try to find HD quality first
            for pattern in download_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if matches:
                    best_video_url = matches[0]  # Take the first match
                    quality = 'HD' if 'HD' in pattern else 'Standard'
                    self.logger.info(f"TikDownloader.io: Found {quality} quality video")
                    break

            # If no download links found, try direct CDN links
            if not best_video_url:
                cdn_pattern = r'https://v16-[^.]+\.tiktokcdn\.com/[^"\'\\s]+(?:\.mp4)?'
                cdn_matches = re.findall(cdn_pattern, html_content)
                if cdn_matches:
                    best_video_url = cdn_matches[0]
                    quality = 'CDN_Direct'
                    self.logger.info(f"TikDownloader.io: Found direct CDN link")

            if best_video_url:
                return {
                    'success': True,
                    'video_url': best_video_url,
                    'title': title,
                    'author': 'Unknown',  # Could be extracted from HTML if needed
                    'duration': 0,  # Could be extracted from HTML if needed
                    'quality': quality,
                    'thumbnail': None,  # Could be extracted from HTML if needed
                    'source': 'tikdownloader_io'
                }
            else:
                self.logger.error("TikDownloader.io: No video URL found in response")
                return None

        except Exception as e:
            self.logger.error(f"TikDownloader.io parsing error: {e}")
            return None

    async def download_with_musicaldown(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Download using musicaldown.com API"""
        try:
            data = {
                'url': url,
                'format': '',
                'quality': 'hd'
            }

            async with self.session.post(
                'https://musicaldown.com/api/converter/index',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    if result.get('success') and result.get('data'):
                        data = result['data']
                        video_url = data.get('url')

                        if video_url:
                            return {
                                'success': True,
                                'video_url': video_url,
                                'title': data.get('title', 'TikTok Video'),
                                'author': data.get('author', 'Unknown'),
                                'quality': 'HD',
                                'thumbnail': data.get('thumbnail'),
                                'source': 'musicaldown'
                            }
        except Exception as e:
            self.logger.error(f"MusicalDown API error: {e}")

        return None

    async def download_with_ssstik(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Download using ssstik.io API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://ssstik.io',
                'Referer': 'https://ssstik.io/en'
            }

            data = {
                'id': url,
                'locale': 'en',
                'tt': 'aSBkb3du'  # Base64 encoded token
            }

            self.logger.info(f"SSSTik API: Requesting video info for {url}")

            async with self.session.post(
                'https://ssstik.io/abc?url=dl',
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                self.logger.info(f"SSSTik API response status: {response.status}")

                if response.status == 200:
                    html = await response.text()

                    # Extract download link from HTML response
                    # SSSTik returns HTML with download links
                    video_url_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>.*?without watermark', html, re.IGNORECASE | re.DOTALL)
                    if not video_url_match:
                        # Try alternative pattern
                        video_url_match = re.search(r'<a[^>]*class="[^"]*without_watermark[^"]*"[^>]*href="([^"]+)"', html, re.IGNORECASE)

                    if video_url_match:
                        video_url = video_url_match.group(1)

                        # Extract title
                        title_match = re.search(r'<p[^>]*class="[^"]*maintext[^"]*"[^>]*>([^<]+)', html)
                        title = title_match.group(1).strip() if title_match else 'TikTok Video'

                        # Extract author
                        author_match = re.search(r'<h2>([^<]+)</h2>', html)
                        author = author_match.group(1).strip() if author_match else 'Unknown'

                        self.logger.info(f"SSSTik API: Got video URL: {video_url[:100]}...")

                        return {
                            'success': True,
                            'video_url': video_url,
                            'title': title,
                            'author': author,
                            'quality': 'HD',
                            'source': 'ssstik'
                        }
                    else:
                        self.logger.error("SSSTik API: No video URL found in response")
                else:
                    response_text = await response.text()
                    self.logger.error(f"SSSTik API HTTP error {response.status}: {response_text[:200]}")

        except Exception as e:
            self.logger.error(f"SSSTik API error: {e}")
            self.logger.exception("Full exception:")

        return None

    async def download_with_tikwm_original(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Download using TikWM's original downloader (originalDownloader.html)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://www.tikwm.com',
                'Referer': 'https://www.tikwm.com/originalDownloader.html'
            }

            data = {
                'url': url,
                'count': 12,
                'cursor': 0,
                'web': 1,
                'hd': 1
            }

            self.logger.info(f"TikWM Original Downloader: Requesting video info for {url}")

            async with self.session.post(
                'https://www.tikwm.com/api/',
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                self.logger.info(f"TikWM Original response status: {response.status}")

                if response.status == 200:
                    result = await response.json()

                    if result.get('code') == 0 and result.get('data'):
                        data = result['data']

                        # Get the original download link (wmplay = watermark play, play = without watermark)
                        video_url = data.get('wmplay') or data.get('play')

                        if video_url:
                            # Fix relative URLs
                            if video_url.startswith('/'):
                                video_url = 'https://www.tikwm.com' + video_url

                            self.logger.info(f"TikWM Original: Got video URL: {video_url[:100]}...")

                            return {
                                'success': True,
                                'video_url': video_url,
                                'title': data.get('title', 'TikTok Video'),
                                'author': data.get('author', {}).get('nickname', 'Unknown'),
                                'duration': data.get('duration', 0),
                                'quality': 'HD',
                                'thumbnail': data.get('cover'),
                                'source': 'tikwm_original'
                            }
                        else:
                            self.logger.error("TikWM Original: No video URL in response")
                    else:
                        self.logger.error(f"TikWM Original error: code={result.get('code')}, msg={result.get('msg')}")
                else:
                    response_text = await response.text()
                    self.logger.error(f"TikWM Original HTTP error {response.status}: {response_text[:200]}")

        except Exception as e:
            self.logger.error(f"TikWM Original error: {e}")
            self.logger.exception("Full exception:")

        return None

    async def download_with_fallback_scraping(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """Fallback method using direct scraping"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()

                    # Look for JSON data in script tags
                    json_pattern = r'<script[^>]*>.*?window\.__INITIAL_STATE__\s*=\s*({.*?});'
                    match = re.search(json_pattern, html, re.DOTALL)

                    if match:
                        try:
                            data = json.loads(match.group(1))

                            # Navigate through the data structure to find video info
                            # This structure may change, so it's a fallback method
                            video_detail = self._extract_video_from_initial_state(data)
                            if video_detail:
                                return video_detail
                        except json.JSONDecodeError:
                            pass

                    # Alternative: Look for specific patterns in HTML
                    video_patterns = [
                        r'"downloadAddr":"([^"]+)"',
                        r'"playAddr":"([^"]+)"',
                        r'<video[^>]*src="([^"]+)"'
                    ]

                    for pattern in video_patterns:
                        match = re.search(pattern, html)
                        if match:
                            video_url = match.group(1).replace('\\u002F', '/')
                            return {
                                'success': True,
                                'video_url': video_url,
                                'title': 'TikTok Video',
                                'author': 'Unknown',
                                'quality': 'Unknown',
                                'source': 'scraping'
                            }

        except Exception as e:
            self.logger.error(f"Fallback scraping error: {e}")

        return None

    def _extract_video_from_initial_state(self, data: Dict) -> Optional[Dict]:
        """Extract video information from TikTok's initial state data"""
        try:
            # Try to navigate the complex data structure
            # This is highly dependent on TikTok's current structure
            video_data = None

            # Common paths where video data might be located
            possible_paths = [
                ['ItemModule', 'video'],
                ['VideoPage', 'video'],
                ['ItemList', 'video-detail'],
                ['seo', 'metaParams']
            ]

            for path in possible_paths:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    # If we got through all keys successfully
                    if isinstance(current, dict) and 'playAddr' in current:
                        video_data = current
                        break

            if video_data:
                play_addr = video_data.get('playAddr')
                if isinstance(play_addr, dict):
                    video_url = play_addr.get('UrlList', [None])[0]
                elif isinstance(play_addr, str):
                    video_url = play_addr
                else:
                    video_url = None

                if video_url:
                    return {
                        'success': True,
                        'video_url': video_url,
                        'title': video_data.get('desc', 'TikTok Video'),
                        'author': video_data.get('author', {}).get('nickname', 'Unknown'),
                        'quality': 'HD',
                        'source': 'initial_state'
                    }
        except Exception as e:
            self.logger.error(f"Error extracting from initial state: {e}")

        return None

    async def get_video_info(self, url: str, quality: str = 'hd') -> Optional[Dict]:
        """
        Main method to get video information and download URL
        Tries multiple APIs for reliability

        Args:
            url: TikTok video URL
            quality: 'hd' for highest quality, 'standard' for lower quality
        """
        if not self.validate_tiktok_url(url):
            return {
                'success': False,
                'error': 'Invalid TikTok URL'
            }

        video_id = self.extract_video_id(url)
        if not video_id:
            return {
                'success': False,
                'error': 'Could not extract video ID from URL'
            }

        # Choose API methods based on quality preference
        if quality == 'hd':
            # For HD: prioritize tikdownloader.io, fallback to TikWM original downloader
            methods = [
                self.download_with_tikdownloader_io,  # Best HD quality
                self.download_with_tikwm_original,    # Fallback with original downloader
                self.download_with_ssstik,            # Alternative HD source
                self.download_with_musicaldown,
                self.download_with_fallback_scraping
            ]
            self.logger.info("Using HD quality priority: tikdownloader.io → tikwm_original")
        else:
            # For Standard: use ssstik.io, fallback to TikWM original
            methods = [
                self.download_with_ssstik,            # Good for standard quality
                self.download_with_tikwm_original,    # Fallback with original downloader
                self.download_with_tikdownloader_io,  # Always returns HD but reliable
                self.download_with_musicaldown,
                self.download_with_fallback_scraping
            ]
            self.logger.info("Using Standard quality priority: ssstik.io → tikwm_original")

        for method in methods:
            try:
                result = await method(url, quality=quality)
                if result and result.get('success'):
                    self.logger.info(f"Successfully got video info using {result.get('source', 'unknown')} method (quality: {result.get('quality', 'unknown')})")
                    return result
            except Exception as e:
                self.logger.error(f"Method {method.__name__} failed: {e}")
                continue

        return {
            'success': False,
            'error': 'All download methods failed. The video might be private or unavailable.'
        }

    async def download_video_file(self, video_url: str) -> Optional[bytes]:
        """Download the actual video file with improved error handling"""
        if not video_url:
            self.logger.error("No video URL provided")
            return None

        try:
            # Check if URL is from TikWM and needs special handling
            is_tikwm = 'tikwm.com' in video_url

            # Ensure absolute URL
            if video_url.startswith('/'):
                video_url = 'https://www.tikwm.com' + video_url
                is_tikwm = True

            # Set headers based on source
            if is_tikwm:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.tikwm.com/',
                    'Origin': 'https://www.tikwm.com',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.tiktok.com/',
                }

            self.logger.info(f"Attempting to download video from: {video_url[:100]}... (TikWM: {is_tikwm})")

            # Follow redirects and download with extended timeout for large files
            async with self.session.get(
                video_url,
                headers=headers,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(
                    total=600,  # 10 minutes total timeout
                    connect=30,  # 30 seconds to connect
                    sock_read=60  # 60 seconds to read each chunk
                )
            ) as response:

                self.logger.info(f"Video download response status: {response.status}")
                content_length = response.headers.get('Content-Length')
                if content_length:
                    self.logger.info(f"Video size: {int(content_length) / (1024*1024):.1f}MB")

                if response.status == 200:
                    # Download in chunks to avoid timeout on large files
                    chunks = []
                    downloaded = 0
                    chunk_size = 1024 * 1024  # 1MB chunks

                    try:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            chunks.append(chunk)
                            downloaded += len(chunk)

                            # Log progress for large files (every 10MB)
                            if downloaded % (10 * 1024 * 1024) < chunk_size:
                                self.logger.info(f"Downloaded: {downloaded / (1024*1024):.1f}MB")

                        content = b''.join(chunks)

                        if len(content) > 1000:  # Must be at least 1KB to be a valid video
                            self.logger.info(f"Successfully downloaded video: {len(content)} bytes ({len(content)/(1024*1024):.1f}MB)")
                            return content
                        else:
                            self.logger.error(f"Downloaded content too small: {len(content)} bytes")
                            return None

                    except asyncio.TimeoutError:
                        self.logger.error(f"Timeout while downloading (got {downloaded / (1024*1024):.1f}MB so far)")
                        return None
                    except Exception as chunk_error:
                        self.logger.error(f"Error during chunked download: {chunk_error}")
                        return None
                elif response.status == 302 or response.status == 301:
                    # Handle redirects manually if needed
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        self.logger.info(f"Following redirect to: {redirect_url}")
                        return await self.download_video_file(redirect_url)
                else:
                    self.logger.error(f"HTTP error {response.status}: {response.reason}")

        except asyncio.TimeoutError:
            self.logger.error("Video download timed out")
        except Exception as e:
            self.logger.error(f"Error downloading video file: {e}")
            self.logger.exception("Full exception:")

        return None

# Utility functions
async def download_tiktok_video(url: str, quality: str = 'hd') -> Dict:
    """
    Convenience function to download a TikTok video
    Returns video info and binary data

    Args:
        url: TikTok video URL
        quality: 'hd' for highest quality, 'standard' for lower quality (faster)
    """
    async with TikTokDownloader() as downloader:
        # Get video information with quality preference
        video_info = await downloader.get_video_info(url, quality=quality)

        if not video_info.get('success'):
            return video_info

        # Download the video file
        video_data = await downloader.download_video_file(video_info['video_url'])

        if video_data:
            video_info['video_data'] = video_data
            video_info['file_size'] = len(video_data)
            return video_info
        else:
            return {
                'success': False,
                'error': 'Failed to download video file'
            }

# Test function
async def test_download():
    """Test the downloader with a sample URL"""
    test_url = "https://www.tiktok.com/@bra1nooo/video/7535094535538347282"  # Replace with actual URL for testing

    result = await download_tiktok_video(test_url)
    print(f"Download result: {result}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run test
    asyncio.run(test_download())