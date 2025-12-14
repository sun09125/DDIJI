#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from pathlib import Path

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

    # 알라딘 이미지 URL 패턴을 사용하여 여러 경로 시도
    # ItemId의 앞 자리를 폴더 경로로 사용
    # 예: 321294005 -> product/32129/40/cover500/...

    # ItemId를 8자리 정수로 변환
    item_id_int = int(item_id)

    # 여러 이미지 URL 패턴 시도
    possible_urls = []

    # 패턴 1: /product/{앞5자리}/{다음2자리}/cover500/...
    if len(item_id) >= 7:
        prefix = item_id[:5]
        middle = item_id[5:7]
        possible_urls.append(f"https://image.aladin.co.kr/product/{prefix}/{middle}/cover500/{item_id}_1.jpg")
        possible_urls.append(f"https://image.aladin.co.kr/product/{prefix}/{middle}/cover500/{item_id}_2.jpg")
        possible_urls.append(f"https://image.aladin.co.kr/product/{prefix}/{middle}/cover200/{item_id}_1.jpg")
        possible_urls.append(f"https://image.aladin.co.kr/product/{prefix}/{middle}/cover/{item_id}_1.jpg")

    downloaded = False

    for cover_url in possible_urls:
        try:
            img_response = session.get(cover_url, timeout=10)
            if img_response.status_code == 200 and len(img_response.content) > 1000:  # 최소 1KB 이상
                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(img_response.content)

                print(f"[{rank}/100] {title}: OK ({len(img_response.content)} bytes)")
                success_count += 1
                downloaded = True
                break
        except Exception:
            continue

    if not downloaded:
        print(f"[{rank}/100] {title}: 실패 - 표지 이미지를 찾을 수 없음")
        failed_count += 1

    time.sleep(0.3)  # 서버 부하 방지

print(f"\n완료!")
print(f"성공: {success_count}개")
print(f"실패: {failed_count}개")
if success_count + failed_count > 0:
    print(f"성공률: {success_count/(success_count+failed_count)*100:.1f}%")
print(f"\n저장 위치: {download_dir}")
