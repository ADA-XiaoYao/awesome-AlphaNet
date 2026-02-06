import os
import re
import aiohttp
import asyncio
from datetime import datetime

broken_links = []

link_pattern = re.compile(r'\[([^\]]+)\]\((https://github\.com/[^\)]+)\)')

async def check_url(session, url):
    try:
        async with session.head(url, allow_redirects=True, timeout=10) as resp:
            if resp.status in [404, 410]:
                print(f"[{resp.status}] {url}")
                broken_links.append(url)
                return True
    except Exception:
        print(f"[Error] {url}")
        broken_links.append(url)
        return True
    return False

async def process_file(session, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    tasks = []
    for line in lines:
        matches = link_pattern.findall(line)
        for name, url in matches:
            tasks.append(check_url(session, url))
    await asyncio.gather(*tasks)

    new_lines = []
    for line in lines:
        matches = link_pattern.findall(line)
        remove_line = False
        for name, url in matches:
            if url in broken_links:
                remove_line = True
                break
        if not remove_line:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

async def main():
    async with aiohttp.ClientSession() as session:
        md_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))

        tasks = [process_file(session, f) for f in md_files]
        await asyncio.gather(*tasks)

    log_file = f"auto_clean_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        for url in broken_links:
            f.write(url + "\n")
    print(f"\n✅ Done. Removed {len(broken_links)} broken links. Report saved to {log_file}")

if __name__ == "__main__":
    asyncio.run(main())
