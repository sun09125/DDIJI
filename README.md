# DDIJI: 한국소설 띠지/표지 수집 리포지토리

현재 저장소는 알라딘 베스트셀러의 앞/뒷표지와 띠지 이미지를 수집하고 정리하는 스크립트와 데이터 디렉토리만 남겨 두었습니다. OCR 관련 파일은 모두 제거된 상태입니다.

## 주요 디렉토리
- `yearly_bestsellers_2020` ~ `yearly_bestsellers_2024`: 연도별 수집된 표지/뒷표지/띠지 데이터.

## 수집/다운로드 스크립트
- 메타/목록 수집: `bestseller_scraper.py`, `yearly_bestseller_scraper.py`, `aladin.py`
- 앞/뒷표지 다운로드: `download_covers.py`, `download_covers_2023.py`, `download_covers_api_2023.py`, `download_covers_from_product_page_2023.py`, `download_back_covers.py`, `download_back_covers_2023.py`, `download_all_bestsellers.sh`
- 연도별 병합: `collect_year_2023.py`, `collect_all_years.py`
- 기타: `back_cover_scraper.py`, `belly_band_detector.py`(향후 띠지 감지용 스텁)

## 현재 상태
- OCR 관련 스크립트/모델/README는 삭제됨.
- `nul` 0바이트 파일이 여전히 보입니다(Windows 예약 이름). 필요 시 수동 삭제가 필요합니다.

## OCR 재구축을 위한 어노테이션·학습 가이드
1) 어노테이션
- 대상: 표지/뒷표지의 띠지 영역 bbox, 주요 텍스트 영역 bbox(제목/저자/소개 등), 필요 시 클래스 분리.
- 툴: CVAT/Label Studio/Roboflow 등 → YOLO/COCO 포맷으로 익스포트.
- 텍스트 GT: OCR 평가/학습용으로 크롭된 영역별 정답 텍스트를 CSV/JSON으로 별도 저장.

2) 감지 모델 학습(YOLO)
- 데이터: 어노테이션된 bbox를 학습/검증 세트로 분할, 클래스 맵핑(띠지, 텍스트 등) 정의.
- 훈련: YOLOv8/YOLOv5 등으로 finetune, 작은 글자/띠지 검출에 집중(입력 해상도↑, 적절한 anchors, conf/NMS 튜닝).
- 산출물: 새 가중치 파일(예: `weights/band_text_detector.pt`), 추론 스크립트에서 경로 교체.

3) OCR 모델 적용/개선
- 감지 크롭을 EasyOCR/Chandra/Tesseract 등 여러 OCR로 테스트 후, CER/WER로 비교.
- 필요 시 슈퍼해상도/업샘플링·기울기/왜곡 보정 전처리 추가.
- 앙상블: 다중 OCR 결과를 신뢰도/언어모델 기반으로 병합하는 후처리 설계.

4) 평가 자동화
- GT가 있는 소규모 벤치셋으로 mAP(감지)와 CER/WER(OCR)를 정기 측정.
- 리포트: 표/그래프 형태로 비교, 전처리/모델 버전별 로그 유지.

## 사용 예시
```bash
# 연도별 베스트셀러 목록 크롤링 (예시)
python yearly_bestseller_scraper.py

# 앞표지 다운로드 (예시)
python download_covers.py

# 뒷표지 다운로드 (예시)
python download_back_covers.py
```

실제 파라미터와 경로는 각 스크립트 내부 설정에 맞춰 조정하세요.
