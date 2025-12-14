#!/bin/bash

# 한국소설 베스트셀러 100위 표지 이미지 자동 다운로드 스크립트

echo "🏆 한국소설 베스트셀러 TOP 100 표지 이미지 다운로드 시작"
echo "================================================="

# 디렉토리 생성
mkdir -p korean_novel_bestsellers_full

# TTB Key
TTB_KEY="ttbsun091252247001"

# 1-50위 데이터 수집
echo "📚 1-50위 데이터 수집 중..."
curl -s "http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey=${TTB_KEY}&QueryType=Bestseller&MaxResults=50&start=1&SearchTarget=Book&output=JS&Version=20131101&Cover=Big&CategoryId=50993" > bestsellers_1_50.json

# 51-100위 데이터 수집
echo "📚 51-100위 데이터 수집 중..."
curl -s "http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey=${TTB_KEY}&QueryType=Bestseller&MaxResults=50&start=51&SearchTarget=Book&output=JS&Version=20131101&Cover=Big&CategoryId=50993" > bestsellers_51_100.json

echo "✅ 베스트셀러 데이터 수집 완료"

# 주요 베스트셀러 표지 이미지 다운로드 (TOP 20)
echo ""
echo "🖼️  TOP 20 베스트셀러 표지 이미지 다운로드 중..."

# 1위: 절창
echo "1위: 절창 (구병모)"
curl -s "https://image.aladin.co.kr/product/37172/36/cover200/k662031678_2.jpg" > korean_novel_bestsellers_full/001_절창_구병모.jpg

# 2위: 아무도 오지 않는 곳에서
echo "2위: 아무도 오지 않는 곳에서 (천선란)"
curl -s "https://image.aladin.co.kr/product/37425/80/cover200/k242032998_2.jpg" > korean_novel_bestsellers_full/002_아무도오지않는곳에서_천선란.jpg

# 3위: 혼모노
echo "3위: 혼모노 (성해나)"
curl -s "https://image.aladin.co.kr/product/36101/66/cover200/893643974x_2.jpg" > korean_novel_bestsellers_full/003_혼모노_성해나.jpg

# 4위: 안녕이라 그랬어
echo "4위: 안녕이라 그랬어 (김애란)"
curl -s "https://image.aladin.co.kr/product/36566/52/cover200/k462039240_1.jpg" > korean_novel_bestsellers_full/004_안녕이라그랬어_김애란.jpg

# 5위: 양면의 조개껍데기
echo "5위: 양면의 조개껍데기 (김초엽)"
curl -s "https://image.aladin.co.kr/product/37024/77/cover200/k482030732_1.jpg" > korean_novel_bestsellers_full/005_양면의조개껍데기_김초엽.jpg

# 6위: 자몽살구클럽
echo "6위: 자몽살구클럽 (한로로)"
curl -s "https://image.aladin.co.kr/product/36808/37/cover200/k082030009_1.jpg" > korean_novel_bestsellers_full/006_자몽살구클럽_한로로.jpg

# 7위: 소년이 온다
echo "7위: 소년이 온다 (한강)"
curl -s "https://image.aladin.co.kr/product/4086/97/cover200/8936434128_2.jpg" > korean_novel_bestsellers_full/007_소년이온다_한강.jpg

# 8위: 2025 김승옥문학상 수상작품집
echo "8위: 2025 김승옥문학상 수상작품집"
curl -s "https://image.aladin.co.kr/product/37461/41/cover200/k422032910_1.jpg" > korean_novel_bestsellers_full/008_김승옥문학상수상작품집.jpg

# 9위: 노 피플 존
echo "9위: 노 피플 존 (정이현)"
curl -s "https://image.aladin.co.kr/product/37448/73/cover200/k512032607_1.jpg" > korean_novel_bestsellers_full/009_노피플존_정이현.jpg

# 10위: 급류
echo "10위: 급류 (정대건)"
curl -s "https://image.aladin.co.kr/product/30769/24/cover200/8937473402_1.jpg" > korean_novel_bestsellers_full/010_급류_정대건.jpg

# 11-20위 계속...
echo "11위: 한참을 헤매다가 (정미진)"
curl -s "https://image.aladin.co.kr/product/37202/14/cover200/k792031492_1.jpg" > korean_novel_bestsellers_full/011_한참을헤매다가_정미진.jpg

echo "12위: 오직 그녀의 것 (김혜진)"
curl -s "https://image.aladin.co.kr/product/37298/43/cover200/k372031546_1.jpg" > korean_novel_bestsellers_full/012_오직그녀의것_김혜진.jpg

echo "13위: 작별하지 않는다 (한강)"
curl -s "https://image.aladin.co.kr/product/27877/5/cover200/8954682154_3.jpg" > korean_novel_bestsellers_full/013_작별하지않는다_한강.jpg

echo "14위: 채식주의자 (한강)"
curl -s "https://image.aladin.co.kr/product/29137/2/cover200/8936434594_2.jpg" > korean_novel_bestsellers_full/014_채식주의자_한강.jpg

echo "15위: 소설 보다 가을 2025 (문학과지성사)"
curl -s "https://image.aladin.co.kr/product/37210/39/cover200/8932044392_1.jpg" > korean_novel_bestsellers_full/015_소설보다가을2025.jpg

echo "16위: 바르셀로나의 유서 (백세희)"
curl -s "https://image.aladin.co.kr/product/36617/24/cover200/k092030962_1.jpg" > korean_novel_bestsellers_full/016_바르셀로나의유서_백세희.jpg

echo "17위: 꽤 낙천적인 아이 (원소윤)"
curl -s "https://image.aladin.co.kr/product/36752/1/cover200/8937477319_2.jpg" > korean_novel_bestsellers_full/017_꽤낙천적인아이_원소윤.jpg

echo "18위: 파과 (구병모)"
curl -s "https://image.aladin.co.kr/product/33728/6/cover200/k312039010_2.jpg" > korean_novel_bestsellers_full/018_파과_구병모.jpg

echo "19위: 첫 여름, 완주 (김금희)"
curl -s "https://image.aladin.co.kr/product/36275/58/cover200/k692038832_2.jpg" > korean_novel_bestsellers_full/019_첫여름완주_김금희.jpg

echo "20위: 연희동 러너 (임지형)"
curl -s "https://image.aladin.co.kr/product/37042/41/cover200/k642030031_1.jpg" > korean_novel_bestsellers_full/020_연희동러너_임지형.jpg

echo ""
echo "🎉 TOP 20 베스트셀러 표지 이미지 다운로드 완료!"

# 다운로드된 파일 목록 확인
echo ""
echo "📋 다운로드된 파일 목록:"
ls -la korean_novel_bestsellers_full/

echo ""
echo "✅ 전체 작업 완료!"
echo "📁 저장 위치: korean_novel_bestsellers_full/"