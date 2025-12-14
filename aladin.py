import requests
import os
import time
from urllib.parse import urlparse, urljoin
from pathlib import Path
import logging

class AladinCoverScraper:
    def __init__(self, ttb_key, download_dir="covers"):
        """
        알라딘 표지 이미지 스크래퍼 초기화

        Args:
            ttb_key (str): 알라딘 API TTB Key
            download_dir (str): 이미지 다운로드 디렉토리
        """
        self.ttb_key = ttb_key
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.base_url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"

        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # 요청 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_books(self, query, max_results=10, query_type="Keyword", search_target="Book",
                     recent_publish_filter=0, category_id=0):
        """
        알라딘 API로 도서 검색

        Args:
            query (str): 검색어
            max_results (int): 최대 결과 수
            query_type (str): 검색 타입 (Keyword, Title, Author, Publisher)
            search_target (str): 검색 대상 (Book, Foreign, Music, DVD, eBook)
            recent_publish_filter (int): 출간일 필터 (0-60, 최근 몇 개월)
            category_id (int): 카테고리 ID

        Returns:
            list: 검색된 도서 정보 리스트
        """
        params = {
            'ttbkey': self.ttb_key,
            'Query': query,
            'QueryType': query_type,
            'MaxResults': min(max_results, 50),  # API 제한: 최대 50개
            'start': 1,
            'SearchTarget': search_target,
            'output': 'JS',  # JSON 형식
            'Version': '20131101',
            'Cover': 'Big'  # 큰 크기 표지 이미지
        }

        # 출간일 필터 추가 (0이 아닌 경우만)
        if recent_publish_filter > 0:
            params['RecentPublishFilter'] = recent_publish_filter

        # 카테고리 ID 추가 (0이 아닌 경우만)
        if category_id > 0:
            params['CategoryId'] = category_id

        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            # JSON 응답 파싱 (JSONP 형식이므로 앞뒤 제거)
            json_text = response.text
            if json_text.startswith('callback(') and json_text.endswith(');'):
                json_text = json_text[9:-2]

            data = response.json() if not json_text else eval(json_text)

            books = []
            if 'item' in data:
                for item in data['item']:
                    book_info = {
                        'title': item.get('title', ''),
                        'author': item.get('author', ''),
                        'isbn': item.get('isbn', ''),
                        'isbn13': item.get('isbn13', ''),
                        'cover_url': item.get('cover', ''),
                        'publisher': item.get('publisher', ''),
                        'pubdate': item.get('pubDate', ''),
                        'link': item.get('link', '')
                    }
                    books.append(book_info)

            self.logger.info(f"검색 완료: {len(books)}개 도서 발견")
            return books

        except Exception as e:
            self.logger.error(f"도서 검색 중 오류 발생: {e}")
            return []

    def download_cover_image(self, cover_url, filename, retry_count=3):
        """
        표지 이미지 다운로드

        Args:
            cover_url (str): 표지 이미지 URL
            filename (str): 저장할 파일명
            retry_count (int): 재시도 횟수

        Returns:
            bool: 다운로드 성공 여부
        """
        if not cover_url:
            self.logger.warning(f"표지 이미지 URL이 없습니다: {filename}")
            return False

        file_path = self.download_dir / filename

        # 이미 파일이 존재하면 스킵
        if file_path.exists():
            self.logger.info(f"파일이 이미 존재합니다: {filename}")
            return True

        for attempt in range(retry_count):
            try:
                response = self.session.get(cover_url, timeout=30)
                response.raise_for_status()

                # 이미지 파일인지 확인
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.logger.warning(f"이미지가 아닌 파일입니다: {cover_url}")
                    return False

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                self.logger.info(f"다운로드 완료: {filename}")
                return True

            except Exception as e:
                self.logger.warning(f"다운로드 시도 {attempt + 1}/{retry_count} 실패: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)  # 재시도 전 대기

        self.logger.error(f"다운로드 실패: {filename}")
        return False

    def scrape_covers(self, query, max_results=10, delay=1, query_type="Keyword",
                      recent_publish_filter=0, category_id=0, target_year=None):
        """
        검색어로 도서를 찾아 표지 이미지 스크래핑

        Args:
            query (str): 검색어
            max_results (int): 최대 결과 수
            delay (float): 요청 간 대기 시간 (초)
            query_type (str): 검색 타입 (Keyword, Title, Author, Publisher)
            recent_publish_filter (int): 출간일 필터 (0-60, 최근 몇 개월)
            category_id (int): 카테고리 ID
            target_year (str): 필터링할 출간 연도 (예: "2018")

        Returns:
            dict: 다운로드 결과 통계
        """
        self.logger.info(f"표지 이미지 스크래핑 시작: '{query}'")

        # 도서 검색
        books = self.search_books(query, max_results, query_type=query_type,
                                  recent_publish_filter=recent_publish_filter,
                                  category_id=category_id)
        if not books:
            self.logger.warning("검색된 도서가 없습니다.")
            return {'total': 0, 'success': 0, 'failed': 0}

        # 특정 연도 필터링
        if target_year:
            filtered_books = []
            for book in books:
                pubdate = book.get('pubdate', '')
                if target_year in pubdate:
                    filtered_books.append(book)
            books = filtered_books
            self.logger.info(f"{target_year}년 필터링 후: {len(books)}개 도서")

        # 표지 이미지 다운로드
        success_count = 0
        failed_count = 0

        for i, book in enumerate(books, 1):
            title = book['title'].strip()
            isbn = book['isbn13'] or book['isbn'] or f"book_{i}"

            # 파일명 생성 (특수문자 제거)
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_title:
                safe_title = f"book_{i}"

            # 확장자 추정
            cover_url = book['cover_url']
            if cover_url:
                parsed_url = urlparse(cover_url)
                ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            else:
                ext = '.jpg'

            filename = f"{isbn}_{safe_title[:50]}{ext}"

            # 이미지 다운로드
            if self.download_cover_image(cover_url, filename):
                success_count += 1
            else:
                failed_count += 1

            # 요청 간 대기
            if i < len(books):
                time.sleep(delay)

        result = {
            'total': len(books),
            'success': success_count,
            'failed': failed_count
        }

        self.logger.info(f"스크래핑 완료: 총 {result['total']}개, 성공 {result['success']}개, 실패 {result['failed']}개")
        return result

    def scrape_by_isbn_list(self, isbn_list, delay=1):
        """
        ISBN 리스트로 표지 이미지 스크래핑

        Args:
            isbn_list (list): ISBN 리스트
            delay (float): 요청 간 대기 시간

        Returns:
            dict: 다운로드 결과 통계
        """
        self.logger.info(f"ISBN 기반 표지 이미지 스크래핑 시작: {len(isbn_list)}개")

        success_count = 0
        failed_count = 0

        for isbn in isbn_list:
            books = self.search_books(isbn, max_results=1, query_type="Keyword")

            if books:
                book = books[0]
                title = book['title'].strip()
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()

                cover_url = book['cover_url']
                if cover_url:
                    ext = os.path.splitext(urlparse(cover_url).path)[1] or '.jpg'
                    filename = f"{isbn}_{safe_title[:50]}{ext}"

                    if self.download_cover_image(cover_url, filename):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    self.logger.warning(f"표지 이미지 URL이 없습니다: {isbn}")
                    failed_count += 1
            else:
                self.logger.warning(f"도서를 찾을 수 없습니다: {isbn}")
                failed_count += 1

            time.sleep(delay)

        result = {
            'total': len(isbn_list),
            'success': success_count,
            'failed': failed_count
        }

        self.logger.info(f"ISBN 기반 스크래핑 완료: 총 {result['total']}개, 성공 {result['success']}개, 실패 {result['failed']}개")
        return result


def main():
    """
    사용 예시
    """
    # TTB Key 설정
    TTB_KEY = "ttbsun091252247001"

    # 스크래퍼 초기화
    scraper = AladinCoverScraper(TTB_KEY, download_dir="book_covers")

    # 문학과지성사의 2018년 한국소설 도서 스크래핑
    # 한국소설 카테고리 ID: 50927 (일반적인 한국소설 분야)
    result = scraper.scrape_covers("문학과지성사", max_results=50, delay=1,
                                   query_type="Publisher", category_id=50927, target_year="2018")
    print(f"문학과지성사 2018년 한국소설 결과: {result}")

    # 카테고리 없이 출판사+연도로도 검색
    result2 = scraper.scrape_covers("문학과지성사", max_results=50, delay=1,
                                    query_type="Publisher", target_year="2018")
    print(f"문학과지성사 2018년 전체 결과: {result2}")


if __name__ == "__main__":
    main()