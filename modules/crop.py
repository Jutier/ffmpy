import cv2
import numpy as np
import sys
import logging
from tqdm import tqdm
from pathlib import Path
from .utils import get_video_info, run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)



@log_function
def load_model(model_proto: str = "face_model/deploy.prototxt", model_weights: str = "face_model/res10_300x300_ssd_iter_140000.caffemodel") -> cv2.dnn_Net:
	"""
	Carrega o detector de faces baseado em SSD.

	Args:
		model_proto (str): Caminho para o arquivo .prototxt do modelo.
		model_weights (str): Caminho para o arquivo de pesos do modelo.

	Returns:
		cv2.dnn_Net: Rede neural do OpenCV carregada.
	"""
	logger.info("Loading face detection model...")
	return cv2.dnn.readNetFromCaffe(model_proto, model_weights)


def detect_faces(image: np.ndarray, net: cv2.dnn_Net, threshold: float = 0.7) -> list:
	"""
	Detecta rostos em uma imagem usando o modelo SSD.

	Args:
		image (np.ndarray): Frame do vídeo.
		net (cv2.dnn_Net): Rede neural do OpenCV já carregada.
		threshold (float): Confiança mínima para aceitar a detecção (padrão: 0.7).

	Returns:
		list: Faces no formato [(x, y, width, height, confidence), ...].
	"""
	h, w = image.shape[:2]

	# Prepara blob para o modelo SSD
	blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))
	net.setInput(blob)
	detections = net.forward()

	faces = []
	for i in range(detections.shape[2]):
		confidence = detections[0, 0, i, 2]

		if confidence < threshold:
			continue

		# Normaliza coordenadas
		box = detections[0, 0, i, 3:7] * [w, h, w, h]
		x1, y1, x2, y2 = box.astype("int")

		# Garante que as coordenadas estão dentro dos limites
		x = max(0, x1)
		y = max(0, y1)
		w_box = min(w - x, x2 - x1)
		h_box = min(h - y, y2 - y1)

		faces.append((x, y, w_box, h_box, confidence))

	return faces


@log_function
def collect_face_positions(video_path: str, net: cv2.dnn_Net, sample_rate: int = 30) -> list:
	"""
	Analisa um vídeo e coleta a posição horizontal dos rostos.

	Para cada frame:
	- Detecta rostos
	- Seleciona o maior rosto (apresentador)
	- Salva a posição do centro horizontal

	Args:
		video_path (str): Caminho do arquivo de vídeo.
		net (cv2.dnn_Net): Rede neural do OpenCV já carregada.
		sample_rate (int): Processa 1 frame a cada N frames (padrão: 30).

	Returns:
		list: Posições (x, y) do centro do maior rosto em cada frame.
	"""
	cap = cv2.VideoCapture(video_path)
	total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

	centers = []
	progress = tqdm(total=total_frames, desc="Analyzing faces", unit="frames", leave=True)

	for frame_index in range(0, total_frames, sample_rate):
		cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
		ret, frame = cap.read()
		
		if not ret:
			break

		faces = detect_faces(frame, net)

		if faces:
			largest = max(faces, key=lambda f: f[2] * f[3])
			x, y, w, h, _ = largest
			centers.append((x + w / 2, y + h / 2))

		progress.update(sample_rate)

	progress.close()
	cap.release()
	return centers


@log_function
def compute_crop_region(centers: list, frame_width: int, frame_height: int, aspect_ratio: float = 9/16) -> tuple:
	"""
	Calcula a maior região de corte que cabe no frame com o aspect ratio especificado.
	Centraliza nos eixos que foram limitados.

	Args:
		centers (list): Posições (x, y) do centro dos rostos.
		frame_width (int): Largura total do frame em pixels.
		frame_height (int): Altura total do frame em pixels.
		aspect_ratio (float): Proporção largura/altura (padrão: 9/16 para vertical).

	Returns:
		tuple: (x_inicial, y_inicial, largura_corte, altura_corte).
	"""
	# Calcula o maior tamanho que cabe no frame mantendo o aspect ratio
	crop_width = int(min(frame_width, frame_height * aspect_ratio))
	crop_height = int(min(frame_height, frame_width / aspect_ratio))
	
	# Centraliza nos eixos, dependendo de qual foi limitado
	center_x = int(np.median([c[0] for c in centers]))
	center_y = int(np.median([c[1] for c in centers]))
	
	left = center_x - crop_width // 2
	top = center_y - crop_height // 2

	# Garante que o corte fica dentro dos limites
	left = max(0, min(frame_width - crop_width, left))
	top = max(0, min(frame_height - crop_height, top))
	
	return left, top, crop_width, crop_height


