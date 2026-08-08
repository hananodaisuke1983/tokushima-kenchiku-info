# -*- coding: utf-8 -*-
"""
公開サイト（GitHub Pages）用の自動更新スクリプト。GitHub Actionsから実行される。

【重要な設計方針】
このサイトは一般公開されるため、設計事務所名・法人番号・営業戦略等の
個社情報は一切載せない。徳島県入札情報サービスの「建築一式工事」入札公告
（案件名・工種・公告日のみ）という、県が既に公開している事実情報だけを
表示する。
"""
import re
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

HTML_PATH = "index.html"
JST = timezone(timedelta(hours=9))


def fetch_latest_kenchiku_tenders():
    """徳島県の発注見通し・入札公告から「建築一式工事」案件を取得する（会社名は含まない）。"""
    url = "https://e-ppi.pref.tokushima.lg.jp/jouhou/ankens/front"
    res = requests.get(url, params={"dantai_code": "360000"},
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    projects = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = "".join(c.get_text() for c in rows[0].find_all(["th", "td"]))
        if "案件名" not in header:
            continue
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            date_open = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)
            category = cols[2].get_text(strip=True)
            date_announce = cols[3].get_text(strip=True)
            if "建築一式" in category:
                projects.append({
                    "name": name, "category": category,
                    "announce": date_announce, "open": date_open,
                })
    return projects[:20]  # 直近20件まで


def build_rows_html(projects):
    if not projects:
        return '<tr><td colspan="3" class="py-4 px-6 text-center text-slate-400">現在、公告中の建築一式工事案件はありません</td></tr>'
    rows = ""
    for p in projects:
        rows += f"""
                        <tr class="hover:bg-slate-50 transition">
                            <td class="py-4 px-6 font-bold text-slate-800">{p['name']}</td>
                            <td class="py-4 px-6 text-slate-500 text-xs">{p['category']}</td>
                            <td class="py-4 px-6 text-slate-500 text-xs">公告: {p['announce']} / 開札: {p['open']}</td>
                        </tr>"""
    return rows


def update_html(projects):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M")
    content = re.sub(r"最終取得日: [^<]*", f"最終取得日: {now}", content)

    rows_html = build_rows_html(projects)
    pattern = re.compile(r"<!-- LATEST_TENDERS_START -->.*?<!-- LATEST_TENDERS_END -->", re.DOTALL)
    replacement = f"<!-- LATEST_TENDERS_START -->{rows_html}\n                        <!-- LATEST_TENDERS_END -->"
    content = pattern.sub(replacement, content)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"更新完了: {len(projects)}件")


if __name__ == "__main__":
    projects = fetch_latest_kenchiku_tenders()
    update_html(projects)
