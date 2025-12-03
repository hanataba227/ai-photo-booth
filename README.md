# 🎨 AI Photo Booth - 인생네컷 스타일

**목원대학교 컴퓨터공학과 | AI 이미지 스타일 변환 서비스**

버전: **2.0.0** (2025-12-03) | 상태: **프로덕션**

---

## 📋 개요

축제 방문객의 사진을 AI가 6가지 스타일로 변환하는 Streamlit 웹앱입니다. **v2.0**부터 "인생네컷 4-cut" 기능이 추가되어 사용자가 선택한 4개 스타일을 2x2 그리드 템플릿으로 합성 제공합니다.

**주요 기능**
- 📸 사진 업로드 & 6가지 스타일 선택
- 🎞️ **인생네컷 4-cut 생성** (v2.0): 4개 스타일을 2x2 그리드로 합성
- ⚡ **병렬 처리**: 4개 이미지 동시 생성으로 75% 시간 단축
- 🖥️ 관리자 대시보드 & QR 코드 공유

**기술 스택**: Streamlit • Supabase • Gemini 2.5 Flash • Pillow • asyncio

---

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/hanataba227/ai-photo-booth.git
cd ai-photo-booth
```

### 2. 가상환경 생성 및 활성화

**⚠️ 중요: Python 3.11.9 (64bit) 필수**

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# App Settings
ADMIN_PASSWORD=your_admin_password
```

**API 키 발급:**
- **Supabase**: https://supabase.com/ 에서 프로젝트 생성
- **Gemini API**: https://makersuite.google.com/app/apikey 에서 발급

### 5. Supabase 데이터베이스 설정

Supabase SQL Editor에서 다음 SQL을 실행하세요:

```sql
-- 테이블 생성
CREATE TABLE booth_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT now(),
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    style_type TEXT CHECK (style_type IN ('lego', 'anime', 'pixel', 'clay', 'business', 'figure')),
    style_types JSONB,  -- 4-cut 기능용 (v2.0)
    input_image_url TEXT NOT NULL,
    output_image_url TEXT,
    error_message TEXT,
    queue_number INTEGER DEFAULT 0
);

-- 인덱스 생성
CREATE INDEX idx_status_created ON booth_requests(status, created_at);
CREATE INDEX idx_created_at ON booth_requests(created_at DESC);
CREATE INDEX idx_queue_number ON booth_requests(queue_number DESC);
CREATE INDEX idx_style_types ON booth_requests USING GIN (style_types);

-- Row Level Security 활성화
ALTER TABLE booth_requests ENABLE ROW LEVEL SECURITY;

-- 정책 설정
CREATE POLICY "Enable read access for all users" ON booth_requests FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON booth_requests FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON booth_requests FOR UPDATE USING (true);
```

**Storage Buckets 생성:**
1. Supabase Dashboard → Storage
2. `input_images` 버킷 생성 (Private)
3. `output_images` 버킷 생성 (Public)

### 6. 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저에서 자동으로 열립니다. (기본 주소: http://localhost:8501)

---

## 🎭 스타일 옵션

1. 🧱 **레고 (Lego)** - 레고 블럭으로 만든 세상
2. 🎨 **애니메이션 (Anime)** - 지브리 스타일 애니메이션
3. 🎮 **픽셀아트 (Pixel)** - 레트로 8비트 게임 스타일
4. 🪴 **클레이 (Clay)** - 귀여운 클레이 피규어
5. 👔 **비즈니스 (Business)** - 세련된 스튜디오 프로필 사진
6. 🧸 **피규어 (Figure)** - 책상 위 수집용 피규어

---

## 📖 사용 방법

### 일반 사용자 (4-cut 모드)
1. QR 코드를 스캔하여 웹 페이지 접속
2. 사진 업로드
3. **원하는 스타일 4개를 순서대로 선택** (인생네컷 스타일)
4. 제출 후 부스에서 대기

### 관리자
1. `/Admin` 페이지 접속
2. 대기열에서 요청 확인
   - 단일 스타일: 1개 이미지 생성
   - 4-cut: 4개 스타일 동시 생성
3. "생성 시작" 버튼 클릭
4. AI 생성 완료 후 결과 확인
   - 4-cut의 경우 2x2 그리드 템플릿으로 자동 합성
5. QR 코드 제공 및 인쇄

### 4-cut 기능 특징
- 정확히 4개의 스타일 선택 필수
- 선택 순서대로 이미지 배치 (좌상 → 우상 → 좌하 → 우하)
- 4개 이미지를 동시에 생성 (약 30-60초 소요)
- 2x2 그리드 템플릿으로 자동 합성 (954x1428px)
- 각 셀은 기존 4x6 비율(472x709px) 유지

