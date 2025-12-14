#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from pathlib import Path

# JSON 파일 읽기
json_file = Path("yearly_bestsellers_2024/bestseller_data.json")
download_dir = Path("yearly_bestsellers_2024")

with open(json_file, 'r', encoding='utf-8') as f:
    bestsellers = json.load(f)

print(f"\n{len(bestsellers)}개 베스트셀러 표지 이미지 다운로드 시작...\n")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0'
})

success_count = 0
failed_count = 0

for book in bestsellers:
    rank = book.get('rank', 0)
    title = book.get('title', '')
    author = book.get('author', '').split('|')[0].strip()  # 저자 부분만 추출
    cover_url = book.get('cover_url', '')
    isbn13 = book.get('isbn13', '') or f"book_{rank}"

    # 안전한 파일명 생성
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()

    if not safe_title:
        safe_title = f"title_{rank}"
    if not safe_author:
        safe_author = f"author_{rank}"

    # 확장자 추정
    ext = '.jpg'
    if cover_url:
        if '.png' in cover_url.lower():
            ext = '.png'
        elif '.gif' in cover_url.lower():
            ext = '.gif'

    filename = f"{rank:03d}_{isbn13}_{safe_title[:30]}_{safe_author[:20]}{ext}"
    file_path = download_dir / filename

    # 이미 파일이 존재하면 스킵
    if file_path.exists():
        print(f"[{rank}/100] {title}: 이미 존재")
        success_count += 1
        continue

    if not cover_url:
        print(f"[{rank}/100] {title}: 표지 URL 없음")
        failed_count += 1
        continue

    # 이미지 다운로드
    try:
        response = session.get(cover_url, timeout=30)
        response.raise_for_status()

        # 파일 저장
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"[{rank}/100] {title}: OK ({len(response.content)} bytes)")
        success_count += 1
        time.sleep(0.3)  # 서버 부하 방지

    except Exception as e:
        print(f"[{rank}/100] {title}: 실패 - {e}")
        failed_count += 1

print(f"\n완료!")
print(f"성공: {success_count}개")
print(f"실패: {failed_count}개")
print(f"성공률: {success_count/len(bestsellers)*100:.1f}%")
