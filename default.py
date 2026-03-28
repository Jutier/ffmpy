"""
default.py - Pipeline de processamento de vídeo com padrões pré-definidos.

USO:
  Python:  from default import execute_pipeline
           execute_pipeline("video.mp4", "00:05", "01:30", "Texto 1", "Texto 2")

  CLI (linha única):     python default.py "video.mp4|00:05|01:30|Texto 1|Texto 2"
  CLI (arquivo batch):   python default.py -f batch.txt
  CLI (com passo):       python default.py "video.mp4|00:05|01:30|Texto 1|Texto 2" -s 5

FORMATO:
  video|start_time|end_time|text1|text2
  - times: MM:SS ou HH:MM:SS
  - flags: -f (arquivo), -s (passo inicial 1-9)
"""

import logging
from pathlib import Path
from modules.trim import trim_video
from modules.crop import analyze_video
from modules.audio import enhance_audio
from modules.subs import transcribe_to_json, json_to_srt, burn_subtitles_ffmpeg
from modules.overlay import add_mark, add_outro
from modules.write import add_text
from modules.merge import merge_mark, merge_write
from modules.utils import run_ffmpeg, split_text_by_char_limit, get_video_info
from modules.logs import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

# ==================== GLOBAL CONFIGURATION ====================
# Transcription
TRANSCRIPTION_MODEL = "large"
TRANSCRIPTION_LANGUAGE = "pt"
MAX_CHARS_PER_LINE = 25

# Assets paths
INSTA_MARK_PATH = "../assets/insta-mark.png"
IF_MARK_PATH = "../assets/if-mark.png"
OUTRO_PATH = "../assets/outro.mp4"

# Marks positioning
MARK_MARGIN_X = 30
MARK_MARGIN_Y = 30

# Text1 styling (topo)
TEXT1_CHAR_LIMIT = 22
TEXT1_FONT_COLOR = "#06d6a0"
TEXT1_FONT = "Oswald-Medium"
TEXT1_FONT_DIR = "fonts"
TEXT1_FONT_SIZE = 90
TEXT1_Y_TOP = 460
TEXT1_Y_BOTTOM = 570

# Text2 styling (baixo)
TEXT2_FONT_COLOR = "#ef476f"
TEXT2_FONT = "Comfortaa-Medium"
TEXT2_FONT_DIR = "fonts"
TEXT2_FONT_SIZE = 70
TEXT2_Y = 770
TEXT2_START_OFFSET = 1  # Antes do fim, após Trim, sem Outro

# Subtitles styling
SUBTITLE_FONT = "Comfortaa"
SUBTITLE_FONT_DIR = "fonts"
SUBTITLE_FONT_SIZE = 20
SUBTITLE_PRIMARY_COLOUR = "#eee0c9"
SUBTITLE_OUTLINE_COLOUR = "#0f1f24"
SUBTITLE_OUTLINE = 2
MARGIN_V = 80
MARGIN_L = 10
MARGIN_R = 10
# ==================== END CONFIGURATION ====================


def _execute_trim_and_audio(video, start_time, end_time, output_dir, step, start_step):
	"""Executa trim_video e enhance_audio. Retorna (caminho final, passo_atualizado)."""
	current_video = video

	# 1. Trim
	current_video, _ = trim_video(current_video, start_time, end_time, output_dir=output_dir, dry_run=(step < start_step))
	logger.info("✓ Trimmed")
	step += 1

	# 2. Audio enhance
	current_video, _ = enhance_audio(current_video, output_dir=output_dir, dry_run=(step < start_step))
	logger.info("✓ Audio enhanced")
	step += 1

	return current_video, step


def _execute_transcription(video, output_dir, step, start_step):
	"""Executa transcribe_to_json e json_to_srt. Retorna (json_file, srt_file, passo_atualizado)."""
	
	# 3. Transcribe
	json_file = transcribe_to_json(
		video,
		output_dir=output_dir,
		model_name=TRANSCRIPTION_MODEL,
		language=TRANSCRIPTION_LANGUAGE,
		dry_run=(step < start_step),
	)
	logger.info("✓ Transcribed to JSON")
	step += 1

	# 4. Convert to SRT
	srt_file = json_to_srt(json_file, output_dir=output_dir, max_char=MAX_CHARS_PER_LINE, dry_run=(step < start_step))
	logger.info("✓ Converted to SRT")
	step += 1
	
	return json_file, srt_file, step


