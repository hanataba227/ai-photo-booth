# 🎨 ai-photo-booth

2025 목원대학교 컴퓨터공학과 학술제 부스 - AI 이미지 스타일 변환 서비스

## 📋 프로젝트 개요

축제 방문객의 사진을 AI가 다양한 스타일(레고, 애니메이션, 픽셀아트 등)로 변환해주는 웹 애플리케이션입니다.

### 주요 기능
- 📸 사진 업로드 및 스타일 선택
- 🤖 AI 기반 이미지 스타일 변환 (6가지 스타일)
- 📱 모바일 최적화 UI
- 🖥️ 관리자 대시보드
- 📲 QR 코드를 통한 결과 공유

### 기술 스택
- **Frontend/Backend**: Streamlit 1.39.0
- **Database**: Supabase (PostgreSQL + Storage)
- **AI Engine**: Google Gemini Pro Vision API
- **Image Processing**: Pillow
- **Python**: 3.11
- **출력 규격**: 4cm x 6cm @ 118dpi (472x709px)

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

**설치되는 패키지:**
- streamlit==1.39.0 (웹 프레임워크)
- supabase==2.14.0 (백엔드 서비스)
- google-generativeai==0.8.3 (AI 이미지 생성)
- pillow==10.4.0 (이미지 처리)
- qrcode[pil]==8.0 (QR 코드 생성)
- streamlit-autorefresh==1.0.1 (자동 새로고침)
- python-dotenv==1.0.1 (환경 변수 관리)

### 4. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# App Settings (Optional)
ADMIN_PASSWORD=your_admin_password
```

**API 키 발급 방법:**
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
    style_type TEXT NOT NULL CHECK (style_type IN ('lego', 'anime', 'pixel', 'sapporo', 'cyberpunk', 'clay')),
    input_image_url TEXT NOT NULL,
    output_image_url TEXT,
    error_message TEXT
);

-- 인덱스 생성
CREATE INDEX idx_status_created ON booth_requests(status, created_at);
CREATE INDEX idx_created_at ON booth_requests(created_at DESC);

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

### 6. 프롬프트 테스트 (선택사항)

```bash
# test_images 폴더 생성 및 테스트 이미지 추가
mkdir test_images
# 이미지 파일을 test_images/ 폴더에 넣기

# 프롬프트 테스트 실행
python test_prompts.py
```

### 7. 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저에서 자동으로 열립니다. (기본 주소: http://localhost:8501)

## 📁 프로젝트 구조

```
ai-photo-booth/
├── .streamlit/          # Streamlit 설정
├── pages/               # 관리자 페이지
│   └── Admin.py
├── utils/               # 유틸리티 모듈
│   ├── __init__.py
│   ├── supabase_client.py
│   ├── gemini_client.py
│   ├── image_processor.py
│   └── qr_generator.py
├── assets/              # 이미지 에셋
├── test_images/         # 테스트용 이미지
├── .env                 # 환경 변수 (git ignore)
├── .env.example         # 환경 변수 템플릿
├── .gitignore
├── app.py               # 메인 애플리케이션
├── test_prompts.py      # 프롬프트 테스트 스크립트
├── requirements.txt
├── README.md
└── 개발명세서.md        # 상세 개발 문서
```

## 🎭 스타일 옵션

1. 🧱 **레고 (Lego)** - 레고 블럭으로 만든 세상
2. 🎨 **애니메이션 (Anime)** - 지브리 스타일 애니메이션
3. 🎮 **픽셀아트 (Pixel)** - 레트로 8비트 게임 스타일
4. 🪴 **클레이 (Clay)** - 귀여운 클레이 피규어
5. 👔 **비즈니스 (Business)** - 세련된 스튜디오 프로필 사진
6. 🧸 **피규어 (Figure)** - 책상 위 수집용 피규어

## 📖 사용 방법

### 일반 사용자
1. QR 코드를 스캔하여 웹 페이지 접속
2. 사진 업로드
3. 원하는 스타일 선택
4. 제출 후 부스에서 대기

### 관리자
1. `/Admin` 페이지 접속
2. 대기열에서 요청 확인
3. "생성 시작" 버튼 클릭
4. AI 생성 완료 후 결과 확인
5. QR 코드 제공 및 인쇄

## 🧪 테스트

### 프롬프트 테스트
```bash
python test_prompts.py
```

- 6가지 스타일 프롬프트 확인
- Gemini API 연결 테스트
- 이미지 분석 테스트
- 스타일 변환 테스트 (선택적)

## 🐛 문제 해결

### API 키 오류
- `.env` 파일이 올바른 위치에 있는지 확인
- API 키가 정확히 입력되었는지 확인
- Gemini API 할당량 확인

### Supabase 연결 오류
- Supabase URL과 Key가 올바른지 확인
- 테이블과 Storage Bucket이 생성되었는지 확인
- RLS 정책이 설정되었는지 확인

### 이미지 업로드 실패
- 이미지 파일 크기 확인 (최대 10MB)
- 지원 형식 확인 (JPG, PNG)
- Storage Bucket 권한 확인

## 📚 문서

- [개발명세서.md](./개발명세서.md) - 상세 개발 문서
- [Streamlit 문서](https://docs.streamlit.io/)
- [Supabase 문서](https://supabase.com/docs)
- [Gemini API 문서](https://ai.google.dev/docs)

## 🤝 기여

이슈와 Pull Request를 환영합니다!

## 📝 라이선스

MIT License

## 👥 개발팀

COM-ART 개발팀 - 목원대학교 컴퓨터공학과

---

**프로젝트 시작일**: 2025-11-30  
**축제 일정**: TBD
