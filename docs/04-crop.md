# Módulo crop.py

### Propósito
Deteta e recorta rostos em vídeos usando rede neural DeepFace. Utiliza modelo SSD pré-treinado para localizar faces com alta precisão.

### Dependências
- `cv2` (OpenCV)
- `numpy`
- Modelo pré-treinado em `face_model/`

---

### Funções Principais

#### `load_model()`

**Descrição**: Carrega a rede neural pré-treinada (SSD) a partir dos arquivos no diretório `face_model/`.

**Arquivos Necessários**:
- `face_model/deploy.prototxt` - Arquitetura da rede
- `face_model/res10_300x300_ssd_iter_140000.caffemodel` - Pesos treinados (~100MB)

**Retorna**: `cv2.dnn.Net` - Rede carregada pronta para inferência

---

#### `detect_faces(frame, net, threshold=0.7)`

**Descrição**: Detecta todas as faces em um frame único usando a rede neural SSD.

**Parâmetros**:
- `frame` (ndarray): Frame (imagem) em formato BGR (OpenCV padrão)
- `net` (cv2.dnn.Net): Rede neural carregada por `load_model()`
- `threshold` (float): Mínimo de confiança da detecção (0-1) (padrão: 0.7)

**Retorna**: `list` - Lista de faces no formato: `[(x, y, width, height, confidence), ...]`
- `x, y`: Coordenadas do canto superior esquerdo
- `width, height`: Dimensões do bounding box
- `confidence`: Confiança da detecção (0-1)

**Exemplo**:
```python
import cv2
net = load_model()
frame = cv2.imread("frame.jpg")
faces = detect_faces(frame, net, threshold=0.7)
# [(50, 100, 150, 200, 0.95), (400, 150, 150, 200, 0.88)]
```

---

#### `collect_face_positions(video_path, net, sample_rate=30)`

**Descrição**: Analisa um vídeo e coleta a posição de todos os rostos detectados (com sampling).

**Parâmetros**:
- `video_path` (str): Caminho do vídeo
- `net` (cv2.dnn.Net): Rede de detecção carregada por `load_model()`
- `sample_rate` (int): Processa 1 frame a cada N frames (padrão: 30)

**Comportamento**:
1. Abre o vídeo
2. Processa frames a cada `sample_rate` frames
3. Detecta faces em cada frame processado
4. Seleciona o maior rosto (apresentador)
5. Armazena o centro do rosto: `(center_x, center_y)`

**Retorna**: `list` - Lista de posições (x, y) do centro do maior rosto em cada frame analisado

**Tempo de Execução**: ~1-2 minutos para vídeo de 5 min em CPU

**Exemplo**:
```python
net = load_model()
centers = collect_face_positions("video.mp4", net, sample_rate=15)
# [(960, 540), (965, 545), (955, 535), ...]
```

---

#### `compute_crop_region(centers, frame_width, frame_height, aspect_ratio=9/16)`

**Descrição**: Calcula a maior região de corte que cabe no frame mantendo o aspect ratio especificado e centralizado nos rostos.

**Parâmetros**:
- `centers` (list): Posições (x, y) do centro dos rostos (retorno de `collect_face_positions`)
- `frame_width` (int): Largura do vídeo em pixels
- `frame_height` (int): Altura do vídeo em pixels
- `aspect_ratio` (float): Proporção largura/altura (padrão: 9/16 para vertical)

**Lógica**:
1. Calcula o maior tamanho que cabe no frame mantendo o aspect ratio
2. Encontra a posição mediana de todos os rostos (robusta a outliers)
3. Centraliza a região de corte nessa posição
4. Garante que a região fica completamente dentro do vídeo

**Retorna**: `tuple` - `(x_inicial, y_inicial, largura_corte, altura_corte)`

**Exemplo**:
```python
centers = collect_face_positions("video.mp4", net)
# [(960, 540), (965, 545), (950, 535), ...]

region = compute_crop_region(centers, 1920, 1080, aspect_ratio=9/16)
# (405, 0, 1080, 1920)  # x, y, width, height (9:16 para vertical)
```

---

