#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import urllib.request
import urllib.parse
import os
import time
from pathlib import Path

class BestsellerCoverScraper:
    def __init__(self, ttb_key, download_dir="bestseller_covers", year=2024):
        """
        한국소설 베스트셀러 표지 이미지 스크래퍼 초기화
        """
        self.ttb_key = ttb_key
        self.year = year
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

        print(f"다운로드 디렉토리: {self.download_dir}")
        print(f"대상 연도: {self.year}년")

    def get_bestsellers(self, max_results=100):
        """
        한국소설 베스트셀러 100위까지 수집
        """
        print(f"{self.year}년 한국소설 베스트셀러 데이터 수집 중...")

        all_books = []

        # 1페이지 (1-50위)
        books_page1 = self._get_bestseller_page(1, 50, year=self.year)
        all_books.extend(books_page1)

        # 2페이지 (51-100위)
        books_page2 = self._get_bestseller_page(51, 50, year=self.year)
        all_books.extend(books_page2)

        # 100위까지만 제한
        bestsellers = all_books[:max_results]

        print(f"총 {len(bestsellers)}개 베스트셀러 수집 완료")
        return bestsellers

    def _get_bestseller_page(self, start, max_results, year=2024):
        """
        베스트셀러 특정 페이지 가져오기
        """
        base_url = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"

        params = {
            'ttbkey': self.ttb_key,
            'QueryType': 'Bestseller',  # 베스트셀러
            'MaxResults': max_results,
            'start': start,
            'SearchTarget': 'Book',
            'output': 'JS',
            'Version': '20131101',
            'Cover': 'Big',
            'CategoryId': 50993  # 한국소설 (2000년대 이후)
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')

            data = json.loads(content)
            books = data.get('item', [])

            print(f"페이지 {start}~{start+max_results-1}: {len(books)}개 수집")
            time.sleep(1)  # API 호출 제한

            return books

        except Exception as e:
            print(f"페이지 {start} 수집 오류: {e}")
            return []

    def download_cover_image(self, cover_url, filename, retry_count=3):
        """
        표지 이미지 다운로드
        """
        if not cover_url:
            print(f"  [!] 표지 URL 없음: {filename}")
            return False

        file_path = self.download_dir / filename

        # 이미 파일이 존재하면 스킵
        if file_path.exists():
            print(f"  [O] 이미 존재: {filename}")
            return True

        for attempt in range(retry_count):
            try:
                with urllib.request.urlopen(cover_url, timeout=30) as response:
                    content = response.read()

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(content)

                print(f"  [O] 다운로드: {filename} ({len(content)} bytes)")
                return True

            except Exception as e:
                print(f"  [X] 시도 {attempt + 1}/{retry_count} 실패: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)

        print(f"  [X] 다운로드 실패: {filename}")
        return False

    def scrape_all_covers(self, bestsellers, delay=0.5):
        """
        모든 베스트셀러 표지 이미지 다운로드
        """
        print(f"\n[*] {len(bestsellers)}개 베스트셀러 표지 이미지 다운로드 시작...")

        success_count = 0
        failed_count = 0

        for i, book in enumerate(bestsellers, 1):
            title = book.get('title', '').strip()
            author = book.get('author', '').strip()
            cover_url = book.get('cover', '')
            isbn13 = book.get('isbn13', '') or book.get('isbn', '') or f"book_{i}"
            rank = book.get('bestRank', i)

            # 안전한 파일명 생성
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()

            if not safe_title:
                safe_title = f"title_{i}"
            if not safe_author:
                safe_author = f"author_{i}"

            # 확장자 추정
            if cover_url:
                parsed_url = urllib.parse.urlparse(cover_url)
                ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            else:
                ext = '.jpg'

            filename = f"{rank:03d}_{isbn13}_{safe_title[:30]}_{safe_author[:20]}{ext}"

            print(f"\n[{i}/100] {rank}위: {title} - {author}")

            # 이미지 다운로드
            if self.download_cover_image(cover_url, filename):
                success_count += 1
            else:
                failed_count += 1

            # 요청 간 대기
            if i < len(bestsellers):
                time.sleep(delay)

        result = {
            'total': len(bestsellers),
            'success': success_count,
            'failed': failed_count
        }

        print(f"\n[*] 다운로드 완료!")
        print(f"총 {result['total']}개 중 성공 {result['success']}개, 실패 {result['failed']}개")

        return result

    def generate_report(self, bestsellers):
        """
        베스트셀러 리포트 생성
        """
        report_file = self.download_dir / "bestseller_report.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.year}년 한국소설 베스트셀러 TOP 100\n")
            f.write("=" * 50 + "\n\n")

            for i, book in enumerate(bestsellers, 1):
                title = book.get('title', '')
                author = book.get('author', '')
                publisher = book.get('publisher', '')
                pubdate = book.get('pubDate', '')
                cover_url = book.get('cover', '')
                isbn13 = book.get('isbn13', '')
                price = book.get('priceSales', 0)
                rank = book.get('bestRank', i)

                f.write(f"{rank:3d}위. {title}\n")
                f.write(f"       저자: {author}\n")
                f.write(f"       출판: {publisher} ({pubdate})\n")
                f.write(f"       가격: {price:,}원\n")
                f.write(f"       ISBN: {isbn13}\n")
                f.write(f"       표지: {cover_url}\n")
                f.write("-" * 50 + "\n")

        print(f"[*] 리포트 저장: {report_file}")


def main():
    """
    메인 실행 함수
    """
    # TTB Key
    TTB_KEY = "ttbsun091252247001"

    # 스크래퍼 초기화 (2024년 연간 베스트셀러)
    scraper = BestsellerCoverScraper(TTB_KEY, download_dir="korean_novel_bestsellers_2024", year=2024)

    # 베스트셀러 100위까지 수집
    bestsellers = scraper.get_bestsellers(max_results=100)

    if not bestsellers:
        print("[X] 베스트셀러 데이터 수집 실패")
        return

    # 리포트 생성
    scraper.generate_report(bestsellers)

    # 표지 이미지 대량 다운로드
    result = scraper.scrape_all_covers(bestsellers, delay=0.5)

    print(f"\n[*] 최종 결과:")
    print(f"  - 총 베스트셀러: {result['total']}개")
    print(f"  - 다운로드 성공: {result['success']}개")
    print(f"  - 다운로드 실패: {result['failed']}개")
    print(f"  - 성공률: {result['success']/result['total']*100:.1f}%")


if __name__ == "__main__":
    main()