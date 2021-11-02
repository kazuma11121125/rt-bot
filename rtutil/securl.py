# RT Util - Sec URL

from typing import TypedDict

from aiohttp import ClientSession
from ujson import loads


HEADERS = {
    "Connection": "keep-alive",
    "sec-ch-ua": '"Microsoft Edge";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.40",
    "sec-ch-ua-platform": '"macOS"',
    "Origin": "https://securl.nu",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://securl.nu/",
    "Accept-Language": "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
}
CAPTURE_URL_BASE = "https://securl.nu"


class SecURLData(TypedDict):
    status: int
    imgWidth: int
    imgHeight: int
    reqURL: str
    resURL: str
    title: str
    anchors: list
    viruses: list
    blocakList: list
    annoyUrl: str
    img: str
    capturedDate: str


async def check(
    session: ClientSession, url: str, wait_time: int = 1,
    browser_width: int = 965, browser_height: int = 683,
    headers: dict = HEADERS
) -> SecURLData:
    "渡されたURLをSecURLでチェックします。"
    async with session.post(
        "https://securl.nu/jx/get_page_jx.php", data={
            "url": url, 'waitTime': str(wait_time),
            'browserWidth': str(browser_width),
            'browserHeight': str(browser_height), 'from': ''
        }, headers=headers
    ) as r:
        return loads(await r.text())


def get_capture(data: SecURLData) -> str:
    "渡されたデータにある`img`のデータからURLを作ります。"
    return f"{CAPTURE_URL_BASE}{data['img']}"


if __name__ == "__main__":
    from asyncio import run

    async def main(url):
        async with ClientSession() as session:
            return await check(session, url)

    data = run(main(input("URL>")))
    print(data)
    print(get_capture(data))