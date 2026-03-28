# Video Processing Pipeline

Pipeline para processar vídeos: detecta rostos, transcrevendo áudio, adiciona legendas, limpa áudio, bota texto na tela. Usa FFmpeg e OpenCV.

## 📦 Instalação

1. **FFmpeg (deve estar no PATH):** 
   - Instale [ffmpeg](https://ffmpeg.org/download.html)
   - Confirme com `ffmpeg -version` no terminal

2. **Dependências Python:**
   ```bash
   python -m venv .venv
   # Apenas Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Modelos de detecção de rostos:**
   - Crie a pasta `face_model/` na raiz do projeto
   - Baixe e coloque lá:
     - [deploy.prototxt](https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/deploy.prototxt)
     - [res10_300x300_ssd_iter_140000.caffemodel](https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel) (~100MB)

---

## 🎯 O que faz

- ✅ Detecção de rostos - localiza e recorta automaticamente
- ✅ Transcrição - converte fala em texto com timestamps (Whisper)
- ✅ Legendas - cria e incorpora automaticamente
- ✅ Limpeza de áudio - remove ruído com filtros FFmpeg
- ✅ Sobreposição de texto - adiciona texto, marcas e créditos
- ✅ Processamento em lote - vários vídeos de uma vez

## 📚 Documentação

### Interface Principal

| Módulo | Descrição |
|--------|----------|
| [main.py](docs/01-main.md) | 🖥️ **Principal:** CLI com subcommands |
| [default.py](docs/10-default.md) | 🔄 Pipeline: processamento individual ou em lote |

### Componentes

| Módulo | Descrição |
|--------|-----------|
| [write.py](docs/02-write.md) | ✍️ Sobreposição de texto |
| [utils.py](docs/03-utils.md) | 🔧 Funções auxiliares |
| [crop.py](docs/04-crop.md) | 👤 Detecção e recorte de rostos |
| [overlay.py](docs/05-overlay.md) | 🎬 Marcas e créditos |
| [subs.py](docs/06-subs.md) | 📝 Legendas automáticas |
| [trim.py](docs/07-trim.md) | ✂️ Recorte temporal |
| [audio.py](docs/08-audio.md) | 🔊 Melhoria de áudio |
| [merge.py](docs/09-merge.md) | 🔗 Merge de comandos |

### Referência

| Documento | Descrição |
|-----------|----------|
| [FFmpeg Ref](docs/11-ffmpeg.md) | 📖 Referência FFmpeg |

---

## 🚀 Como Usar

### Pipeline completo em Python

```python
from default import execute_pipeline

execute_pipeline(
    video="entrada.mp4",
    start_time="00:05",
    end_time="01:30",
    text1="Título e descrição",
    text2="Inscreva-se"
)
```

### CLI com subcommands

```bash
# Detecta e corta para vertical
python main.py crop video.mp4

# Recorta tempo
python main.py trim video.mp4 00:05 00:30

# Transcreve com Whisper
python main.py transcribe video.mp4 --model-name small --device cpu

# Converte JSON para SRT
python main.py srt transcricao.json --max-char 40

# ⚠️ Neste ponto você pode **editar o arquivo .srt** gerado antes de queimar as legendas
# Basta abrir em um editor de texto e fazer ajustes na transcrição

# Queima legendas
python main.py burn video.mp4 legendas.srt --font-size 24

# Melhora áudio
python main.py audio video.mp4 --comp-ratio 2.0

# Adiciona marca d'água
python main.py mark video.mp4 watermark.png --margin-x 20 --margin-y 20

# Adiciona texto
python main.py write video.mp4 "Olá!" --font-size 50 --x "(w-text_w)/2" --y 100

# Gera espectrograma
python main.py spectrum video.mp4 --width 1280 --height 720
```

Veja [main.py](docs/01-main.md) para todos os comandos.

### Processamento em Lote

```bash
# Linha única (padrão)
python default.py "video.mp4|00:05|01:30|Texto um|Legenda"

# Arquivo batch
python default.py -f batch.txt

# Com passo inicial
python default.py "video.mp4|00:05|01:30|Texto um|Legenda" -s 5

# Arquivo batch com passo inicial
python default.py -f batch.txt -s 7
```

Veja [default.py](docs/10-default.md) para detalhes.

### Via código Python

```python
from default import execute_pipeline

execute_pipeline(
    input_video="video.mp4",
    start_time="0:05",
    end_time="1:30",
    text1="Título",
    text2="Descrição"
)
```

---

## 📖 Documentação Completa

```
docs/
├── 01-main.md          CLI principal
├── 02-write.md         Sobreposicao de texto
├── 03-utils.md         Funcoes auxiliares
├── 04-crop.md          Deteccao de rostos
├── 05-overlay.md       Marcas e creditos
├── 06-subs.md          Legendas automaticas
├── 07-trim.md          Recorte temporal
├── 08-audio.md         Melhoria de audio
├── 09-merge.md         Merge de comandos
├── 10-default.md       Pipeline + padrões
└── 11-ffmpeg.md        Referencia FFmpeg
```