@log_function
def crop_video_ffmpeg(
	input_video: str,
	output_video: str,
	crop_x: int,
	crop_y: int,
	crop_width: int,
	crop_height: int,
	scale: str = "1080x1920",
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Aplica o corte no vídeo usando FFmpeg.

	Args:
		input_video (str): Caminho do arquivo de vídeo de entrada.
		output_video (str): Caminho do arquivo de vídeo de saída.
		crop_x (int): Coordenada X inicial do corte em pixels.
		crop_y (int): Coordenada Y inicial do corte em pixels.
		crop_width (int): Largura do corte em pixels.
		crop_height (int): Altura do corte em pixels.
		scale (str): Resolução de saída no formato "widthxheight" (padrão: "1080x1920").
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False).
	
	Returns:
		tuple[str, list]: (output_video, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""
	input_ffmpeg = Path(input_video).as_posix()
	output_ffmpeg = Path(output_video).as_posix()

	# Monta filtro de vídeo
	vf_chain = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}"
	
	if scale:
		vf_chain += f",scale={scale}"

	# Exemplo: ffmpeg -y -i input.mp4 -vf "crop=960:1920:270:0,scale=1080x1920" -c:a copy output_cropped.mp4
	cmd = [
		"ffmpeg",
		"-y",
		"-i", input_ffmpeg,
		"-vf", vf_chain,
		"-c:a", "copy",
		output_ffmpeg,
	]

	logger.info(f"Cropping video...")
	
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)
	return output_video, cmd_result


@log_function
def analyze_video(
	video_path: str,
	output_dir: str = "crop_output",
	sample_rate: int = 30,
	aspect_ratio: float = 9/16,
	scale: str = "1080x1920",
	dry_run: bool = False,
) -> tuple[str, list]:
	"""Detecta apresentador e aplica corte automático ao vídeo.
	
	Args:
		video_path (str): Arquivo de vídeo.
		output_dir (str): Diretório de saída (padrão: "crop_output").
		sample_rate (int): Processa 1 frame a cada N (padrão: 30).
		aspect_ratio (float): Proporção corte (padrão: 9/16 vertical).
		scale (str): Resolução de saída no formato "widthxheight" (padrão: "1080x1920").
		dry_run (bool): Se True, retorna comando sem executar (padrão: False).
	
	Returns:
		tuple[str, list]: (output_video, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""

	# Carrega modelo

	# Define caminho de saída
	Path(output_dir).mkdir(parents=True, exist_ok=True)
	output_video = str(Path(output_dir) / f"{Path(video_path).stem}_crop{Path(video_path).suffix}")

	if dry_run:
		crop_x, crop_y, crop_width, crop_height = 0, 0, 0, 0 # Espero que não quebre nada...
		output_video, cmd_result = crop_video_ffmpeg(video_path, output_video, crop_x, crop_y, crop_width, crop_height, scale=scale, dry_run=dry_run)
		return output_video, cmd_result

	net = load_model()
	centers = collect_face_positions(video_path, net, sample_rate)

	if not centers:
		raise RuntimeError(f"No faces detected in video: {video_path}")

	video_info = get_video_info(video_path)
	width, height = video_info['width'], video_info['height']
	crop_x, crop_y, crop_width, crop_height = compute_crop_region(centers, width, height, aspect_ratio)



	output_video, cmd_result = crop_video_ffmpeg(video_path, output_video, crop_x, crop_y, crop_width, crop_height, scale=scale, dry_run=dry_run)
	
	return output_video, cmd_result
