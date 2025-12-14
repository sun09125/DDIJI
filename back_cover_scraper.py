#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import re
import json
import time
import os

class BackCoverScraper:
    def __init__(self, download_dir="back_covers"):
        """
        뒷표지 이미지 스크래퍼 초기화
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

        # User-Agent 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_product_page_html(self, product_url):
        """
        상품 상세 페이지 HTML 가져오기
        """
        try:
            request = urllib.request.Request(product_url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
            return html
        except Exception as e:
            print(f"페이지 로드 실패: {e}")
            return None

    def extract_additional_images(self, html, book_title=""):
        """
        상품 페이지에서 추가 이미지 URL 추출
        """
        if not html:
            return []

        image_urls = []

        # 다양한 이미지 패턴 검색
        patterns = [
            # 상품 이미지 갤러리
            r'src=["\']([^"\']*product[^"\']*\.jpg)["\']',
            r'src=["\']([^"\']*cover[^"\']*\.jpg)["\']',
            # 미리보기 이미지
            r'data-src=["\']([^"\']*\.jpg)["\']',
            # 이미지 태그 내의 모든 jpg 파일
            r'<img[^>]*src=["\']([^"\']*\.jpg)["\'][^>]*>',
            # 백그라운드 이미지
            r'background-image:\s*url\(["\']?([^"\']*\.jpg)["\']?\)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match not in image_urls and 'aladin.co.kr' in match:
                    image_urls.append(match)

        print(f"  📷 발견된 이미지: {len(image_urls)}개")
        return image_urls

    def download_image(self, image_url, filename):
        """
        이미지 다운로드
        """
        try:
            request = urllib.request.Request(image_url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=15) as response:
                image_data = response.read()

            file_path = os.path.join(self.download_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(image_data)

            print(f"    ✅ 다운로드: {filename} ({len(image_data):,} bytes)")
            return True

        except Exception as e:
            print(f"    ❌ 다운로드 실패: {e}")
            return False

    def scrape_book_images(self, book_info):
        """
        특정 도서의 모든 이미지 수집
        """
        title = book_info.get('title', '').strip()
        author = book_info.get('author', '').strip()
        product_url = book_info.get('link', '')
        isbn13 = book_info.get('isbn13', '') or book_info.get('isbn', '')
        rank = book_info.get('bestRank', 0)

        print(f"\n🔍 [{rank}위] {title} - {author}")
        print(f"  📖 상품 페이지: {product_url}")

        if not product_url:
            print("  ⚠️  상품 URL이 없습니다.")
            return 0

        # 상품 페이지 HTML 가져오기
        html = self.get_product_page_html(product_url)
        if not html:
            return 0

        # 추가 이미지 URL 추출
        image_urls = self.extract_additional_images(html, title)

        if not image_urls:
            print("  ⚠️  추가 이미지를 찾을 수 없습니다.")
            return 0

        # 파일명 생성용 안전한 문자열
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
        safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()[:15]

        download_count = 0

        # 각 이미지 다운로드
        for i, img_url in enumerate(image_urls[:5], 1):  # 최대 5개까지만
            # 절대 URL로 변환
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = 'https://www.aladin.co.kr' + img_url
            elif not img_url.startswith('http'):
                continue

            filename = f"{rank:03d}_{isbn13}_{safe_title}_{safe_author}_img{i}.jpg"

            if self.download_image(img_url, filename):
                download_count += 1

            time.sleep(0.5)  # 요청 간 대기

        return download_count


def test_back_cover_scraping():
    """
    뒷표지 스크래핑 테스트 (TOP 3 베스트셀러)
    """
    # 테스트용 베스트셀러 정보
    test_books = [
        {
            'title': '절창',
            'author': '구병모',
            'link': 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=371723601',
            'isbn13': '9791141602451',
            'bestRank': 1
        },
        {
            'title': '아무도 오지 않는 곳에서',
            'author': '천선란',
            'link': 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=374258051',
            'isbn13': '9791193078709',
            'bestRank': 2
        },
        {
            'title': '혼모노',
            'author': '성해나',
            'link': 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=361016676',
            'isbn13': '9788936439743',
            'bestRank': 3
        }
    ]

    scraper = BackCoverScraper("back_covers_test")

    print("🔍 뒷표지 및 추가 이미지 스크래핑 테스트")
    print("=" * 50)

    total_images = 0

    for book in test_books:
        images_downloaded = scraper.scrape_book_images(book)
        total_images += images_downloaded
        time.sleep(2)  # 페이지 간 대기

    print(f"\n🎉 테스트 완료! 총 {total_images}개 추가 이미지 다운로드")


if __name__ == "__main__":
    test_back_cover_scraping()