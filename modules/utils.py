import cv2
import subprocess
import time
import logging
from .logs import setup_logger, log_function

setup_logger()
logger = logging.getLogger(__name__)


def split_text_by_char_limit(text, char_limit=22):
	"""
	Divide texto nos espaços, acumulando palavras até atingir o limite de caracteres.
	Primeira linha fica com até char_limit caracteres, resto vai na segunda linha.
	"""
	words = text.split()
	first_line = []
	
	for i, word in enumerate(words):
		# Testar se adicionar a próxima palavra ultrapassa o limite
		test_line = " ".join(first_line + [word])
		if len(test_line) <= char_limit:
			first_line.append(word)
		else:
			# Encontrou o ponto de quebra
			second_line = " ".join(words[i:])
			return " ".join(first_line), second_line
	
	# Se todas as palavras cabem na primeira linha
	return " ".join(first_line), ""


@log_function
def get_video_info(video_path: str) -> dict:
	"""
	Extrai informações detalhadas de um vídeo.

	Args:
		video_path (str): Caminho para o arquivo de vídeo.

	Returns:
		dict: Dicionário com todas as informações do vídeo.
		      Chaves: width, height, fps, duration, frame_count, fourcc, codec_name

	Raises:
		RuntimeError: Se o vídeo não puder ser aberto.
	"""
	cap = cv2.VideoCapture(video_path)

	if not cap.isOpened():
		raise RuntimeError(f"Cannot open video: {video_path}")

	try:
		# Extrai todas as informações possíveis
		width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
		fps = cap.get(cv2.CAP_PROP_FPS)
		frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))

		# Converte FOURCC para string
		codec_name = ""
		if fourcc != 0:
			codec_name = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

		# Calcula duração
		duration = frame_count / fps if fps > 0 else 0

		# Retorna todas as informações
		return {
			'width': width,
			'height': height,
			'fps': fps,
			'duration': duration,
			'frame_count': frame_count,
			'fourcc': fourcc,
			'codec_name': codec_name,
		}

	finally:
		cap.release()


@log_function
def hex_to_rgb(hex_color: str) -> tuple:
	"""
	Converte HEX (#RRGGBB) para RGB tuple.

	Args:
		hex_color (str): Cor em formato HEX (#RRGGBB).

	Returns:
		tuple: (R, G, B) valores de 0-255.
	"""
	hex_color = hex_color.strip().lstrip("#")

	if len(hex_color) != 6:
		raise ValueError("HEX must follow RRGGBB format.")

	r = int(hex_color[0:2], 16)
	g = int(hex_color[2:4], 16)
	b = int(hex_color[4:6], 16)

	return (r, g, b)


@log_function
def hex_to_ass(hex_color: str) -> str:
	"""
	Converte HEX (#RRGGBB ou #RRGGBBAA) para formato ASS (&HAABBGGRR&).

	Aceita:
		RRGGBB
		#RRGGBB
		RRGGBBAA
		#RRGGBBAA

	Alpha no HEX segue padrão RGBA (FF=opaco).
	Alpha no ASS é invertido (00=opaco).
	"""

	hex_color = hex_color.strip().lstrip("#")

	if len(hex_color) not in (6, 8):
		raise ValueError("HEX must follow RRGGBB or RRGGBBAA format.")

	# Extrai RGB usando hex_to_rgb
	r, g, b = hex_to_rgb(f"#{hex_color[:6]}")

	# Processa alpha se fornecido
	if len(hex_color) == 8:
		rgba_alpha = int(hex_color[6:8], 16)
	else:
		rgba_alpha = 255  # opaco

	ass_alpha = 255 - rgba_alpha

	return f"&H{ass_alpha:02X}{b:02X}{g:02X}{r:02X}&"


@log_function
def run_ffmpeg(cmd: list, timeout: int = None, dry_run: bool = False) -> list:
	"""
	Executa comando FFmpeg com logging automático.

	Args:
		cmd (list): Comando FFmpeg como lista
		timeout (int): Timeout em segundos
		dry_run (bool): Apenas mostra comando sem executar

	Returns:
		list: Comando executado
	"""

	cmd_str = " ".join(cmd)

	if dry_run:
		logger.info(f"Dry-run. No output created.")
		logger.info(f"❕ Some directories may have been created.")
		logger.info(f"Cmd:\n$ {cmd_str}")
		return cmd

	logger.info("Running FFmpeg...")
	logger.debug(f"FFmpeg Command: {cmd_str}")
	
	start_time = time.time()
	try:
		# Captura output
		result = subprocess.run(
			cmd,
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			timeout=timeout,
			text=True
		)
		
		elapsed = time.time() - start_time
		
		# Loga stderr (que é onde FFmpeg manda progresso)
		if result.stderr:
			logger.debug(f"FFmpeg Output:\n{result.stderr}")
		
		logger.info(f"✓ FFmpeg finished successfully! ({elapsed:.2f}s)")
		
	except subprocess.TimeoutExpired:
		error_msg = f"FFmpeg timeout ({timeout}s)"
		logger.error(error_msg)
		raise RuntimeError(error_msg)
	except subprocess.CalledProcessError as e:
		error_msg = f"FFmpeg error: {e}"
		logger.error(f"{error_msg}\nStderr: {e.stderr}")
		raise RuntimeError(error_msg)
	except FileNotFoundError:
		error_msg = "FFmpeg not found in PATH"
		logger.error(error_msg)
		raise RuntimeError(error_msg)
	
	return cmd