#### `crop_video_ffmpeg(input_video, output_video, crop_x, crop_y, crop_width, crop_height, scale="1080x1920", dry_run=False)`

**Descrição**: Aplica o corte no vídeo usando FFmpeg com os filtros crop e scale.

**Parâmetros**:
- `input_video` (str): Caminho do arquivo de vídeo de entrada
- `output_video` (str): Caminho do arquivo de vídeo de saída
- `crop_x` (int): Coordenada X inicial do corte em pixels
- `crop_y` (int): Coordenada Y inicial do corte em pixels
- `crop_width` (int): Largura do corte em pixels
- `crop_height` (int): Altura do corte em pixels
- `scale` (str): Resolução de saída no formato "widthxheight" (padrão: "1080x1920")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_video, cmd_list)

**Comando FFmpeg Utilizado**:
```
ffmpeg -y -i input.mp4 -vf "crop=1080:1920:270:0,scale=1080x1920" -c:a copy output_cropped.mp4
```

**Exemplo**:
```python
crop_video_ffmpeg(
    input_video="video.mp4",
    output_video="video_cropped.mp4",
    crop_x=420,
    crop_y=0,
    crop_width=1080,
    crop_height=1920,
    scale="1080x1920"
)
```

---

#### `analyze_video(video_path, output_dir="crop_output", sample_rate=30, aspect_ratio=9/16, scale="1080x1920", dry_run=False)`

**Descrição**: Pipeline completo automatizado: detecta rostos → calcula região de corte → aplica corte no vídeo.

**Parâmetros**:
- `video_path` (str): Caminho do vídeo de entrada
- `output_dir` (str): Diretório de saída (padrão: "crop_output")
- `sample_rate` (int): Processa 1 frame a cada N frames (padrão: 30)
- `aspect_ratio` (float): Proporção do corte (padrão: 9/16 para vertical)
- `scale` (str): Resolução de saída no formato "widthxheight" (padrão: "1080x1920")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_video, cmd_list)

**Processo Interno**:
1. Carrega modelo de detecção SSD
2. Coleta posições de rostos com sampling
3. Calcula região de corte com aspect ratio
4. Aplica corte e scale usando FFmpeg
5. Retorna caminho do vídeo processado

**Arquivo de Saída**: `{nome_video}_crop.mp4`

**Estrutura de Saída**:
```
output_dir/
└── video_crop.mp4        # Vídeo recortado e escalado
```

**Exemplos**:
```python
# Corte automático com configuração padrão (9:16 vertical)
analyze_video("video.mp4")

# Corte customizado (16:9 horizontal)
analyze_video("video.mp4", aspect_ratio=16/9, scale="1920x1080")

# Mais frames analisados (mais lento aber mais preciso)
analyze_video("video.mp4", sample_rate=10)

# Dry-run
analyze_video("video.mp4", dry_run=True)
```

**Tempo de Execução**: ~2-5 minutos para vídeo 5min (depende do sample_rate)

**Casos de Uso**:
- Converter vídeos horizontais para vertical (mobile)
- Focar em apresentador
- Padronizar resoluções para rede social

**Limitações**:
- Requer faces claramente visíveis no vídeo
- Funca melhor com iluminação adequada
- Apresentador deve estar relativamente imóvel
- `margin_percent` (float): Margem percentual (padrão: 0.2)

**Retorna**: `tuple` - `(crop_x, crop_y, crop_width, crop_height)` pronto para `crop_video_ffmpeg()`

**Exemplo**:
```python
crop_x, crop_y, crop_w, crop_h = analyze_video("video.mp4")
crop_video_ffmpeg("video.mp4", "video_cropped.mp4", crop_x, crop_y, crop_w, crop_h)
```

---

### Fluxo Típico

```python
from crop import load_model, analyze_video, crop_video_ffmpeg

# Passo 1: Detectar e calcular région
net = load_model()
crop_x, crop_y, crop_w, crop_h = analyze_video("input.mp4", net)

# Passo 2: Aplicar corte
crop_video_ffmpeg("input.mp4", "output_cropped.mp4", crop_x, crop_y, crop_w, crop_h)
```