def _execute_marks(video, output_dir, step, start_step):
	"""
	Executa adição de marcas como um passo único, para salvar tempo com encoding.
	Retorna (caminho final, passo_atualizado).
	"""
	current_video = video

	# 6. Add marks
	# dry_run=True (camandos para merge)
	_, cmd1 = add_mark(
		current_video,
		INSTA_MARK_PATH,
		output_dir=output_dir,
		margin_x=MARK_MARGIN_X,
		margin_y=MARK_MARGIN_Y,
		dry_run=True,
	)
	_, cmd2 = add_mark(
		current_video,
		IF_MARK_PATH,
		output_dir=output_dir,
		ref_x="end",
		ref_y="end",
		margin_x=MARK_MARGIN_X,
		margin_y=MARK_MARGIN_Y,
		dry_run=True,
	)
	output_path, merged_cmd = merge_mark([cmd1, cmd2], current_video, output_dir=output_dir)

	# Apenas executar se não passamos dessa etapa
	if step >= start_step:
		run_ffmpeg(merged_cmd)
	logger.info("✓ Marks added")

	current_video = output_path
	step += 1

	return current_video, step


def _execute_writes(video, text1, text2, base_output_dir, videos_dir, text_start_time, step, start_step):
	"""
	Executa add_text com todos os textos, dividindo o primeiro em duas linhas.
	Retorna (saída_final, passo_atualizado).
	"""
	current_video = video

	# Separa o texto 1
	text1_top, text1_bottom = split_text_by_char_limit(text1, char_limit=TEXT1_CHAR_LIMIT)

	# dry_run=True (camandos para merge)
	_, cmd1 = add_text(
		current_video,
		text1_top,
		x="(w-text_w)/2",
		y=str(TEXT1_Y_TOP),
		output_dir=videos_dir,
		font_size=TEXT1_FONT_SIZE,
		font_color=TEXT1_FONT_COLOR,
		font=TEXT1_FONT,
		font_dir=TEXT1_FONT_DIR,
		start_time=str(text_start_time),
		dry_run=True,
	)

	_, cmd2 = add_text(
		current_video,
		text1_bottom,
		x="(w-text_w)/2",
		y=str(TEXT1_Y_BOTTOM),
		output_dir=videos_dir,
		font_size=TEXT1_FONT_SIZE,
		font_color=TEXT1_FONT_COLOR,
		font=TEXT1_FONT,
		font_dir=TEXT1_FONT_DIR,
		start_time=str(text_start_time),
		dry_run=True,
	)

	_, cmd3 = add_text(
		current_video,
		text2,
		x="(w-text_w)/2",
		y=str(TEXT2_Y),
		output_dir=base_output_dir,
		font_size=TEXT2_FONT_SIZE,
		font_color=TEXT2_FONT_COLOR,
		font=TEXT2_FONT,
		font_dir=TEXT2_FONT_DIR,
		start_time=str(text_start_time),
		dry_run=True,
	)
	
	output_path, merged_cmd = merge_write([cmd1, cmd2, cmd3], current_video, output_dir=base_output_dir)

	# Apenas executar se não passamos dessa etapa
	if step >= start_step:
		run_ffmpeg(merged_cmd)
	logger.info("✓ All texts written")
	step += 1

	return output_path, step


