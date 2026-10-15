// Search synonyms and alternative terms for tools
export const TOOL_SYNONYMS: Record<string, string[]> = {
  // 압축 (Compression)
  '7-zip': ['7zip', '세븐집', '압축', '무료 압축', '알집 대신', 'zip', 'rar'],
  'nanazip': ['나나집', '압축', '알집 대신', 'zip'],
  'peazip': ['피집', '압축', '알집 대신', 'zip', 'rar'],
  
  // 화면 캡처 (Screen Capture)
  'sharex': ['쉐어엑스', '화면 캡처', '캡처', '스크린샷', '알캡처 대신', '녹화'],
  'flameshot': ['플레임샷', '화면 캡처', '캡처', '스크린샷', '알캡처 대신'],
  
  // 이미지 편집 (Image Editing)
  'gimp': ['김프', '포토샵 대신', '사진 편집', '이미지 편집', 'Photoshop', '포토샵'],
  'krita': ['크리타', '그림', '드로잉', '페인팅', '포토샵 대신', '사진 편집'],
  'inkscape': ['잉크스케이프', '일러스트레이터 대신', '벡터', '일러스트', 'Illustrator', '일러'],
  
  // 영상 편집 (Video Editing)
  'opencut': ['오픈컷', 'CapCut 대신', '캡컷 대신', '영상 편집', '비디오 편집', '동영상'],
  'shotcut': ['샷컷', 'CapCut 대신', '캡컷 대신', '영상 편집', '비디오 편집', '동영상'],
  'obs-studio': ['OBS', '녹화', '화면 녹화', '방송', '스트리밍', '반디캠 대신', '오캠 대신'],
  
  // 다이어그램 (Diagram)
  'draw-io': ['드로우아이오', '다이어그램', '순서도', 'Visio 대신', '비지오 대신', '마인드맵', '알마인드 대신'],
  
  // 파일 전송 (File Transfer)
  'localsend': ['로컬센드', '파일 전송', '에어드롭 대신', 'AirDrop', '파일 공유', '카톡 파일'],
  
  // 문서 (Documents)
  'h2orestart': ['한글 필터', 'HWP', '한글', '한컴오피스', '한컴 대신', '문서 편집'],
  'libreoffice': ['리브레오피스', '오피스', '한글', 'HWP', '한컴 대신', '문서 편집'],
  'hop': ['홉', 'HOP', 'HWP', 'HWPX', '한글', '한컴 대신', '한컴오피스'],
  'rhwp': ['rhwp', 'HWP', 'HWPX', '한글', '한컴 대신', '웹 한글'],
};

// App to tool mapping for search
export const APP_TOOL_MAP: Record<string, string[]> = {
  'alzip': ['7-zip', 'nanazip', 'peazip'],
  'alcapture': ['sharex', 'flameshot'],
  'photoshop': ['gimp', 'krita'],
  'illustrator': ['inkscape'],
  'capcut': ['opencut', 'shotcut'],
  'bandicam-ocam': ['obs-studio'],
  'visio-almind': ['draw-io'],
  'file-transfer': ['localsend'],
  'hancom-office': ['hop', 'rhwp', 'h2orestart', 'libreoffice'],
};

// Category to task terms
export const CATEGORY_TASKS: Record<string, string[]> = {
  '영상·오디오': ['영상 편집', '비디오 편집', '동영상', '화면 녹화', '방송', '스트리밍'],
  '이미지·디자인': ['사진 편집', '이미지 편집', '그림', '드로잉', '벡터', '디자인'],
  '문서·오피스': ['문서 편집', '한글', 'HWP', '워드', '오피스'],
  '유틸리티': ['압축', 'zip', '캡처', '스크린샷', '파일 전송'],
};