---

## 🎞️ 4-CUT 기능 (v2.0)

### 템플릿 레이아웃

```
┌─────────┬─────────┐
│  이미지1  │  이미지2  │  472x709px
│ (Style1)│ (Style2)│
├─────────┼─────────┤  10px 여백
│  이미지3  │  이미지4  │  472x709px
│ (Style3)│ (Style4)│
└─────────┴─────────┘

최종 템플릿: 954x1428px (2x2 그리드)
```

### 주요 개선사항

#### 성능 최적화
- **75% 시간 단축**: 순차 120초 → 병렬 30초
- **asyncio + ThreadPoolExecutor**: 4개 이미지 동시 생성
- **독립적 에러 처리**: 실패한 이미지만 개별 재시도 (최대 3회)

#### 안정성
- 부분 실패 시나리오 대응
- 실패한 스타일 명시적 표시
- 재시도 로직 개선

#### 사용자 경험
- 선택 순서 실시간 표시
- 실시간 선택 개수 검증
- 선택 초기화 버튼

---

## 🚀 배포 가이드

### 기존 프로젝트 업데이트 (v1.0 → v2.0)

#### 1. 데이터베이스 마이그레이션 (필수)

Supabase SQL Editor에서 실행:

```sql
-- style_types JSONB 컬럼 추가
ALTER TABLE booth_requests 
ADD COLUMN IF NOT EXISTS style_types JSONB;

-- 인덱스 추가 (선택적, 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_booth_requests_style_types 
ON booth_requests USING GIN (style_types);

-- 확인
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'booth_requests';
```

#### 2. 코드 업데이트

```bash
git pull origin main
pip install -r requirements.txt  # 의존성 재확인
streamlit run app.py
```

#### 3. 배포 체크리스트

**배포 전:**
- [x] 모든 코드 작성 완료
- [x] 에러 검사 통과
- [ ] Supabase 마이그레이션 실행 ⚠️
- [ ] 실제 환경 테스트 ⚠️

**배포 후 테스트:**
- [ ] 사용자: 4개 스타일 선택 → 제출
- [ ] 관리자: 4-cut 생성 → 템플릿 확인
- [ ] 하위 호환: 단일 스타일 요청도 정상 작동
- [ ] 혼합 대기열: 단일/4-cut 혼합 처리
- [ ] 에러 시나리오: API 실패, 부분 실패 등

### 성능 및 제한사항

**API 사용량:**
- **4-cut 요청 = 4배 API 호출**
- Gemini API 무료 티어: 15 RPM (분당 요청)
- 동시 처리 가능: 최대 3-4개 4-cut 요청 (12-16 API 호출)

**예상 소요 시간:**
- 단일 스타일: 약 30초
- 4-cut (병렬): 약 30-60초
- 4-cut (순차): 약 120초 ❌ 사용 안 함

---

## 🧪 테스트

### 템플릿 생성 테스트 (더미 이미지)

```bash
python test_four_cut_integration.py
# 선택: 2
```

4개의 서로 다른 색상 이미지로 템플릿 생성을 테스트합니다.

### 전체 통합 테스트 (실제 AI 생성)

```bash
python test_four_cut_integration.py
# 선택: 1
```

⚠️ `test_images/` 폴더에 테스트 이미지가 필요합니다.

### 프롬프트 테스트 (기존 기능)

```bash
python test_prompts.py
```

6가지 스타일 프롬프트 및 Gemini API 연결을 테스트합니다.

---

## 📁 프로젝트 구조

```
ai-photo-booth/
├── .streamlit/                  # Streamlit 설정
├── pages/
│   └── Admin.py                # 관리자 대시보드
├── utils/
│   ├── __init__.py
│   ├── supabase_client.py      # Supabase 연동
│   ├── gemini_client.py        # Gemini AI (병렬 생성 포함)
│   ├── image_processor.py      # 이미지 처리 (4-cut 템플릿)
│   └── qr_generator.py         # QR 코드 생성
├── test_images/                # 테스트용 이미지
├── test_results/               # 테스트 결과 저장
├── .env                        # 환경 변수 (git ignore)
├── app.py                      # 메인 애플리케이션
├── test_prompts.py             # 프롬프트 테스트
├── test_four_cut_integration.py # 4-cut 통합 테스트
├── migration_add_style_types.sql # DB 마이그레이션
├── requirements.txt
└── README.md
```

---

## 🔧 기술 구현 상세

### 병렬 생성 (gemini_client.py)

