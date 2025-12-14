#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from pathlib import Path
from bs4 import BeautifulSoup
import re

def collect_year_data(year):
    """특정 연도의 베스트셀러 데이터 수집 및 이미지 다운로드"""

    print(f"\n{'='*80}")
    print(f"{year}년 한국소설 연간 베스트셀러 수집 시작")
    print(f"{'='*80}\n")

    download_dir = Path(f"yearly_bestsellers_{year}")
    covers_dir = download_dir / "covers"
    back_covers_dir = download_dir / "back_covers"
    covers_dir.mkdir(parents=True, exist_ok=True)
    back_covers_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # 1단계: 베스트셀러 목록 수집
    print(f"[1/3] 베스트셀러 목록 수집 중...")
    all_books = []

    for page in range(1, 3):  # 2페이지 (100개)
        url = f"https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=YearlyBest&BranchType=1&Year={year}&CID=50917&page={page}"

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('div.ss_book_box')

            for idx, item in enumerate(items, 1):
                try:
                    rank = (page - 1) * 50 + idx

                    title_elem = item.select_one('a.bo3')
                    title = title_elem.get_text(strip=True) if title_elem else "제목 없음"
                    if ' - ' in title:
                        title = title.split(' - ')[0].strip()

                    book_list = item.select_one('div.ss_book_list')
                    author = ""
                    if book_list:
                        lines = book_list.find_all(['li', 'span', 'div'])
                        for line in lines:
                            txt = line.get_text(strip=True)
                            if '지은이' in txt or '저자' in txt or '지음' in txt:
                                author = txt.replace('지은이:', '').replace('저자:', '').replace('지음', '').strip()
                                break

                    item_id = item.get('itemid', '')
                    link_elem = item.select_one('a')
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        itemid_match = re.search(r'ItemId=(\d+)', href)
                        if itemid_match:
                            item_id = itemid_match.group(1)

                    cover_elem = item.select_one('img.i_cover')
                    cover_url = ""
                    if cover_elem and 'src' in cover_elem.attrs:
                        cover_url = cover_elem['src']
                        if cover_url.startswith('//'):
                            cover_url = 'https:' + cover_url
                        elif cover_url.startswith('/'):
                            cover_url = 'https://www.aladin.co.kr' + cover_url

                    book_info = {
                        'rank': rank,
                        'title': title,
                        'author': author,
                        'isbn13': item_id,
                        'cover_url': cover_url,
                        'publisher': "",
                        'pubdate': ""
                    }

                    all_books.append(book_info)

                except Exception as e:
                    print(f"  아이템 파싱 오류: {e}")
                    continue

            time.sleep(1)

        except Exception as e:
            print(f"  페이지 {page} 수집 오류: {e}")
            break

    print(f"  총 {len(all_books)}개 베스트셀러 수집 완료")

    # JSON 저장
    json_file = covers_dir / "bestseller_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, ensure_ascii=False, indent=2)

    # 2단계: 앞표지 다운로드
    print(f"\n[2/3] 앞표지 이미지 다운로드 중...")
    front_success = 0
    front_failed = 0

    for book in all_books:
        rank = book['rank']
        title = book['title']
        author = book.get('author', '').split('|')[0].strip()
        item_id = book.get('isbn13', '') or f"book_{rank}"

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()[:20]

        if not safe_title:
            safe_title = f"title_{rank}"
        if not safe_author:
            safe_author = f"author_{rank}"

        filename = f"{rank:03d}_{item_id}_{safe_title}_{safe_author}.jpg"
        file_path = covers_dir / filename

        if file_path.exists():
            front_success += 1
            continue

        if not item_id or item_id.startswith('book_'):
            front_failed += 1
            continue

        # 상품 페이지에서 표지 추출
        product_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={item_id}"

        try:
            response = session.get(product_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            cover_url = None
            images = soup.find_all('img')
            for img in images:
                src = img.get('src', '')
                if 'letslook' in src and '_f.jpg' in src:
                    cover_url = src
                    break

            if not cover_url:
                for img in images:
                    src = img.get('src', '')
                    if 'cover500' in src or '/cover/' in src:
                        cover_url = src.replace('cover200', 'cover500') if 'cover200' in src else src
                        break

            if not cover_url:
                api_cover = book.get('cover_url', '')
                if api_cover:
                    cover_url = api_cover.replace('cover200', 'cover500')

            if not cover_url:
                front_failed += 1
                continue

            if cover_url.startswith('//'):
                cover_url = 'https:' + cover_url
            elif cover_url.startswith('/'):
                cover_url = 'https://www.aladin.co.kr' + cover_url

            img_response = session.get(cover_url, timeout=30)
            img_response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(img_response.content)

            front_success += 1
            time.sleep(0.5)

        except Exception:
            front_failed += 1
            time.sleep(1)

    print(f"  앞표지 다운로드: 성공 {front_success}개, 실패 {front_failed}개")

    # 3단계: 뒷표지 다운로드
    print(f"\n[3/3] 뒷표지 이미지 다운로드 중...")
    back_success = 0
    back_failed = 0
    back_not_found = 0

    for book in all_books:
        rank = book['rank']
        title = book['title']
        author = book.get('author', '').split('|')[0].strip()
        item_id = book.get('isbn13', '') or f"book_{rank}"

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()[:20]

        if not safe_title:
            safe_title = f"title_{rank}"
        if not safe_author:
            safe_author = f"author_{rank}"

        filename = f"{rank:03d}_{item_id}_{safe_title}_{safe_author}_back.jpg"
        file_path = back_covers_dir / filename

        if file_path.exists():
            back_success += 1
            continue

        if not item_id or item_id.startswith('book_'):
            back_failed += 1
            continue

        product_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={item_id}"

        try:
            response = session.get(product_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            back_cover_url = None
            images = soup.find_all('img')
            for img in images:
                src = img.get('src', '')
                if 'letslook' in src and '_b.jpg' in src:
                    back_cover_url = src
                    break

            if not back_cover_url:
                back_not_found += 1
                continue

            if back_cover_url.startswith('//'):
                back_cover_url = 'https:' + back_cover_url
            elif back_cover_url.startswith('/'):
                back_cover_url = 'https://www.aladin.co.kr' + back_cover_url

            img_response = session.get(back_cover_url, timeout=30)
            img_response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(img_response.content)

            back_success += 1
            time.sleep(0.5)

        except Exception:
            back_failed += 1
            time.sleep(1)

    print(f"  뒷표지 다운로드: 성공 {back_success}개, 뒷표지 없음 {back_not_found}개, 실패 {back_failed}개")

    print(f"\n{year}년 수집 완료!")
    print(f"  - 앞표지: {front_success}/{len(all_books)}")
    print(f"  - 뒷표지: {back_success}/{len(all_books)}")
    return {
        'year': year,
        'total': len(all_books),
        'front_success': front_success,
        'back_success': back_success
    }

def main():
    """2022, 2021, 2020년 순차 수집"""
    years = [2022, 2021, 2020]
    results = []

    for year in years:
        result = collect_year_data(year)
        results.append(result)
        print(f"\n다음 연도로 이동...\n")
        time.sleep(2)

    # 최종 요약
    print(f"\n{'='*80}")
    print("전체 수집 완료!")
    print(f"{'='*80}\n")
    for result in results:
        print(f"{result['year']}년: 앞표지 {result['front_success']}/{result['total']}, 뒷표지 {result['back_success']}/{result['total']}")

if __name__ == "__main__":
    main()
