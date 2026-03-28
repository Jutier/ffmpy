# Módulo main.py

### Propósito
Interface de linha de comando (CLI) centralizada para executar todos os comandos de processamento de vídeo. Implementa **lazy loading** de módulos para máxima performance.

### Arquitetura

#### Lazy Loading
Em vez de importar todos os módulos no início (OpenCV, Whisper, etc), o `main.py` importa cada módulo **apenas quando necessário**:

```python
# Sem Lazy Loading:
from crop import analyze_video
from subs import transcribe_to_json
from audio import enhance_audio
# ... tudo carregado ao iniciar

# Com Lazy Loading:
if command_name == "crop":
    module = importlib.import_module("crop")
    func = getattr(module, "analyze_video")
    # Carrega SÓ quando necessário
```

**Benefício**: Comandos leves como `write` carregam **quase instantaneamente** sem carregar OpenCV/Whisper.

#### Mapa de Comandos
O `COMMAND_MAP` conecta comando CLI → módulo e função:

```python
COMMAND_MAP = {
    "crop": ("modules.crop", "analyze_video"),
    "trim": ("modules.trim", "trim_video"),
    "transcribe": ("modules.subs", "transcribe_to_json"),
    "srt": ("modules.subs", "json_to_srt"),
    "burn": ("modules.subs", "burn_subtitles_ffmpeg"),
    "mark": ("modules.overlay", "add_mark"),
    "outro": ("modules.overlay", "add_outro"),
    "audio": ("modules.audio", "enhance_audio"),
    "spectrum": ("modules.audio", "generate_spectrum"),
    "write": ("modules.write", "add_text"),
}
```

### Comandos Disponíveis

- **crop** – Detecta e corta para vertical
- **trim** – Corta trechos do vídeo
- **transcribe** – Transcreve com Whisper
- **srt** – Converte transcrição para legendas
- **burn** – Queima legendas no vídeo
- **mark** – Adiciona marca d'água
- **outro** – Adiciona encerramento com fade
- **audio** – Aprimora áudio com filtros
- **spectrum** – Gera visualização de espectro
- **write** – Escreve texto em vídeos

### Flags Globais

- **-h, --help** – Mostra a ajuda geral ou para um comando específico.
- **-t, --time** – Mede tempo de execução

### Processamento de Argumentos

A função `execute_command()` converte argumentos CLI em kwargs para as funções:

```python
def execute_command(args, measure_time=False):
    # 1. Importa módulo sob demanda
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    
    # 2. Converte args → kwargs
    kwargs = {arg: val for arg, val in vars(args).items() 
              if arg not in ['command', 'func', 'time'] and val is not None}
    
    # 3. Trata casos especiais (ex: eq_bands)
    if command_name == "audio" and "eq_bands" in kwargs:
        # Parse "400,1,-5;2500,1,-3" → [(400,1,-5), (2500,1,-3)]
        kwargs["eq_bands"] = parse_eq_bands(kwargs["eq_bands"])
    
    # 4. Executa função
    result = func(**kwargs)
    return result
```
