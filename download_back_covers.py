#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup
import re

# JSON 파일 읽기
json_file = Path("yearly_bestsellers_2024/bestseller_data.json")
download_dir = Path("yearly_bestsellers_2024/back_covers")
download_dir.mkdir(exist_ok=True)

with open(json_file, 'r', encoding='utf-8') as f:
    bestsellers = json.load(f)

print(f"\n{len(bestsellers)}개 베스트셀러 뒷표지 이미지 다운로드 시작...\n")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

success_count = 0
failed_count = 0
not_found_count = 0

for book in bestsellers:
    rank = book.get('rank', 0)
    title = book.get('title', '')
    author = book.get('author', '').split('|')[0].strip()
    item_id = book.get('isbn13', '')

    # 안전한 파일명 생성
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()

    if not safe_title:
        safe_title = f"title_{rank}"
    if not safe_author:
        safe_author = f"author_{rank}"

    filename = f"{rank:03d}_{item_id}_{safe_title[:30]}_{safe_author[:20]}_back.jpg"
    file_path = download_dir / filename

    # 이미 파일이 존재하면 스킵
    if file_path.exists():
        print(f"[{rank}/100] {title}: 이미 존재")
        success_count += 1
        continue

    if not item_id:
        print(f"[{rank}/100] {title}: ItemId 없음")
        failed_count += 1
        continue

    # 웹페이지에서 뒷표지 이미지 URL 찾기
    product_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={item_id}"

    try:
        response = session.get(product_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # letslook 이미지 중 _b.jpg로 끝나는 것 찾기
        back_cover_url = None

        # 모든 이미지에서 _b.jpg 패턴 찾기
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if 'letslook' in src and '_b.jpg' in src:
                back_cover_url = src
                break

        if not back_cover_url:
            print(f"[{rank}/100] {title}: 뒷표지 없음")
            not_found_count += 1
            continue

        # 상대 경로를 절대 경로로 변환
        if back_cover_url.startswith('//'):
            back_cover_url = 'https:' + back_cover_url
        elif back_cover_url.startswith('/'):
            back_cover_url = 'https://www.aladin.co.kr' + back_cover_url

        # 뒷표지 이미지 다운로드
        img_response = session.get(back_cover_url, timeout=30)
        img_response.raise_for_status()

        # 파일 저장
        with open(file_path, 'wb') as f:
            f.write(img_response.content)

        print(f"[{rank}/100] {title}: OK ({len(img_response.content)} bytes)")
        success_count += 1
        time.sleep(0.5)  # 서버 부하 방지

    except Exception as e:
        print(f"[{rank}/100] {title}: 실패 - {e}")
        failed_count += 1
        time.sleep(1)

print(f"\n완료!")
print(f"성공: {success_count}개")
print(f"뒷표지 없음: {not_found_count}개")
print(f"실패: {failed_count}개")
print(f"성공률: {success_count/(success_count+not_found_count+failed_count)*100:.1f}%")
print(f"\n저장 위치: {download_dir}")
