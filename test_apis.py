"""
Quick test script for new API implementations
"""
import asyncio
import logging
from tiktok_downloader import TikTokDownloader

logging.basicConfig(level=logging.INFO)

async def test_apis():
    test_url = "https://www.tiktok.com/@jiraqz/video/7463873379582348566"

    async with TikTokDownloader() as downloader:
        print("\n" + "="*60)
        print("Testing HD Quality (tikdownloader.io → tikwm_original)")
        print("="*60)
        result_hd = await downloader.get_video_info(test_url, quality='hd')
        if result_hd and result_hd.get('success'):
            print(f"✅ HD Download successful!")
            print(f"   Source: {result_hd.get('source')}")
            print(f"   Quality: {result_hd.get('quality')}")
            print(f"   Title: {result_hd.get('title', '')[:50]}")
        else:
            print(f"❌ HD Download failed: {result_hd.get('error') if result_hd else 'Unknown error'}")

        print("\n" + "="*60)
        print("Testing Standard Quality (ssstik.io → tikwm_original)")
        print("="*60)
        result_std = await downloader.get_video_info(test_url, quality='standard')
        if result_std and result_std.get('success'):
            print(f"✅ Standard Download successful!")
            print(f"   Source: {result_std.get('source')}")
            print(f"   Quality: {result_std.get('quality')}")
            print(f"   Title: {result_std.get('title', '')[:50]}")
        else:
            print(f"❌ Standard Download failed: {result_std.get('error') if result_std else 'Unknown error'}")

        print("\n" + "="*60)
        print("Test Complete!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_apis())
