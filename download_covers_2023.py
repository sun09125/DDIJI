#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

# JSON 파일 읽기
json_file = Path("yearly_bestsellers_2023/bestseller_data.json")
download_dir = Path("yearly_bestsellers_2023/covers")
download_dir.mkdir(exist_ok=True)

with open(json_file, 'r', encoding='utf-8') as f:
    bestsellers = json.load(f)

print(f"\n{len(bestsellers)}개 베스트셀러 표지 이미지 다운로드 시작...\n")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

success_count = 0
failed_count = 0

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

    filename = f"{rank:03d}_{item_id}_{safe_title[:30]}_{safe_author[:20]}.jpg"
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

    # 웹페이지에서 표지 이미지 URL 찾기
    product_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={item_id}"

    try:
        response = session.get(product_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 표지 이미지 찾기 - 여러 방법 시도
        cover_url = None

        # 방법 1: cover_image 클래스
        cover_img = soup.select_one('img.cover_image')
        if cover_img and cover_img.get('src'):
            cover_url = cover_img['src']

        # 방법 2: prd_img 영역
        if not cover_url:
            prd_img = soup.select_one('div.prd_img img')
            if prd_img and prd_img.get('src'):
                cover_url = prd_img['src']

        # 방법 3: id가 BigImage인 img
        if not cover_url:
            big_img = soup.select_one('img#BigImage')
            if big_img and big_img.get('src'):
                cover_url = big_img['src']

        if not cover_url:
            print(f"[{rank}/100] {title}: 표지 이미지 URL 찾을 수 없음")
            failed_count += 1
            continue

        # 상대 경로를 절대 경로로 변환
        if cover_url.startswith('//'):
            cover_url = 'https:' + cover_url
        elif cover_url.startswith('/'):
            cover_url = 'https://www.aladin.co.kr' + cover_url

        # 고해상도 이미지로 변환 (cover/cover500 등)
        cover_url = cover_url.replace('/cover/', '/cover500/').replace('/cover200/', '/cover500/')

        # 표지 이미지 다운로드
        img_response = session.get(cover_url, timeout=30)
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
print(f"실패: {failed_count}개")
print(f"성공률: {success_count/(success_count+failed_count)*100:.1f}%")
print(f"\n저장 위치: {download_dir}")
