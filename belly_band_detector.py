#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
띠지(Belly Band) 검출 및 텍스트 추출 프로그램

띠지의 특징:
1. 가로로 긴 직사각형 영역
2. 배경색이 주변과 다른 경우가 많음
3. 텍스트 밀도가 높음
4. 보통 하단 1/3 또는 중앙에 위치
"""

import cv2
import numpy as np
import easyocr
from pathlib import Path
import json
from datetime import datetime

class BellyBandDetector:
    def __init__(self, use_gpu=True):
        """띠지 검출기 초기화"""
        print("EasyOCR 초기화 중...")
        self.reader = easyocr.Reader(['ko', 'en'], gpu=use_gpu)
        print("초기화 완료!")

    def detect_text_regions(self, image_path):
        """이미지에서 모든 텍스트 영역 검출"""
        image = cv2.imread(str(image_path))
        if image is None:
            return None, []

        # OCR로 텍스트 검출
        results = self.reader.readtext(str(image_path))

        return image, results

    def is_horizontal_band(self, bbox, image_shape):
        """바운딩 박스가 가로 띠 형태인지 판단"""
        # bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        points = np.array(bbox)

        # 너비와 높이 계산
        width = np.linalg.norm(points[1] - points[0])
        height = np.linalg.norm(points[2] - points[1])

        # 가로가 세로보다 충분히 긴지 확인
        if width < height * 2:
            return False

        # 이미지 너비의 일정 비율 이상인지 확인
        img_width = image_shape[1]
        if width < img_width * 0.3:  # 이미지 너비의 30% 이상
            return False

        return True

    def group_nearby_texts(self, results, image_shape, y_threshold=30):
        """가까운 텍스트들을 그룹화하여 띠지 후보 찾기"""
        if not results:
            return []

        # y 좌표 기준으로 정렬
        sorted_results = sorted(results, key=lambda x: np.mean([p[1] for p in x[0]]))

        groups = []
        current_group = [sorted_results[0]]
        current_y = np.mean([p[1] for p in sorted_results[0][0]])

        for result in sorted_results[1:]:
            result_y = np.mean([p[1] for p in result[0]])

            # y 좌표가 비슷하면 같은 그룹
            if abs(result_y - current_y) < y_threshold:
                current_group.append(result)
            else:
                if len(current_group) >= 2:  # 최소 2개 이상의 텍스트
                    groups.append(current_group)
                current_group = [result]
                current_y = result_y

        # 마지막 그룹 추가
        if len(current_group) >= 2:
            groups.append(current_group)

        return groups

    def calculate_group_bbox(self, group):
        """그룹의 전체 바운딩 박스 계산"""
        all_points = []
        for result in group:
            all_points.extend(result[0])

        all_points = np.array(all_points)
        x_min = all_points[:, 0].min()
        y_min = all_points[:, 1].min()
        x_max = all_points[:, 0].max()
        y_max = all_points[:, 1].max()

        return [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]

    def find_belly_band_candidates(self, image, results):
        """띠지 후보 영역 찾기"""
        if not results:
            return []

        # 텍스트 그룹화
        groups = self.group_nearby_texts(results, image.shape)

        candidates = []
        for group in groups:
            # 그룹의 전체 바운딩 박스
            bbox = self.calculate_group_bbox(group)

            # 가로 띠 형태인지 확인
            if self.is_horizontal_band(bbox, image.shape):
                # 그룹의 모든 텍스트 합치기
                text = ' '.join([result[1] for result in group])
                confidence = np.mean([result[2] for result in group])

                candidates.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence,
                    'text_count': len(group),
                    'position': np.mean([p[1] for p in bbox]) / image.shape[0]  # 상대적 y 위치
                })

        return candidates

    def detect_belly_band(self, image_path, visualize=True):
        """띠지 검출 메인 함수"""
        image, results = self.detect_text_regions(image_path)

        if image is None:
            return None

        # 띠지 후보 찾기
        candidates = self.find_belly_band_candidates(image, results)

        if not candidates:
            return {
                'has_belly_band': False,
                'belly_band_text': None,
                'confidence': 0,
                'all_text': [{'text': r[1], 'confidence': r[2]} for r in results]
            }

        # 가장 가능성 높은 띠지 선택 (텍스트 개수와 신뢰도 고려)
        best_candidate = max(candidates,
                           key=lambda x: x['text_count'] * x['confidence'])

        result = {
            'has_belly_band': True,
            'belly_band_text': best_candidate['text'],
            'confidence': best_candidate['confidence'],
            'bbox': best_candidate['bbox'],
            'position': best_candidate['position'],
            'all_candidates': len(candidates),
            'all_text': [{'text': r[1], 'confidence': r[2]} for r in results]
        }

        # 시각화
        if visualize:
            vis_image = image.copy()

            # 띠지 영역 표시
            bbox = np.array(best_candidate['bbox'], dtype=np.int32)
            cv2.polylines(vis_image, [bbox], True, (0, 255, 0), 3)

            # 띠지 텍스트 표시
            y_pos = int(bbox[0][1] - 10)
            cv2.putText(vis_image, f"Belly Band: {best_candidate['text'][:50]}",
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 다른 후보들은 노란색으로
            for candidate in candidates:
                if candidate == best_candidate:
                    continue
                bbox = np.array(candidate['bbox'], dtype=np.int32)
                cv2.polylines(vis_image, [bbox], True, (0, 255, 255), 2)

            result['visualization'] = vis_image

        return result

    def process_directory(self, input_dir, output_dir, file_pattern="*.jpg"):
        """디렉토리 내 모든 이미지 처리"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        image_files = sorted(input_path.glob(file_pattern))

        print(f"\n{len(image_files)}개 이미지 처리 시작...\n")

        results_summary = []
        belly_band_count = 0

        for idx, image_file in enumerate(image_files, 1):
            print(f"[{idx}/{len(image_files)}] {image_file.name}")

            try:
                result = self.detect_belly_band(str(image_file), visualize=True)

                if result is None:
                    print(f"  [!] 이미지 로드 실패")
                    continue

                # 결과 저장
                base_name = image_file.stem

                # JSON 저장
                json_file = output_path / f"{base_name}_belly_band.json"
                save_result = {k: v for k, v in result.items() if k != 'visualization'}
                save_result['timestamp'] = datetime.now().isoformat()
                save_result['image_file'] = image_file.name

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(save_result, f, ensure_ascii=False, indent=2)

                # 시각화 이미지 저장
                if 'visualization' in result:
                    vis_file = output_path / f"{base_name}_belly_band_viz.jpg"
                    cv2.imwrite(str(vis_file), result['visualization'])

                # 텍스트 파일 저장
                txt_file = output_path / f"{base_name}_belly_band.txt"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    if result['has_belly_band']:
                        f.write(f"띠지 발견: {result['belly_band_text']}\n")
                        f.write(f"신뢰도: {result['confidence']:.2f}\n")
                        f.write(f"위치: {result['position']:.1%}\n")
                        belly_band_count += 1
                        print(f"  [O] 띠지: {result['belly_band_text'][:50]}")
                    else:
                        f.write("띠지 없음\n")
                        print(f"  [-] 띠지 없음")

                    f.write(f"\n=== 전체 텍스트 ===\n")
                    for text_info in result['all_text']:
                        f.write(f"{text_info['text']} (신뢰도: {text_info['confidence']:.2f})\n")

                results_summary.append({
                    'file': image_file.name,
                    'has_belly_band': result['has_belly_band'],
                    'text': result['belly_band_text'] if result['has_belly_band'] else None
                })

            except Exception as e:
                print(f"  [X] 오류: {e}")
                continue

        # 전체 요약 저장
        summary_file = output_path / "belly_band_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_images': len(image_files),
                'belly_bands_found': belly_band_count,
                'percentage': belly_band_count / len(image_files) * 100 if image_files else 0,
                'results': results_summary
            }, f, ensure_ascii=False, indent=2)

        print(f"\n완료!")
        print(f"총 {len(image_files)}개 중 {belly_band_count}개 띠지 발견 ({belly_band_count/len(image_files)*100:.1f}%)")
        print(f"결과 저장: {output_path}")

def main():
    """메인 실행 함수"""
    detector = BellyBandDetector(use_gpu=True)

    # 2024년 앞표지 띠지 검출
    print("\n=== 2024년 앞표지 띠지 검출 ===")
    detector.process_directory(
        input_dir="yearly_bestsellers_2024/covers",
        output_dir="yearly_bestsellers_2024/belly_bands",
        file_pattern="*.jpg"
    )

if __name__ == "__main__":
    main()