def execute_pipeline(video, start_time, end_time, text1, text2, start_step=1):
	"""
	Executa pipeline completo de processamento de vídeo (9 passos lógicos).

	Args:
		video (str): Caminho do vídeo de entrada.
		start_time (str): Tempo inicial do trim (MM:SS ou HH:MM:SS).
		end_time (str): Tempo final do trim (MM:SS ou HH:MM:SS).
		text1 (str): Texto dividido em duas linhas por char_limit.
		text2 (str): Texto que aparece abaixo de text1.
		start_step (int): Passo inicial (1-9). Passos < start_step usam dry_run (padrão: 1).

	Returns:
		str: Caminho do vídeo final processado ou None se erro.

	Nota: Parâmetros de configuração definidos como constantes globais (topo do arquivo).

	Nota: Marks e Writes são tratados como passos únicos apesar de múltiplas operações internas
	(usa merge para uma única passagem de FFmpeg).

	Estrutura de output:
		- output_<INPUT>/videos/ → Vídeos intermediários
		- output_<INPUT>/transcriptions/ → JSON e SRT
		- output_<INPUT>/ → Saída final
	"""

	# Extrair nome do vídeo inicial (sem extensão)
	input_stem = Path(video).stem
	base_output_dir = f"output_{input_stem}"
	
	# Criar estrutura de diretórios
	videos_dir = f"{base_output_dir}/videos"
	transcriptions_dir = f"{base_output_dir}/transcriptions"

	Path(base_output_dir).mkdir(parents=True, exist_ok=True)
	Path(videos_dir).mkdir(parents=True, exist_ok=True)
	Path(transcriptions_dir).mkdir(parents=True, exist_ok=True)

	current_video = video
	step = 1

	try:
		# 1-2. Trim + Audio
		current_video, step = _execute_trim_and_audio(current_video, start_time, end_time, videos_dir, step, start_step)

		# Obter duração do vídeo para calcular start_time dos textos
		video_info = get_video_info(current_video)
		duration = video_info['duration']
		text_start_time = max(0, int(duration) - TEXT2_START_OFFSET)

		# 3-4. Transcribe + SRT
		json_file, srt_file, step = _execute_transcription(
			current_video,
			transcriptions_dir,
			step,
			start_step
		)

		# 5. Crop
		current_video, _ = analyze_video(current_video, output_dir=videos_dir, dry_run=(step < start_step))
		step += 1

		# 6. Adicionar marcas (Instagram + IF)
		current_video, step = _execute_marks(
			current_video,
			videos_dir,
			step,
			start_step
		)

		# 7. Burn subtitles
		current_video, _ = burn_subtitles_ffmpeg(
			current_video,
			srt_file,
			output_dir=videos_dir,
			font=SUBTITLE_FONT,
			font_dir=SUBTITLE_FONT_DIR,
			font_size=SUBTITLE_FONT_SIZE,
			primary_colour=SUBTITLE_PRIMARY_COLOUR,
			outline_colour=SUBTITLE_OUTLINE_COLOUR,
			outline=SUBTITLE_OUTLINE,
			margin_v = MARGIN_V,
			margin_l = MARGIN_L,
			margin_r = MARGIN_R,
			dry_run=(step < start_step),
		)
		step += 1

		# 8. Add outro
		current_video, _ = add_outro(current_video, OUTRO_PATH, output_dir=videos_dir, dry_run=(step < start_step), hex_color="#073b4c")
		step += 1

		# 9. Write all texts
		final_output, step = _execute_writes(
			current_video,
			text1,
			text2,
			base_output_dir,
			videos_dir,
			text_start_time,
			step,
			start_step
		)

		return final_output

	except Exception as e:
		import traceback
		logger.error(f"\nSomething went wrong at step {step}:\n{e}\n")
		traceback.print_exc()
		return None


# ==================== BATCH MODE ====================

def _parse_line(line):
	"""Analisa linha em formato: video|start_time|end_time|text1|text2."""
	partes = [p.strip() for p in line.split("|")]
	if len(partes) < 5:
		raise ValueError(f"Invalid format: {line}. Expected: video|start|end|text1|text2")
	return tuple(partes[:5])


def batch_process(input_arg, start_step=1, is_file=False):
	"""
	Processa vídeos em modo batch.
	
	Args:
		input_arg (str): Arquivo batch (.txt) ou linha única (video|start|end|text1|text2)
		start_step (int): Passo inicial (1-9, padrão: 1)
		is_file (bool): Se True, trata input como arquivo; se False, como linha única
	
	Exemplos:
		# Linha única
		batch_process("video.mp4|00:05|01:30|Texto um|Legenda")
		
		# Arquivo batch
		batch_process("batch.txt", is_file=True)
	"""
	
	if is_file:
		# Processar como arquivo batch
		logger.info(f"Processing batch file: {input_arg}")
		with open(input_arg, 'r', encoding='utf-8') as f:
			for linha in f:
				linha = linha.strip()
				if not linha or linha.startswith("#"):
					continue
				try:
					video, start, end, text1, text2 = _parse_line(linha)
					result = execute_pipeline(video, start, end, text1, text2, start_step=start_step)
					if result:
						logger.info(f"✓ Done: {result}")
				except ValueError as e:
					logger.warning(f"Skipping: {e}")
	else:
		# Processar como linha única
		try:
			video, start, end, text1, text2 = _parse_line(input_arg)
			result = execute_pipeline(video, start, end, text1, text2, start_step=start_step)
			if result:
				logger.info(f"✓ Done: {result}")
		except ValueError as e:
			logger.error(f"Invalid input: {e}")
			raise


if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser(description="Video processing pipeline")
	parser.add_argument("input", nargs="?", help="Linha única ou arquivo (com -f)")
	parser.add_argument("-f", "--from-file", action="store_true", help="Arquivo batch")
	parser.add_argument("-s", "--start-step", type=int, choices=range(1, 10), default=1, help="Passo inicial (1-9)")
	
	args = parser.parse_args()
	
	if not args.input:
		parser.error("input required")
	
	batch_process(args.input, start_step=args.start_step, is_file=args.from_file)
