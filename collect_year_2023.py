#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from yearly_bestseller_scraper import YearlyBestsellerScraper

def main():
    TTB_KEY = "ttbsun091252247001"

    # 2023년 베스트셀러 수집
    print("=" * 80)
    print("2023년 한국소설 연간 베스트셀러 수집 시작")
    print("=" * 80)

    scraper = YearlyBestsellerScraper(TTB_KEY, year=2023)
    bestsellers = scraper.get_yearly_bestsellers(max_results=100)

    if not bestsellers:
        print("[X] 베스트셀러 데이터 수집 실패")
        return 1

    # 리포트 생성
    scraper.generate_report(bestsellers)

    # 표지 이미지 다운로드
    result = scraper.scrape_all_covers(bestsellers, delay=0.5)

    print(f"\n[*] 2023년 최종 결과:")
    print(f"  - 총 베스트셀러: {result['total']}개")
    print(f"  - 다운로드 성공: {result['success']}개")
    print(f"  - 다운로드 실패: {result['failed']}개")
    print(f"  - 성공률: {result['success']/result['total']*100:.1f}%")

    return 0

if __name__ == "__main__":
    sys.exit(main())
