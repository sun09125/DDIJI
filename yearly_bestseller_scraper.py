#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from pathlib import Path
from bs4 import BeautifulSoup
import re

class YearlyBestsellerScraper:
    def __init__(self, ttb_key, year=2024, download_dir="yearly_bestsellers"):
        """
        알라딘 연간 베스트셀러 스크래퍼 초기화
        """
        self.ttb_key = ttb_key
        self.year = year
        self.download_dir = Path(f"{download_dir}_{year}")
        self.download_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        print(f"다운로드 디렉토리: {self.download_dir}")
        print(f"대상 연도: {self.year}년 연간 베스트셀러")

    def get_yearly_bestsellers(self, max_results=100):
        """
        알라딘 웹사이트에서 연간 베스트셀러 수집
        """
        print(f"\n{self.year}년 한국소설 연간 베스트셀러 데이터 수집 중...")

        all_books = []

        # 페이지별로 데이터 수집 (한 페이지에 50개씩)
        pages_needed = (max_results + 49) // 50  # 올림 계산

        for page in range(1, pages_needed + 1):
            print(f"\n페이지 {page} 수집 중...")

            url = f"https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=YearlyBest&BranchType=1&Year={self.year}&CID=50917&page={page}"

            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # 베스트셀러 아이템 찾기
                items = soup.select('div.ss_book_box')

                if not items:
                    print(f"  페이지 {page}에서 아이템을 찾을 수 없습니다.")
                    break

                print(f"  {len(items)}개 도서 발견")

                for idx, item in enumerate(items, 1):
                    try:
                        # 순위 추출 (테이블 첫 번째 td에서)
                        rank_text = item.select_one('td')
                        rank = (page - 1) * 50 + idx
                        if rank_text:
                            rank_match = re.search(r'(\d+)\.', rank_text.get_text(strip=True))
                            if rank_match:
                                rank = int(rank_match.group(1))

                        # 제목 추출
                        title_elem = item.select_one('a.bo3')
                        title = title_elem.get_text(strip=True) if title_elem else "제목 없음"
                        # 하이픈 앞의 여분 텍스트 제거 (예: "제목 - 부제" -> "제목")
                        if ' - ' in title:
                            title = title.split(' - ')[0].strip()

                        # 저자/출판사 정보 추출 (ss_book_list 내에서)
                        book_list = item.select_one('div.ss_book_list')
                        author = ""
                        publisher = ""
                        pubdate = ""

                        if book_list:
                            # 저자 정보는 보통 a.bo3 다음의 텍스트에 있음
                            text_content = book_list.get_text(' | ')
                            # 파이프로 분리된 정보에서 추출 시도
                            lines = book_list.find_all(['li', 'span', 'div'])
                            for line in lines:
                                txt = line.get_text(strip=True)
                                if '지은이' in txt or '저자' in txt or '지음' in txt:
                                    author = txt.replace('지은이:', '').replace('저자:', '').replace('지음', '').strip()
                                    break

                        # ItemId 추출 (더 신뢰성 있는 식별자)
                        item_id = item.get('itemid', '')

                        # 링크에서 ItemId 추출
                        isbn13 = item_id  # ItemId를 ISBN 대신 사용
                        link_elem = item.select_one('a')
                        if link_elem and 'href' in link_elem.attrs:
                            href = link_elem['href']
                            itemid_match = re.search(r'ItemId=(\d+)', href)
                            if itemid_match:
                                isbn13 = itemid_match.group(1)

                        # 표지 이미지 URL 추출
                        cover_elem = item.select_one('img.i_cover')
                        cover_url = ""
                        if cover_elem and 'src' in cover_elem.attrs:
                            cover_url = cover_elem['src']
                            # 상대 경로를 절대 경로로 변환
                            if cover_url.startswith('//'):
                                cover_url = 'https:' + cover_url
                            elif cover_url.startswith('/'):
                                cover_url = 'https://www.aladin.co.kr' + cover_url

                        book_info = {
                            'rank': rank,
                            'title': title,
                            'author': author,
                            'isbn13': isbn13,
                            'cover_url': cover_url,
                            'publisher': publisher,
                            'pubdate': pubdate
                        }

                        all_books.append(book_info)

                    except Exception as e:
                        print(f"  아이템 파싱 오류: {e}")
                        continue

                time.sleep(1)  # 서버 부하 방지

            except Exception as e:
                print(f"  페이지 {page} 수집 오류: {e}")
                break

        # 최대 결과 수만큼만 반환
        bestsellers = all_books[:max_results]
        print(f"\n총 {len(bestsellers)}개 베스트셀러 수집 완료")

        return bestsellers

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
                response = self.session.get(cover_url, timeout=30)
                response.raise_for_status()

                # 이미지 파일인지 확인
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"  [!] 이미지가 아닌 파일: {cover_url}")
                    return False

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                print(f"  [O] 다운로드: {filename} ({len(response.content)} bytes)")
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
            cover_url = book.get('cover_url', '')
            isbn13 = book.get('isbn13', '') or f"book_{i}"
            rank = book.get('rank', i)

            # 안전한 파일명 생성
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).strip()

            if not safe_title:
                safe_title = f"title_{i}"
            if not safe_author:
                safe_author = f"author_{i}"

            # 확장자 추정
            ext = '.jpg'
            if cover_url:
                if '.png' in cover_url.lower():
                    ext = '.png'
                elif '.gif' in cover_url.lower():
                    ext = '.gif'

            filename = f"{rank:03d}_{isbn13}_{safe_title[:30]}_{safe_author[:20]}{ext}"

            print(f"\n[{i}/{len(bestsellers)}] {rank}위: {title} - {author}")

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
            f.write(f"{self.year}년 한국소설 연간 베스트셀러 TOP 100\n")
            f.write("=" * 80 + "\n\n")

            for book in bestsellers:
                rank = book.get('rank', 0)
                title = book.get('title', '')
                author = book.get('author', '')
                publisher = book.get('publisher', '')
                pubdate = book.get('pubdate', '')
                isbn13 = book.get('isbn13', '')
                cover_url = book.get('cover_url', '')

                f.write(f"{rank:3d}위. {title}\n")
                f.write(f"       저자: {author}\n")
                f.write(f"       출판: {publisher} ({pubdate})\n")
                f.write(f"       ISBN: {isbn13}\n")
                f.write(f"       표지: {cover_url}\n")
                f.write("-" * 80 + "\n")

        print(f"[*] 리포트 저장: {report_file}")

        # JSON 형식으로도 저장
        json_file = self.download_dir / "bestseller_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(bestsellers, f, ensure_ascii=False, indent=2)
        print(f"[*] JSON 데이터 저장: {json_file}")


def main():
    """
    메인 실행 함수
    """
    # TTB Key
    TTB_KEY = "ttbsun091252247001"

    # 스크래퍼 초기화 (2024년 연간 베스트셀러)
    scraper = YearlyBestsellerScraper(TTB_KEY, year=2024)

    # 베스트셀러 100위까지 수집
    bestsellers = scraper.get_yearly_bestsellers(max_results=100)

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
